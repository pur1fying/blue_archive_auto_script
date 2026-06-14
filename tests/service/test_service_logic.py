from __future__ import annotations

import asyncio
from pathlib import Path

from watchfiles import Change

from service.utils.broadcast import BroadcastChannel
from service.conf.manager import ConfigManager
from service.utils.diff import apply_patch, diff_documents


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
