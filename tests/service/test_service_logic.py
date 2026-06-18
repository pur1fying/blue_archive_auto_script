from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from pathlib import Path

from watchfiles import Change

from service.utils.broadcast import BroadcastChannel
from service.conf.manager import ConfigManager
from service.utils.diff import apply_patch, diff_documents
from service import runtime as runtime_module
from service.runtime import ServiceRuntime


def test_apply_patch_and_diff_documents():
    original = {"a": 1, "nested": {"keep": True}, "items": [1, 2]}
    updated = apply_patch(
        original,
        [
            {"op": "replace", "path": "/a", "value": 2},
            {"op": "add", "path": "/nested/new", "value": "x"},
            {"op": "remove", "path": "/items/0"},
        ],
    )

    assert updated == {"a": 2, "nested": {"keep": True, "new": "x"}, "items": [2]}
    assert {"op": "replace", "path": "/a", "value": 3} in diff_documents(updated, {**updated, "a": 3})


def test_broadcast_channel_drops_oldest_when_subscriber_is_full():
    async def scenario():
        channel = BroadcastChannel(max_queue_size=1)
        queue = channel.subscribe()
        await channel.publish({"seq": 1})
        await channel.publish({"seq": 2})
        return await queue.get()

    assert asyncio.run(scenario()) == {"seq": 2}


def test_config_manager_classifies_config_files():
    root = Path("project")
    manager = ConfigManager(root)
    config_path = root / "config" / "default_config" / "config.json"
    event_path = root / "config" / "default_config" / "event.json"
    gui_path = root / "config" / "gui.json"
    static_path = root / "config" / "static.json"

    assert manager._classify_config_change(Change.modified, config_path) == (False, ("config", "default_config"))
    assert manager._classify_config_change(Change.modified, event_path) == (False, ("event", "default_config"))
    assert manager._classify_config_change(Change.modified, gui_path) == (False, ("gui", None))
    assert manager._classify_config_change(Change.modified, static_path) == (False, ("static", None))
    assert manager._classify_config_change(Change.added, root / "config" / "new_config") == (True, None)


def _write_config_pair(root: Path, config_id: str, name: str) -> Path:
    config_dir = root / "config" / config_id
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps({"name": name, "server": "官服"}, ensure_ascii=False), encoding="utf-8")
    (config_dir / "event.json").write_text("[]", encoding="utf-8")
    return config_path


def test_config_manager_initial_scan_publishes_config_add(tmp_path):
    async def scenario():
        _write_config_pair(tmp_path, "default_config", "Default")
        manager = ConfigManager(tmp_path)
        manager.set_loop(asyncio.get_running_loop())
        queue = await manager.subscribe_updates()

        await manager.scan_once()

        return await queue.get()

    payload = asyncio.run(scenario())

    assert payload["type"] == "patch"
    assert payload["resource"] == "config"
    assert payload["resource_id"] == "default_config"
    assert payload["ops"][0]["op"] == "add"


def test_config_manager_scan_publishes_config_remove(tmp_path):
    async def scenario():
        _write_config_pair(tmp_path, "default_config", "Default")
        manager = ConfigManager(tmp_path)
        manager.set_loop(asyncio.get_running_loop())
        queue = await manager.subscribe_updates()

        await manager.scan_once()
        await queue.get()
        shutil.rmtree(tmp_path / "config" / "default_config")
        await manager.scan_once()

        return await queue.get()

    payload = asyncio.run(scenario())

    assert payload["type"] == "patch"
    assert payload["resource"] == "config"
    assert payload["resource_id"] == "default_config"
    assert payload["ops"][0]["op"] == "remove"


def test_config_manager_detects_manual_config_json_change(tmp_path):
    async def scenario():
        config_path = _write_config_pair(tmp_path, "default_config", "Before")
        manager = ConfigManager(tmp_path)
        manager.set_loop(asyncio.get_running_loop())
        queue = await manager.subscribe_updates()

        await manager.scan_once()
        await queue.get()
        await manager.get_snapshot("config", "default_config")

        config_path.write_text(
            json.dumps({"name": "After", "server": "官服"}, ensure_ascii=False),
            encoding="utf-8",
        )
        future = time.time() + 2
        os.utime(config_path, (future, future))

        await manager._check_resource("config", "default_config")
        return await queue.get()

    payload = asyncio.run(scenario())

    assert payload["type"] == "patch"
    assert payload["resource"] == "config"
    assert payload["resource_id"] == "default_config"
    assert {"op": "replace", "path": "/name", "value": "After"} in payload["ops"]


def test_service_runtime_streams_sha_results_by_completion(monkeypatch, tmp_path):
    def fake_configs(channel):
        return [
            {"name": "slow", "method": "SLOW", "channel": channel},
            {"name": "fast", "method": "FAST", "channel": channel},
        ]

    def fake_test_repo_sha(config, timeout):
        time.sleep(0.05 if config["name"] == "slow" else 0.01)
        return {
            "name": config["name"],
            "method": config["method"],
            "duration": timeout,
            "success": True,
            "value": config["name"],
            "error": None,
        }

    async def scenario():
        runtime = ServiceRuntime(tmp_path)
        results = []
        async for result in runtime.test_all_sha_stream("stable"):
            results.append(result["name"])
        return results

    monkeypatch.setattr(runtime_module, "repo_sha_test_configs", fake_configs)
    monkeypatch.setattr(runtime_module, "test_repo_sha", fake_test_repo_sha)

    assert asyncio.run(scenario()) == ["fast", "slow"]
