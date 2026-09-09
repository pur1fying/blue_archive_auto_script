from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from fastapi import APIRouter, HTTPException, WebSocket

from service.auth import AuthenticationError, SecretStreamBox
from service.channels import SyncChannelHandler
from service.transport import ChannelClosed, WebSocketChannelEndpoint
from service.types import SyncPatchMessage

from .security import perform_business_resume, send_stream_json
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


async def sync_sender(
    websocket: WebSocket,
    stream: SecretStreamBox,
    queue: asyncio.Queue,
    send_lock: asyncio.Lock | None = None,
) -> None:
    """Compatibility helper retained for focused WebSocket behavior tests."""
    send_lock = send_lock or asyncio.Lock()
    try:
        while True:
            payload = dict(await queue.get())
            payload.setdefault("direction", "push")
            async with send_lock:
                await send_stream_json(websocket, stream, payload)
    except asyncio.CancelledError:
        return


async def apply_sync_patch(data: SyncPatchMessage) -> dict:
    """Compatibility entry point backed by the transport-neutral handler."""
    return await SyncChannelHandler(context)._handle_message(
        {
            "type": "patch",
            "resource": data.resource,
            "resource_id": data.resource_id,
            "timestamp": data.timestamp,
            "ops": data.ops,
        }
    )


@router.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket) -> None:
    try:
        _logger.debug("Sync websocket connection started")
        _, stream = await perform_business_resume(websocket, channel="sync")
        await SyncChannelHandler(context).handle(WebSocketChannelEndpoint(websocket, stream))
    except (AuthenticationError, HTTPException, ValueError) as exc:
        _logger.warning("Sync websocket authentication/protocol failure: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except ChannelClosed:
        _logger.debug("Sync websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        _logger.exception("Sync websocket failed: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        _logger.debug("Sync websocket closed")
