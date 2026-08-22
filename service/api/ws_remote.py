from __future__ import annotations

import logging
from contextlib import suppress

from fastapi import APIRouter, WebSocket

from service.channels import RemoteChannelHandler
from service.transport import ChannelClosed, WebSocketChannelEndpoint

from .security import perform_business_resume
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.websocket("/ws/remote")
async def websocket_remote(websocket: WebSocket) -> None:
    try:
        _logger.info("Remote websocket accepted")
        _, stream = await perform_business_resume(websocket, channel="remote")
        await RemoteChannelHandler(context).handle(WebSocketChannelEndpoint(websocket, stream))
    except ChannelClosed:
        _logger.info("Remote websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - remote failures are scoped to this connection
        _logger.exception("Remote websocket failed: %s", exc)
        with suppress(Exception):
            await websocket.close(code=1011, reason=f"remote: {type(exc).__name__}")
    finally:
        _logger.info("Remote websocket closed")
