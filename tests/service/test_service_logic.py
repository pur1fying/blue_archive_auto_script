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


def test_config_manager_ignores_runtime_log_directory(caplog, tmp_path):
    async def scenario():
        manager = ConfigManager(tmp_path)
        manager.set_loop(asyncio.get_running_loop())
        log_path = tmp_path / "config" / "logs" / "baas-service.jsonl"
        await manager._handle_watch_batch([(Change.modified, str(log_path))])

    caplog.set_level("INFO")
    asyncio.run(scenario())

    assert not any("baas-service.jsonl" in record.message for record in caplog.records)


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


def test_android_config_snapshot_locks_local_device_methods(monkeypatch, tmp_path):
    monkeypatch.setenv("BAAS_ANDROID", "1")
    _write_config_pair(tmp_path, "default_config", "Default")
    config_path = tmp_path / "config" / "default_config" / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "name": "Default",
                "server": "官服",
                "control_method": "adb",
                "screenshot_method": "scrcpy",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    manager = ConfigManager(tmp_path)
    snapshot = asyncio.run(manager.get_snapshot("config", "default_config"))

    assert snapshot.data["control_method"] == "android_local"
    assert snapshot.data["screenshot_method"] == "android_local"


def test_android_config_patch_cannot_change_local_device_methods(monkeypatch, tmp_path):
    monkeypatch.setenv("BAAS_ANDROID", "1")
    _write_config_pair(tmp_path, "default_config", "Default")
    manager = ConfigManager(tmp_path)
    snapshot = asyncio.run(manager.get_snapshot("config", "default_config"))

    updated = asyncio.run(
        manager.apply_patch(
            "config",
            "default_config",
            [
                {"op": "add", "path": "/control_method", "value": "adb"},
                {"op": "add", "path": "/screenshot_method", "value": "scrcpy"},
            ],
            snapshot.timestamp,
            origin="frontend",
        )
    )

    assert updated.data["control_method"] == "android_local"
    assert updated.data["screenshot_method"] == "android_local"


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
        async for result in runtime.test_all_sha_stream("stable", timeout=12):
            results.append((result["name"], result["duration"]))
        return results

    monkeypatch.setattr(runtime_module, "repo_sha_test_configs", fake_configs)
    monkeypatch.setattr(runtime_module, "test_repo_sha", fake_test_repo_sha)

    assert asyncio.run(scenario()) == [("fast", 10.0), ("slow", 10.0)]


def test_android_update_to_latest_schedules_backend_restart(monkeypatch, tmp_path):
    scheduled = []

    def fake_update(_setup_path):
        return {"status": "updated", "restart_required": True, "current": "abc"}

    async def fake_stop_all_tasks(self):
        return {"status": "stopped"}

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setattr(runtime_module, "update_to_latest", fake_update)
    monkeypatch.setattr(ServiceRuntime, "stop_all_tasks", fake_stop_all_tasks)
    monkeypatch.setattr(
        ServiceRuntime,
        "_schedule_android_backend_restart",
        lambda self, delay: scheduled.append(delay) or True,
    )

    runtime = ServiceRuntime(tmp_path)
    result = asyncio.run(runtime.update_to_latest())

    assert result["backend_restart_scheduled"] is True
    assert result["backend_restart_delay_seconds"] == 2.0
    assert scheduled == [2.0]


def test_android_update_stream_schedules_backend_restart(monkeypatch, tmp_path):
    scheduled = []

    def fake_update_stream(_setup_path, progress=None):
        if progress:
            progress("done", {"sha": "abc"})
        return {"status": "updated", "restart_required": True, "current": "abc"}

    async def fake_stop_all_tasks(self):
        return {"status": "stopped"}

    async def scenario():
        runtime = ServiceRuntime(tmp_path)
        events = []
        async for event in runtime.update_to_latest_stream():
            events.append(event)
        return events

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setattr(runtime_module, "update_to_latest_with_progress", fake_update_stream)
    monkeypatch.setattr(ServiceRuntime, "stop_all_tasks", fake_stop_all_tasks)
    monkeypatch.setattr(
        ServiceRuntime,
        "_schedule_android_backend_restart",
        lambda self, delay: scheduled.append(delay) or True,
    )

    events = asyncio.run(scenario())

    assert events[0]["type"] == "progress"
    assert events[1]["type"] == "result"
    assert events[1]["result"]["backend_restart_scheduled"] is True
    assert scheduled == [2.0]
