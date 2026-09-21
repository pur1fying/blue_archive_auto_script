import asyncio
import threading
from typing import Any, List, Set, Union


class BroadcastChannel:
    """Simple multi-consumer broadcast based on asyncio queues."""

    def __init__(self, loop: Union[asyncio.AbstractEventLoop, None] = None, max_queue_size: int = 128) -> None:
        self._loop = loop
        self._max_queue_size = max_queue_size
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = threading.Lock()

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue_size)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, message: Any) -> None:
        with self._lock:
            subscribers: List[asyncio.Queue] = list(self._subscribers)
        for queue in subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    # Give up if subscriber never consumes
                    pass

    def publish_threadsafe(self, message: Any) -> None:
        if self._loop is None:
            raise RuntimeError("Event loop is not set for BroadcastChannel")
        asyncio.run_coroutine_threadsafe(self.publish(message), self._loop)
