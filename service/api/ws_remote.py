from __future__ import annotations

import logging
from contextlib import suppress

from fastapi import APIRouter, WebSocket

from service.remote import ScrcpyProxySession

from .security import perform_business_resume, recv_stream_json
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.websocket("/ws/remote")
async def websocket_remote(websocket: WebSocket) -> None:
    proxy = None

    try:
        _logger.info("remote websocket accepted")
        _, stream = await perform_business_resume(websocket, channel="remote")
        _logger.info("remote secure session resumed")
        message = await recv_stream_json(websocket, stream)
        config_id = message.get("config_id")
        to_encrypt = message.get("decrypt", True)

        _logger.info("remote client initialization started config_id=%s", config_id)
        client = await context.runtime.require_remote_(config_id)
        _logger.info("remote client ready config_id=%s", config_id)
        proxy = ScrcpyProxySession(client, stream, encrypt_adb_to_ws=to_encrypt)
        await proxy.run(websocket)
    except Exception as exc:
        _logger.exception("remote websocket failed: %s", exc)
        with suppress(Exception):
            await websocket.close(code=1011, reason=f"remote: {type(exc).__name__}")
    finally:
        if proxy is not None:
            await proxy.close()
        _logger.info("remote websocket closed")
