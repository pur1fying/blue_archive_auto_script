from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from .base import ChannelClosed
from .framing import KIND_BYTES, KIND_CLOSE, KIND_ERROR, KIND_JSON
from .shm_native import CHUNK_BYTES, MAX_PAYLOAD_BYTES, PACKET_HEADER, SharedMemorySession

_CLOSED = object()


class SharedMemoryWriter:
    """One writer actor owns the outgoing slot index and whole packet order.

    Cancelling a channel task cannot interrupt a partially published packet.
    The normal path performs no thread-pool dispatch; only full slots wait in
    the executor, while this actor retains ownership of the current packet.
    """

    def __init__(self, session: SharedMemorySession, on_failure: Callable[[Exception], None]) -> None:
        self.session = session
        self._on_failure = on_failure
        self._queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
        self._task = asyncio.create_task(self._run(), name="shm-writer")

    async def write(self, stream: int, kind: int, payload: bytes) -> None:
        if self._closed:
            raise ChannelClosed("Shared-memory writer closed")
        if kind not in (KIND_JSON, KIND_BYTES, KIND_CLOSE, KIND_ERROR):
            raise ValueError(f"Unsupported shared-memory packet kind: {kind}")
        if len(payload) > MAX_PAYLOAD_BYTES:
            raise ValueError("Shared-memory payload exceeds the 64 MiB limit")
        future = asyncio.get_running_loop().create_future()
        self._queue.put_nowait((stream, kind, payload, future))
        await future

    async def _run(self) -> None:
        current = None
        try:
            while True:
                job = await self._queue.get()
                if job is None:
                    return
                stream, kind, payload, current = job
                if current.cancelled():
                    continue
                packet = PACKET_HEADER.pack(stream, kind, len(payload)) + payload
                for offset in range(0, len(packet), CHUNK_BYTES):
                    chunk = packet[offset:offset + CHUNK_BYTES]
                    if not self.session.write_chunk("p2r", chunk, block=False):
                        await asyncio.to_thread(self.session.write_chunk, "p2r", chunk)
                if not current.done():
                    current.set_result(None)
                current = None
        except Exception as exc:
            self._closed = True
            failure = exc if isinstance(exc, ChannelClosed) else ChannelClosed(str(exc))
            if current is not None and not current.done():
                current.set_exception(failure)
            self._fail_pending(failure)
            self.session.stop()
            self._on_failure(exc)

    def _fail_pending(self, exc: Exception) -> None:
        while not self._queue.empty():
            job = self._queue.get_nowait()
            if job is not None and not job[3].done():
                job[3].set_exception(exc)

    async def close(self) -> None:
        self._closed = True
        self.session.stop()
        self._fail_pending(ChannelClosed("Shared-memory writer closed"))
        self._queue.put_nowait(None)
        await self._task


class SharedMemoryChannelEndpoint:
    def __init__(self, stream: int, writer: SharedMemoryWriter) -> None:
        self.stream = stream
        self._writer = writer
        self._incoming: asyncio.Queue = asyncio.Queue()
        self._closed = False

    def feed_frame(self, kind: int, payload: bytes, release: Callable[[], None] = lambda: None) -> None:
        if self._closed:
            release()
            return
        if kind == KIND_CLOSE:
            self.connection_lost()
            release()
        elif kind == KIND_ERROR:
            self._incoming.put_nowait((ChannelClosed(payload.decode("utf-8", errors="replace")), None, release))
        elif kind in (KIND_JSON, KIND_BYTES):
            self._incoming.put_nowait((kind, payload, release))
        else:
            release()
            raise ValueError(f"Unsupported shared-memory packet kind: {kind}")

    def connection_lost(self) -> None:
        if not self._closed:
            self._closed = True
            while not self._incoming.empty():
                item = self._incoming.get_nowait()
                if item is not _CLOSED:
                    item[2]()
            self._incoming.put_nowait(_CLOSED)

    async def _recv(self, expected: int) -> bytes:
        item = await self._incoming.get()
        if item is _CLOSED:
            raise ChannelClosed("Shared-memory channel closed")
        kind, payload, release = item
        release()
        if isinstance(kind, Exception):
            raise kind
        if kind != expected:
            raise ChannelClosed(f"Unexpected shared-memory kind: expected {expected}, received {kind}")
        return payload

    async def recv_json(self) -> dict[str, Any]:
        payload = json.loads(await self._recv(KIND_JSON))
        if not isinstance(payload, dict):
            raise ValueError("Shared-memory JSON packet must contain an object")
        return payload

    async def recv_bytes(self) -> bytes:
        return await self._recv(KIND_BYTES)

    async def send_json(self, payload: dict[str, Any]) -> None:
        await self._send(KIND_JSON, json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))

    async def send_bytes(self, payload: bytes) -> None:
        await self._send(KIND_BYTES, payload)

    async def _send(self, kind: int, payload: bytes) -> None:
        if self._closed:
            raise ChannelClosed("Shared-memory channel closed")
        await self._writer.write(self.stream, kind, payload)

    def configure_binary_encryption(self, enabled: bool) -> None:
        pass

    async def close(self) -> None:
        if self._closed:
            return
        # Return incoming leases before an outgoing full ring can make the
        # close notification wait. The writer still preserves packet order.
        self.connection_lost()
        await self._writer.write(self.stream, KIND_CLOSE, b"")
