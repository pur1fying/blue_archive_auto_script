from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from .broadcast import BroadcastChannel
from .diff import PatchConflictError, apply_patch, diff_documents
from .messages import PatchOperation, SyncPushPayload

ResourceKey = Tuple[str, Optional[str]]


@dataclass
class ResourceSnapshot:
    data: Any
    timestamp: float


class ConfigManager:
    """Manages persisted configuration resources with diff support."""

    def __init__(self, project_root: Path, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._root = project_root
        self._config_root = self._root / "config"
        self._lock = asyncio.Lock()
        self._snapshots: Dict[ResourceKey, ResourceSnapshot] = {}
        self._mtimes: Dict[ResourceKey, float] = {}
        self._update_bus = BroadcastChannel(loop)
        self._loop = loop
        self._gui_full: Union[Dict[str, Any], None] = None
        self._poll_interval = 1.0

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._update_bus.set_loop(loop)

    # ------------------------------------------------------------------
    # basic filesystem helpers
    # ------------------------------------------------------------------
    def _file_path(self, resource: str, resource_id: Optional[str]) -> Path:
        if resource in ("config", "event"):
            if not resource_id:
                raise ValueError(f"resource_id required for resource '{resource}'")
            return self._config_root / resource_id / f"{resource}.json"
        if resource == "gui":
            return self._config_root / "gui.json"
        if resource == "static":
            return self._config_root / "static.json"
        raise ValueError(f"Unsupported resource '{resource}'")

    def list_config_ids(self) -> List[str]:
        ids: List[str] = []
        if not self._config_root.exists():
            return ids
        for child in self._config_root.iterdir():
            if not child.is_dir():
                continue
            config_file = child / "config.json"
            event_file = child / "event.json"
            if config_file.exists() and event_file.exists():
                ids.append(child.name)
        return sorted(ids)

    async def get_config_list(self) -> ResourceSnapshot:
        async with self._lock:
            ids = self.list_config_ids()
            return ResourceSnapshot(json.loads(json.dumps(ids)), time.time())

    # ------------------------------------------------------------------
    # snapshot helpers
    # ------------------------------------------------------------------
    def _project_gui(self, full_gui: Dict[str, Any]) -> Dict[str, Any]:
        main_window = full_gui.get("MainWindow", {})
        fluent = full_gui.get("QFluentWidgets", {})
        return {
            "MainWindow": {
                "Language": main_window.get("Language"),
                "DpiScale": main_window.get("DpiScale"),
            },
            "QFluentWidgets": {
                "ThemeMode": fluent.get("ThemeMode"),
            },
        }

    def _merge_gui(self, projection: Dict[str, Any]) -> Dict[str, Any]:
        if self._gui_full is None:
            self._gui_full = {}
        merged = json.loads(json.dumps(self._gui_full))  # deep copy via json
        merged.setdefault("MainWindow", {})
        merged.setdefault("QFluentWidgets", {})
        main_window = projection.get("MainWindow", {})
        if "Language" in main_window:
            merged["MainWindow"]["Language"] = main_window.get("Language")
        if "DpiScale" in main_window:
            merged["MainWindow"]["DpiScale"] = main_window.get("DpiScale")
        fluent = projection.get("QFluentWidgets", {})
        if "ThemeMode" in fluent:
            merged["QFluentWidgets"]["ThemeMode"] = fluent.get("ThemeMode")
        self._gui_full = merged
        return merged

    def _load_from_disk(self, resource: str, resource_id: Optional[str]) -> ResourceSnapshot:
        path = self._file_path(resource, resource_id)
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if resource == "gui":
            self._gui_full = data
            projection = self._project_gui(data)
            data_to_store = projection
        else:
            data_to_store = data
        timestamp = path.stat().st_mtime
        snapshot = ResourceSnapshot(data=data_to_store, timestamp=timestamp)
        self._snapshots[(resource, resource_id)] = snapshot
        self._mtimes[(resource, resource_id)] = timestamp
        return snapshot

    async def get_snapshot(self, resource: str, resource_id: Optional[str]) -> ResourceSnapshot:
        key = (resource, resource_id)
        async with self._lock:
            snapshot = self._snapshots.get(key)
            if snapshot is None:
                snapshot = self._load_from_disk(resource, resource_id)
            return ResourceSnapshot(json.loads(json.dumps(snapshot.data)), snapshot.timestamp)

    async def get_static_snapshot(self) -> ResourceSnapshot:
        snapshot = await self.get_snapshot("static", None)
        return snapshot

    # ------------------------------------------------------------------
    # update operations
    # ------------------------------------------------------------------
    async def apply_patch(
        self,
        resource: str,
        resource_id: Optional[str],
        operations: Iterable[PatchOperation | dict[str, Any]],
        timestamp: float,
        origin: str = "backend",
    ) -> ResourceSnapshot:
        key = (resource, resource_id)
        async with self._lock:
            snapshot = self._snapshots.get(key)
            if snapshot is None:
                snapshot = self._load_from_disk(resource, resource_id)
            elif timestamp < snapshot.timestamp:
                raise PatchConflictError("Incoming patch is older than current snapshot")

            current_data = json.loads(json.dumps(snapshot.data))
            ops_payload = [op.model_dump() if isinstance(op, PatchOperation) else dict(op) for op in operations]
            updated = apply_patch(current_data, ops_payload)

            if resource == "gui":
                if not isinstance(updated, dict):
                    raise PatchConflictError("GUI patch must result in a mapping document")
                full_gui = self._merge_gui(updated)
            else:
                full_gui = updated

            path = self._file_path(resource, resource_id)
            if resource == "gui":
                to_dump = full_gui
            else:
                to_dump = updated
            self._write_json(path, to_dump, resource)

            new_timestamp = max(timestamp, time.time(), path.stat().st_mtime)
            new_snapshot = ResourceSnapshot(data=updated, timestamp=new_timestamp)
            self._snapshots[key] = new_snapshot
            self._mtimes[key] = new_timestamp

        payload = SyncPushPayload(
            resource=resource, resource_id=resource_id, timestamp=new_snapshot.timestamp, ops=[
                PatchOperation(**op) for op in ops_payload
            ], origin=origin,
        )
        await self._update_bus.publish(payload.model_dump())
        return ResourceSnapshot(json.loads(json.dumps(new_snapshot.data)), new_snapshot.timestamp)

    def _write_json(self, path: Path, data: Any, resource: str) -> None:
        indent = 4 if resource in ("config", "gui") else 2
        with path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=indent, ensure_ascii=False)

    async def subscribe_updates(self) -> asyncio.Queue:
        if self._loop is None:
            raise RuntimeError("ConfigManager event loop not configured")
        return self._update_bus.subscribe()

    def unsubscribe_updates(self, queue: asyncio.Queue) -> None:
        self._update_bus.unsubscribe(queue)

    # ------------------------------------------------------------------
    # disk scanning
    # ------------------------------------------------------------------
    async def scan_once(self) -> None:
        for config_id in self.list_config_ids():
            await self._check_resource("config", config_id)
            await self._check_resource("event", config_id)
        await self._check_resource("gui", None)

    async def _check_resource(self, resource: str, resource_id: Optional[str]) -> None:
        key = (resource, resource_id)
        path = self._file_path(resource, resource_id)
        if not path.exists():
            return
        mtime = path.stat().st_mtime
        previous = self._mtimes.get(key)
        if previous is None:
            self._mtimes[key] = mtime
            return
        if mtime <= previous:
            return
        async with self._lock:
            old_snapshot = self._snapshots.get(key)
            fresh_snapshot = self._load_from_disk(resource, resource_id)
        if old_snapshot is None:
            ops = [{"op": "replace", "path": "", "value": fresh_snapshot.data}]
        else:
            ops = diff_documents(old_snapshot.data, fresh_snapshot.data)
        if not ops:
            return
        payload = SyncPushPayload(
            resource=resource,
            resource_id=resource_id,
            timestamp=fresh_snapshot.timestamp,
            ops=[PatchOperation(**op) for op in ops],
            origin="filesystem",
        )
        await self._update_bus.publish(payload.dict())

    async def watch_filesystem(self) -> None:
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
            self._update_bus.set_loop(self._loop)
        while True:
            await self.scan_once()
            await asyncio.sleep(self._poll_interval)


