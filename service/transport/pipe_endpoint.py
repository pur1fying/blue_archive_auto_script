from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Any, Optional

from .base import ChannelClosed
from .framing import KIND_BYTES, KIND_CLOSE, KIND_ERROR, KIND_JSON, encode_frame, encode_json

_CLOSED = object()


class PipeChannelEndpoint:
    def __init__(self, transport: asyncio.Transport) -> None:
        self._transport = transport
        self._incoming: asyncio.Queue[object] = asyncio.Queue()
        self._send_lock = asyncio.Lock()
        self._writable = asyncio.Event()
        self._writable.set()
        self._closed = False

    def feed_frame(self, kind: int, payload: bytes) -> None:
        if kind == KIND_CLOSE:
            self.connection_lost()
        elif kind in (KIND_JSON, KIND_BYTES):
            self._incoming.put_nowait((kind, payload))
        elif kind == KIND_ERROR:
            self._incoming.put_nowait(ChannelClosed(payload.decode("utf-8", errors="replace")))
        else:
            self._incoming.put_nowait(ChannelClosed(f"Unsupported pipe frame kind: {kind}"))

    def connection_lost(self) -> None:
        if not self._closed:
            self._closed = True
            self._incoming.put_nowait(_CLOSED)
        self._writable.set()

    def pause_writing(self) -> None:
        self._writable.clear()

    def resume_writing(self) -> None:
        self._writable.set()

    async def _recv(self, expected_kind: int) -> bytes:
        item = await self._incoming.get()
        if item is _CLOSED:
            raise ChannelClosed("Pipe connection closed")
        if isinstance(item, Exception):
            raise item
        kind, payload = item  # type: ignore[misc]
        if kind != expected_kind:
            raise ChannelClosed(f"Unexpected pipe frame kind: expected {expected_kind}, received {kind}")
        return payload

    async def recv_json(self) -> dict[str, Any]:
        payload = await self._recv(KIND_JSON)
        value = json.loads(payload.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Pipe JSON frame must contain an object")
        return value

    async def recv_bytes(self) -> bytes:
        return await self._recv(KIND_BYTES)

    async def _send(self, frame: bytes) -> None:
        if self._closed or self._transport.is_closing():
            raise ChannelClosed("Pipe connection closed")
        async with self._send_lock:
            await self._writable.wait()
            if self._closed or self._transport.is_closing():
                raise ChannelClosed("Pipe connection closed")
            self._transport.write(frame)

    async def send_json(self, payload: dict[str, Any]) -> None:
        await self._send(encode_json(payload))

    async def send_bytes(self, payload: bytes) -> None:
        await self._send(encode_frame(KIND_BYTES, payload))

    def configure_binary_encryption(self, enabled: bool) -> None:
        pass

    async def close(self) -> None:
        if self._closed:
            return
        with suppress(Exception):
            await self._send(encode_frame(KIND_CLOSE))
        self._closed = True
        self._transport.close()


class InMemoryChannelEndpoint:
    """Test endpoint that exercises handlers without binding a transport."""

    def __init__(self) -> None:
        self.incoming: asyncio.Queue[object] = asyncio.Queue()
        self.outgoing: asyncio.Queue[tuple[int, bytes]] = asyncio.Queue()
        self.closed = False

    async def recv_json(self) -> dict[str, Any]:
        item = await self.incoming.get()
        if item is _CLOSED:
            raise ChannelClosed
        if not isinstance(item, dict):
            raise TypeError("Expected JSON object")
        return item

    async def recv_bytes(self) -> bytes:
        item = await self.incoming.get()
        if item is _CLOSED:
            raise ChannelClosed
        if not isinstance(item, bytes):
            raise TypeError("Expected bytes")
        return item

    async def send_json(self, payload: dict[str, Any]) -> None:
        await self.outgoing.put((KIND_JSON, json.dumps(payload).encode()))

    async def send_bytes(self, payload: bytes) -> None:
        await self.outgoing.put((KIND_BYTES, payload))

    def configure_binary_encryption(self, enabled: bool) -> None:
        pass

    async def close(self) -> None:
        self.closed = True
