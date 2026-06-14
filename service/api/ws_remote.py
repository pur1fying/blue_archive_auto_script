from __future__ import annotations

from fastapi import APIRouter, WebSocket

from service.remote import ScrcpyProxySession

from .security import perform_business_resume, recv_stream_json
from .state import context

router = APIRouter()


@router.websocket("/ws/remote")
async def websocket_remote(websocket: WebSocket) -> None:
    proxy = None

    try:
        _, stream = await perform_business_resume(websocket, channel="remote")
        message = await recv_stream_json(websocket, stream)
        config_id = message.get("config_id")
        to_encrypt = message.get("decrypt", True)

        client = await context.runtime.require_remote_(config_id)
        proxy = ScrcpyProxySession(client, stream, encrypt_adb_to_ws=to_encrypt)
        await proxy.run(websocket)
    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        if proxy is not None:
            await proxy.close()
