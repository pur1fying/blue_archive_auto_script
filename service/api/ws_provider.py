from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from service.auth import AuthenticationError, SecretStreamBox
from service.types import ProviderRequest

from .security import perform_business_resume, recv_stream_json, send_stream_json
from .state import context

router = APIRouter()


async def provider_sender(
    websocket: WebSocket,
    stream: SecretStreamBox,
    queue: asyncio.Queue,
    envelope_type: str,
) -> None:
    try:
        while True:
            payload = await queue.get()
            if envelope_type == "status":
                response = {"type": envelope_type, "status": payload}
            else:
                response = {"type": envelope_type, "entry": payload}
            await send_stream_json(websocket, stream, response)
    except asyncio.CancelledError:
        pass


@router.websocket("/ws/provider")
async def websocket_provider(websocket: WebSocket) -> None:
    log_queue = status_queue = None
    log_task = status_task = None
    try:
        _, stream = await perform_business_resume(websocket, channel="provider")
        history = context.log_manager.get_history()
        scopes = context.log_manager.get_scopes()
        await send_stream_json(websocket, stream, {"type": "logs_full", "scopes": scopes, "entries": history})
        await send_stream_json(websocket, stream, {"type": "status", "status": context.runtime.current_status()})
        if context.runtime.is_all_data_initialized:
            await send_stream_json(websocket, stream, {"type": "status", "status": {"is_all_data_initialized": True}})
        log_queue = await context.log_manager.subscribe()
        status_queue = await context.runtime.subscribe_status()
        log_task = asyncio.create_task(provider_sender(websocket, stream, log_queue, "log"))
        status_task = asyncio.create_task(provider_sender(websocket, stream, status_queue, "status"))
        while True:
            message = await recv_stream_json(websocket, stream)
            req_type = message.get("type")
            if req_type == "static_request":
                ProviderRequest(**message)
                snapshot = await context.config_manager.get_static_snapshot()
                await send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "static_snapshot",
                        "timestamp": snapshot.timestamp,
                        "data": snapshot.data,
                    },
                )
            elif req_type == "status_request":
                await send_stream_json(websocket, stream, {"type": "status", "status": context.runtime.current_status()})
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider message: {req_type}")
    except (AuthenticationError, HTTPException) as exc:
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        for task in (log_task, status_task):
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        if log_queue is not None:
            context.log_manager.unsubscribe(log_queue)
        if status_queue is not None:
            context.runtime.unsubscribe_status(status_queue)
