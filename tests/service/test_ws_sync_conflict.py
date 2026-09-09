from __future__ import annotations

import asyncio
from types import SimpleNamespace

from service.api import ws_sync
from service.types import SyncPatchMessage
from service.utils.diff import PatchConflictError


class _ConfigManager:
    def __init__(self) -> None:
        self.conflict = True
        self.applied_timestamps: list[float] = []

    async def apply_patch(self, resource, resource_id, ops, timestamp, origin):
        self.applied_timestamps.append(timestamp)
        if self.conflict:
            raise PatchConflictError("Incoming patch is older than current snapshot")

    async def get_snapshot(self, resource, resource_id):
        return SimpleNamespace(timestamp=200.0, data={"channel": "stable"})


def test_stale_sync_patch_returns_snapshot_and_can_retry(monkeypatch):
    manager = _ConfigManager()
    monkeypatch.setattr(ws_sync, "context", SimpleNamespace(config_manager=manager))
    patch = SyncPatchMessage(
        type="patch",
        resource="setup_toml",
        resource_id="global",
        timestamp=100.0,
        ops=[{"op": "replace", "path": "/channel", "value": "dev"}],
    )

    conflict = asyncio.run(ws_sync.apply_sync_patch(patch))

    assert conflict == {
        "type": "patch_conflict",
        "resource": "setup_toml",
        "resource_id": "global",
        "request_timestamp": 100.0,
        "timestamp": 200.0,
        "data": {"channel": "stable"},
        "error": "Incoming patch is older than current snapshot",
    }

    manager.conflict = False
    retry = SyncPatchMessage(
        type="patch",
        resource=patch.resource,
        resource_id=patch.resource_id,
        timestamp=conflict["timestamp"],
        ops=patch.ops,
    )
    acknowledged = asyncio.run(ws_sync.apply_sync_patch(retry))

    assert acknowledged["type"] == "patch_ack"
    assert acknowledged["timestamp"] == 200.0
    assert manager.applied_timestamps == [100.0, 200.0]
