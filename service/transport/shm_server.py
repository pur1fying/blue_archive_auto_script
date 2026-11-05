from __future__ import annotations

import asyncio
import json
import logging
import threading
from contextlib import suppress
from typing import Any

from .base import ChannelClosed
from .framing import KIND_CLOSE, KIND_ERROR, KIND_JSON
from .pipe_server import _HANDLERS
from .shm_budget import InboundBudget, InboundLease
from .shm_endpoint import SharedMemoryChannelEndpoint, SharedMemoryWriter
from .shm_native import PacketDecoder, SharedMemorySession

_logger = logging.getLogger(__name__)


class SharedMemoryTransportServer:
    def __init__(self, base: str, service_context: Any, *, inbound_bytes: int = 16 * 1024 * 1024,
                 stream_bytes: int = 8 * 1024 * 1024) -> None:
        self.base = base
        self.context = service_context
        self._session: SharedMemorySession | None = None
        self._writer: SharedMemoryWriter | None = None
        self._reader: threading.Thread | None = None
        self._endpoints: dict[int, SharedMemoryChannelEndpoint] = {}
        self._handlers: dict[int, asyncio.Task] = {}
        self._closed = False
        self._close_task: asyncio.Task | None = None
        self._close_complete = asyncio.Event()
        self._budget: InboundBudget | None = None
        self._inbound_bytes = inbound_bytes
        self._stream_bytes = stream_bytes

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self._session = SharedMemorySession(self.base)
        self._session.publish_peer_pid()
        self._budget = InboundBudget(self._session, self._inbound_bytes, self._stream_bytes)
        self._writer = SharedMemoryWriter(self._session, self._connection_failed)
        self._reader = threading.Thread(target=self._read_loop, args=(loop,), name="shm-reader", daemon=True)
        self._reader.start()
        try:
            await self._writer.write(0, KIND_JSON, b'{"type":"ready","transport":"shm","version":1}')
        except BaseException:
            await self.close()
            raise
        _logger.info("Shared-memory transport ready base=%s", self.base)

    def _read_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        assert self._session is not None
        assert self._budget is not None
        pending: list[tuple[int, int, bytes, InboundLease]] = []
        pending_bytes = 0
        inflight: InboundLease | None = None

        def flush() -> None:
            nonlocal pending, pending_bytes
            if pending:
                loop.call_soon_threadsafe(self._dispatch_packets, pending)
                pending = []
                pending_bytes = 0

        def admit(stream: int, kind: int, length: int) -> None:
            nonlocal inflight
            inflight = self._budget.try_acquire(stream, length)
            if inflight is None:
                # Give the loop ownership of already admitted packets before
                # waiting for a consumer to return their byte budget.
                flush()
                inflight = self._budget.acquire(stream, length)

        def complete(stream: int, kind: int, payload: bytes) -> None:
            nonlocal inflight, pending_bytes
            assert inflight is not None
            pending.append((stream, kind, payload, inflight))
            inflight = None
            pending_bytes += len(payload)
            if len(pending) >= 64 or pending_bytes >= 256 * 1024:
                flush()

        decoder = PacketDecoder(admit, complete)
        try:
            while True:
                chunk = self._session.read_chunk("r2p")
                decoder.feed(chunk)
                # Drain an available burst before crossing into the event loop.
                for _ in range(63):
                    chunk = self._session.read_chunk("r2p", block=False)
                    if chunk is None:
                        break
                    decoder.feed(chunk)
                flush()
        except Exception as exc:
            if not self._closed:
                loop.call_soon_threadsafe(self._connection_failed, exc)
        finally:
            if inflight is not None:
                inflight.release()
            for _, _, _, lease in pending:
                lease.release()

    def _dispatch_packets(self, packets: list[tuple[int, int, bytes, InboundLease]]) -> None:
        if self._closed:
            for _, _, _, lease in packets:
                lease.release()
            return
        assert self._writer is not None
        remaining = iter(packets)
        try:
            for stream, kind, payload, lease in remaining:
                transferred = False
                try:
                    if stream == 0:
                        if kind == KIND_CLOSE:
                            raise ChannelClosed("Shared-memory owner closed session")
                        raise ValueError("Business packets must use a nonzero shared-memory stream")
                    endpoint = self._endpoints.get(stream)
                    if endpoint is None:
                        # Both peers may finish a stream at the same time.
                        if kind == KIND_CLOSE:
                            continue
                        if kind != KIND_JSON:
                            raise ValueError("The first shared-memory stream packet must be JSON open")
                        request = json.loads(payload)
                        channel = str(request.get("channel", ""))
                        if request.get("type") != "open" or channel not in _HANDLERS:
                            raise ValueError(f"Unsupported shared-memory open request: {channel}")
                        endpoint = SharedMemoryChannelEndpoint(stream, self._writer)
                        self._endpoints[stream] = endpoint
                        self._handlers[stream] = asyncio.create_task(
                            self._run_handler(stream, channel, endpoint), name=f"shm-{channel}-{stream}"
                        )
                    else:
                        transferred = True
                        endpoint.feed_frame(kind, payload, lease.release)
                        if kind == KIND_CLOSE:
                            task = self._handlers.get(stream)
                            if task is not None:
                                task.cancel()
                finally:
                    if not transferred:
                        lease.release()
        except Exception as exc:
            for _, _, _, lease in remaining:
                lease.release()
            self._connection_failed(exc)

    async def _run_handler(self, stream: int, channel: str, endpoint: SharedMemoryChannelEndpoint) -> None:
        try:
            await endpoint.send_json({"type": "open_ok", "channel": channel})
            await _HANDLERS[channel](self.context).handle(endpoint)
        except (asyncio.CancelledError, ChannelClosed):
            pass
        except Exception as exc:
            _logger.exception("Shared-memory channel failed stream=%s channel=%s", stream, channel)
            with suppress(ChannelClosed):
                await endpoint._send(KIND_ERROR, str(exc).encode("utf-8", errors="replace"))
        finally:
            with suppress(ChannelClosed):
                await endpoint.close()
            self._endpoints.pop(stream, None)
            self._handlers.pop(stream, None)

    def _connection_failed(self, exc: Exception) -> None:
        if self._closed:
            return
        _logger.info("Shared-memory session disconnected: %s", exc)
        asyncio.create_task(self.close(), name="shm-close")

    async def close(self) -> None:
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._close(), name="shm-close-workers")
        await asyncio.shield(self._close_task)

    async def wait_closed(self) -> None:
        await self._close_complete.wait()

    async def _close(self) -> None:
        self._closed = True
        try:
            if self._session is not None:
                self._session.stop()
            if self._budget is not None:
                self._budget.close()
            for endpoint in self._endpoints.values():
                endpoint.connection_lost()
            tasks = list(self._handlers.values())
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            if self._writer is not None:
                await self._writer.close()
            if self._reader is not None:
                await asyncio.to_thread(self._reader.join)
                self._reader = None
            if self._session is not None:
                self._session.close()
                self._session = None
        finally:
            self._close_complete.set()
