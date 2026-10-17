from __future__ import annotations

import threading

from .base import ChannelClosed
from .shm_native import PACKET_HEADER, SharedMemorySession


class InboundLease:
    def __init__(self, budget: "InboundBudget", stream: int, size: int) -> None:
        self._budget = budget
        self._stream = stream
        self._size = size
        self._released = False

    def release(self) -> None:
        if not self._released:
            self._released = True
            self._budget.release(self._stream, self._size)


class InboundBudget:
    """Charge bytes from packet header admission until the handler consumes it.

    One shared lease covers reassembly, the loop bridge, and the stream queue.
    A single maximum-size packet is allowed when both budgets are empty; it
    keeps the producer blocked until that packet is consumed. The fixed charge
    also bounds the number of tiny/empty packets and their Python metadata.
    """

    def __init__(self, session: SharedMemorySession, total_bytes: int = 16 * 1024 * 1024,
                 stream_bytes: int = 8 * 1024 * 1024) -> None:
        if total_bytes <= 0 or stream_bytes <= 0:
            raise ValueError("Shared-memory byte budgets must be positive")
        self._session = session
        self._wake = session.new_wake_event()
        self._lock = threading.Lock()
        self._closed = False
        self._limit = total_bytes
        self._stream_limit = stream_bytes
        self._used = 0
        self._streams: dict[int, int] = {}
        self.peak_bytes = 0

    @property
    def used_bytes(self) -> int:
        with self._lock:
            return self._used

    def try_acquire(self, stream: int, payload_bytes: int) -> InboundLease | None:
        size = payload_bytes + PACKET_HEADER.size + 64
        with self._lock:
            if self._closed:
                raise ChannelClosed("Shared-memory inbound budget closed")
            used = self._streams.get(stream, 0)
            if (self._used and self._used + size > self._limit) or (used and used + size > self._stream_limit):
                return None
            self._used += size
            self._streams[stream] = used + size
            self.peak_bytes = max(self.peak_bytes, self._used)
            return InboundLease(self, stream, size)

    def acquire(self, stream: int, payload_bytes: int) -> InboundLease:
        while True:
            lease = self.try_acquire(stream, payload_bytes)
            if lease is not None:
                return lease
            # Auto-reset event retains a release racing this wait. Native stop
            # and owner-process handles cancel the wait without polling.
            self._session.wait_for_wake(self._wake)

    def release(self, stream: int, size: int) -> None:
        with self._lock:
            self._used -= size
            self._streams[stream] -= size
            if self._streams[stream] == 0:
                del self._streams[stream]
            if not self._closed:
                self._session.wake(self._wake)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._session.wake(self._wake)
