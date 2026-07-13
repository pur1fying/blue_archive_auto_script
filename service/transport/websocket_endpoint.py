from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from service.auth import SecretStreamBox

from .base import ChannelClosed


class WebSocketChannelEndpoint:
    def __init__(self, websocket: WebSocket, stream: SecretStreamBox) -> None:
        self.websocket = websocket
        self.stream = stream
        self._encrypt_binary_outbound = True

    async def recv_json(self) -> dict[str, Any]:
        return json.loads((await self.recv_bytes()).decode("utf-8"))

    async def recv_bytes(self) -> bytes:
        try:
            frame = await self.websocket.receive_bytes()
        except WebSocketDisconnect as exc:
            raise ChannelClosed from exc
        return self.stream.decrypt(frame)

    async def send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        await self._send_frame(self.stream.encrypt(body))

    async def send_bytes(self, payload: bytes) -> None:
        frame = self.stream.encrypt(payload) if self._encrypt_binary_outbound else payload
        await self._send_frame(frame)

    async def _send_frame(self, payload: bytes) -> None:
        try:
            await self.websocket.send_bytes(payload)
        except (RuntimeError, WebSocketDisconnect) as exc:
            raise ChannelClosed from exc

    def configure_binary_encryption(self, enabled: bool) -> None:
        self._encrypt_binary_outbound = enabled

    async def close(self) -> None:
        with suppress(RuntimeError):
            await self.websocket.close()
