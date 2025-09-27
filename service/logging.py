from __future__ import annotations

import asyncio
import queue
import threading
from datetime import datetime
from typing import Any, Dict, Iterable, List

from .broadcast import BroadcastChannel

LEVEL_MAP = {
    1: "INFO",
    2: "WARNING",
    3: "ERROR",
    4: "CRITICAL",
}


class LogManager:
    """Consumes one or more logger queues and republishes via asyncio."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop
        self._history: List[Dict[str, Any]] = []
        self._broadcast = BroadcastChannel(loop)
        self._stop_event = threading.Event()
        self._workers: List[threading.Thread] = []
        self._sources: List[queue.Queue] = []

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._broadcast.set_loop(loop)

    def register_queue(self, log_queue: queue.Queue) -> None:
        if log_queue in self._sources:
            return
        self._sources.append(log_queue)
        if self._workers:
            worker = threading.Thread(
                target=self._pump,
                args=(log_queue,),
                name=f"log-pump-{len(self._workers)}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

    def start(self) -> None:
        if self._workers:
            return
        self._stop_event.clear()
        for idx, src in enumerate(self._sources):
            worker = threading.Thread(
                target=self._pump, args=(src,), name=f"log-pump-{idx}", daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def stop(self) -> None:
        self._stop_event.set()
        for worker in self._workers:
            worker.join(timeout=1.0)
        self._workers.clear()

    def _pump(self, source: queue.Queue) -> None:
        while not self._stop_event.is_set():
            try:
                record = source.get(timeout=0.5)
            except queue.Empty:
                continue
            entry = self._normalize_record(record)
            self._history.append(entry)
            if self._loop:
                self._broadcast.publish_threadsafe(entry)

    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = record.get("time")
        if isinstance(timestamp, datetime):
            iso = timestamp.isoformat()
        else:
            iso = datetime.now(datetime.timezone.utc).isoformat()
        level = LEVEL_MAP.get(record.get("level", 1), "INFO")
        message = record.get("message", "")
        return {"time": iso, "level": level, "message": message}

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    async def subscribe(self) -> asyncio.Queue:
        if self._loop is None:
            raise RuntimeError("LogManager loop is not configured")
        return self._broadcast.subscribe()

    def unsubscribe(self, queue_obj: asyncio.Queue) -> None:
        self._broadcast.unsubscribe(queue_obj)

