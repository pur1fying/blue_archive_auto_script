from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Optional

from service.channels import (
    ProviderChannelHandler,
    RemoteChannelHandler,
    SyncChannelHandler,
    TriggerChannelHandler,
)

from .base import ChannelClosed
from .framing import KIND_ERROR, KIND_JSON, FrameDecoder, encode_frame
from .pipe_endpoint import PipeChannelEndpoint

_logger = logging.getLogger(__name__)
_HANDLERS = {
    "provider": ProviderChannelHandler,
    "sync": SyncChannelHandler,
    "trigger": TriggerChannelHandler,
    "remote": RemoteChannelHandler,
}


class _PipeProtocol(asyncio.Protocol):
    def __init__(self, service_context: Any) -> None:
        self._context = service_context
        self._transport: Optional[asyncio.Transport] = None
        self._endpoint: Optional[PipeChannelEndpoint] = None
        self._decoder = FrameDecoder()
        self._handler_task: Optional[asyncio.Task[None]] = None
        self._opened = False

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = transport  # type: ignore[assignment]
        self._endpoint = PipeChannelEndpoint(self._transport)

    def data_received(self, data: bytes) -> None:
        try:
            for kind, payload in self._decoder.feed(data):
                if not self._opened:
                    self._open_channel(kind, payload)
                elif self._endpoint is not None:
                    self._endpoint.feed_frame(kind, payload)
        except Exception as exc:  # noqa: BLE001 - protocol errors close only this client
            self._fail(exc)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if self._endpoint is not None:
            self._endpoint.connection_lost()
        if self._handler_task is not None:
            self._handler_task.cancel()

    def pause_writing(self) -> None:
        if self._endpoint is not None:
            self._endpoint.pause_writing()

    def resume_writing(self) -> None:
        if self._endpoint is not None:
            self._endpoint.resume_writing()

    def _open_channel(self, kind: int, payload: bytes) -> None:
        if kind != KIND_JSON:
            raise ValueError("The first pipe frame must be a JSON open request")
        request = json.loads(payload.decode("utf-8"))
        if request.get("type") != "open":
            raise ValueError("The first pipe message must be an open request")
        channel = str(request.get("channel", ""))
        handler_type = _HANDLERS.get(channel)
        if handler_type is None:
            raise ValueError(f"Unsupported pipe channel: {channel}")
        if self._endpoint is None:
            raise RuntimeError("Pipe endpoint was not initialized")
        self._opened = True
        self._handler_task = asyncio.create_task(self._run_handler(channel, handler_type(self._context)))

    async def _run_handler(self, channel: str, handler: Any) -> None:
        assert self._endpoint is not None
        try:
            await self._endpoint.send_json({"type": "open_ok", "channel": channel})
            await handler.handle(self._endpoint)
        except asyncio.CancelledError:
            return
        except ChannelClosed:
            _logger.debug("Pipe channel disconnected channel=%s", channel)
            return
        except Exception as exc:  # noqa: BLE001 - sent to the owning client
            _logger.exception("Pipe channel failed channel=%s: %s", channel, exc)
            self._fail(exc)
        finally:
            await self._endpoint.close()

    def _fail(self, exc: Exception) -> None:
        if self._transport is None or self._transport.is_closing():
            return
        message = str(exc).encode("utf-8", errors="replace")
        with suppress(Exception):
            self._transport.write(encode_frame(KIND_ERROR, message))
        self._transport.close()


class PipeTransportServer:
    def __init__(self, pipe_name: str, service_context: Any) -> None:
        self.pipe_name = pipe_name
        self.service_context = service_context
        self._servers: list[Any] = []
        self._unix_path: Optional[Path] = None

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        if os.name == "nt":
            start_serving_pipe = getattr(loop, "start_serving_pipe", None)
            if start_serving_pipe is None:
                raise RuntimeError("Named pipe transport requires the Windows Proactor event loop")
            self._servers = await start_serving_pipe(
                lambda: _PipeProtocol(self.service_context), self.pipe_name
            )
            _logger.info("Named pipe transport listening pipe=%s", self.pipe_name)
            return

        socket_path = Path(self.pipe_name)
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        socket_path.unlink(missing_ok=True)
        server = await loop.create_unix_server(
            lambda: _PipeProtocol(self.service_context), path=str(socket_path)
        )
        os.chmod(socket_path, 0o600)
        self._servers = [server]
        self._unix_path = socket_path
        _logger.info("Unix pipe transport listening path=%s", socket_path)

    async def close(self) -> None:
        for server in self._servers:
            server.close()
            wait_closed = getattr(server, "wait_closed", None)
            if wait_closed is not None:
                await wait_closed()
        self._servers.clear()
        if self._unix_path is not None:
            self._unix_path.unlink(missing_ok=True)
            self._unix_path = None
