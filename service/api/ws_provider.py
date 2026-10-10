from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket

from service.auth import AuthenticationError, SecretStreamBox
from service.channels import ProviderChannelHandler
from service.transport import ChannelClosed, WebSocketChannelEndpoint

from .security import perform_business_resume, send_stream_json
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


async def provider_sender(
    websocket: WebSocket,
    stream: SecretStreamBox,
    queue: asyncio.Queue,
    envelope_type: str,
    send_lock: Optional[asyncio.Lock] = None,
) -> None:
    """Compatibility helper retained for focused WebSocket behavior tests."""
    send_lock = send_lock or asyncio.Lock()
    try:
        while True:
            payload = await queue.get()
            key = "status" if envelope_type == "status" else "entry"
            async with send_lock:
                await send_stream_json(websocket, stream, {"type": envelope_type, key: payload})
    except asyncio.CancelledError:
        return


@router.websocket("/ws/provider")
async def websocket_provider(websocket: WebSocket) -> None:
    try:
        _logger.debug("Provider websocket connection started")
        _, stream = await perform_business_resume(websocket, channel="provider")
        await ProviderChannelHandler(context).handle(WebSocketChannelEndpoint(websocket, stream))
    except (AuthenticationError, HTTPException, ValueError) as exc:
        _logger.warning("Provider websocket authentication/protocol failure: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except ChannelClosed:
        _logger.debug("Provider websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        _logger.exception("Provider websocket failed: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        _logger.debug("Provider websocket closed")
