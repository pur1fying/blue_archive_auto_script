from __future__ import annotations

import logging
from contextlib import suppress

from fastapi import APIRouter, HTTPException, WebSocket

from service.auth import AuthenticationError
from service.channels import TriggerChannelHandler
from service.transport import ChannelClosed, WebSocketChannelEndpoint

from .security import perform_business_resume
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.websocket("/ws/trigger")
async def websocket_trigger(websocket: WebSocket) -> None:
    try:
        _logger.debug("Trigger websocket connection started")
        _, stream = await perform_business_resume(websocket, channel="trigger")
        await TriggerChannelHandler(context).handle(WebSocketChannelEndpoint(websocket, stream))
    except (AuthenticationError, HTTPException, ValueError) as exc:
        _logger.warning("Trigger websocket authentication/protocol failure: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except ChannelClosed:
        _logger.debug("Trigger websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        _logger.exception("Trigger websocket failed: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        _logger.debug("Trigger websocket closed")
