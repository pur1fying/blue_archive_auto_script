from __future__ import annotations

import asyncio
import queue
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

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
        self._sources: Dict[queue.Queue, str] = {}
        self._queue_tasks: Dict[queue.Queue, asyncio.Task] = {}
        self._sentinels: Dict[queue.Queue, object] = {}
        self._active_tasks: Set[asyncio.Task] = set()
        self._running = False

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._broadcast.set_loop(loop)

    def register_queue(self, log_queue: queue.Queue, scope: str = "global") -> None:
        if log_queue in self._sources:
            return
        self._sources[log_queue] = scope
        sentinel = object()
        self._sentinels[log_queue] = sentinel
        if self._running and self._loop is not None:
            task = self._loop.create_task(self._pump_async(log_queue, scope, sentinel), name=f"log-pump-{scope}")
            self._queue_tasks[log_queue] = task
            self._active_tasks.add(task)
            task.add_done_callback(self._make_cleanup(log_queue))

    def unregister_queue(self, log_queue: queue.Queue) -> None:
        scope = self._sources.pop(log_queue, None)
        if scope is None:
            return
        task = self._queue_tasks.pop(log_queue, None)
        sentinel = self._sentinels.pop(log_queue, None)
        if task is not None and sentinel is not None:
            try:
                log_queue.put_nowait(sentinel)
            except queue.Full:
                # Queues provided by the logger are unbounded; ignore if full.
                pass

    async def start(self) -> None:
        if self._running:
            return
        if self._loop is None:
            raise RuntimeError("LogManager loop is not configured")
        self._running = True
        for idx, (src, scope) in enumerate(self._sources.items()):
            sentinel = self._sentinels.setdefault(src, object())
            task = self._loop.create_task(
                self._pump_async(src, scope, sentinel),
                name=f"log-pump-{idx}",
            )
            self._queue_tasks[src] = task
            self._active_tasks.add(task)
            task.add_done_callback(self._make_cleanup(src))

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        tasks = list(self._active_tasks)
        for queue_obj, sentinel in list(self._sentinels.items()):
            try:
                queue_obj.put_nowait(sentinel)
            except queue.Full:
                # Queues provided by the logger are unbounded; ignore if full.
                pass
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._queue_tasks.clear()
        self._active_tasks.clear()
        self._sentinels.clear()

    def _make_cleanup(self, queue_obj: queue.Queue):
        def _cleanup(task: asyncio.Task) -> None:
            self._active_tasks.discard(task)
            self._queue_tasks.pop(queue_obj, None)
            self._sentinels.pop(queue_obj, None)

        return _cleanup

    async def _pump_async(self, source: queue.Queue, scope: str, sentinel: object) -> None:
        while True:
            record = await asyncio.to_thread(source.get)
            if record is sentinel:
                break
            entry = self._normalize_record(record, scope)
            with self._history_lock:
                self._history_all.append(entry)
                self._history_per_scope[scope].append(entry)
            await self._broadcast.publish(entry)

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
