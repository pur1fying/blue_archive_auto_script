from __future__ import annotations

import asyncio
import queue
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .broadcast import BroadcastChannel

LEVEL_MAP = {
    1: "INFO",
    2: "WARNING",
    3: "ERROR",
    4: "CRITICAL",
}


class LogManager:
    """Consumes logger queues and republishes entries tagged by scope."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop
        self._broadcast = BroadcastChannel(loop)
        self._history_lock = threading.Lock()
        self._history_all: List[Dict[str, Any]] = []
        self._history_per_scope: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._stop_event = threading.Event()
        self._workers: List[threading.Thread] = []
        self._sources: Dict[queue.Queue, str] = {}

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._broadcast.set_loop(loop)

    def register_queue(self, log_queue: queue.Queue, scope: str = "global") -> None:
        if log_queue in self._sources:
            return
        self._sources[log_queue] = scope
        if self._workers:
            worker = threading.Thread(
                target=self._pump,
                args=(log_queue, scope),
                name=f"log-pump-{len(self._workers)}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

    def unregister_queue(self, log_queue: queue.Queue) -> None:
        # Queues are long lived; we keep workers alive for simplicity.
        # This method exists for API completeness so callers can drop references.
        self._sources.pop(log_queue, None)

    def start(self) -> None:
        if self._workers:
            return
        self._stop_event.clear()
        for idx, (src, scope) in enumerate(self._sources.items()):
            worker = threading.Thread(
                target=self._pump,
                args=(src, scope),
                name=f"log-pump-{idx}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

    def stop(self) -> None:
        self._stop_event.set()
        for worker in self._workers:
            worker.join(timeout=1.0)
        self._workers.clear()

    def _pump(self, source: queue.Queue, scope: str) -> None:
        while not self._stop_event.is_set():
            try:
                record = source.get(timeout=0.5)
            except queue.Empty:
                continue
            entry = self._normalize_record(record, scope)
            with self._history_lock:
                self._history_all.append(entry)
                self._history_per_scope[scope].append(entry)
            if self._loop:
                self._broadcast.publish_threadsafe(entry)

    def _normalize_record(self, record: Dict[str, Any], scope: str) -> Dict[str, Any]:
        timestamp = record.get("time")
        if isinstance(timestamp, datetime):
            iso = timestamp.astimezone(timezone.utc).isoformat()
        else:
            iso = datetime.now(timezone.utc).isoformat()
        level = LEVEL_MAP.get(record.get("level", 1), "INFO")
        message = record.get("message", "")
        return {"scope": scope, "time": iso, "level": level, "message": message}

    def get_history(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._history_lock:
            if scope is None:
                return list(self._history_all)
            return list(self._history_per_scope.get(scope, []))

    def get_scopes(self) -> List[str]:
        with self._history_lock:
            scopes = set(self._history_per_scope.keys())
        scopes.update(self._sources.values())
        return sorted(scopes)

    async def subscribe(self) -> asyncio.Queue:
        if self._loop is None:
            raise RuntimeError("LogManager loop is not configured")
        return self._broadcast.subscribe()

    def unsubscribe(self, queue_obj: asyncio.Queue) -> None:
        self._broadcast.unsubscribe(queue_obj)
