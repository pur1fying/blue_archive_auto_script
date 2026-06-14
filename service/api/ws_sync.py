from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from service.auth import AuthenticationError, SecretStreamBox
from service.types import SyncPatchMessage, SyncPullMessage

from .security import perform_business_resume, recv_stream_json, send_stream_json
from .state import context

router = APIRouter()


async def sync_sender(websocket: WebSocket, stream: SecretStreamBox, queue: asyncio.Queue) -> None:
    try:
        while True:
            payload = dict(await queue.get())
            payload.setdefault("direction", "push")
            await send_stream_json(websocket, stream, payload)
    except asyncio.CancelledError:
        pass


@router.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket) -> None:
    queue = None
    sender_task = None
    try:
        _, stream = await perform_business_resume(websocket, channel="sync")
        queue = await context.config_manager.subscribe_updates()
        sender_task = asyncio.create_task(sync_sender(websocket, stream, queue))
        while True:
            message = await recv_stream_json(websocket, stream)
            msg_type = message.get("type")
            if msg_type == "pull":
                data = SyncPullMessage(**message)
                snapshot = await context.config_manager.get_snapshot(data.resource, data.resource_id)
                await send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "snapshot",
                        "resource": data.resource,
                        "resource_id": data.resource_id,
                        "timestamp": snapshot.timestamp,
                        "data": snapshot.data,
                    },
                )
            elif msg_type == "patch":
                data = SyncPatchMessage(**message)
                await context.config_manager.apply_patch(
                    data.resource,
                    data.resource_id,
                    data.ops,
                    data.timestamp,
                    origin="frontend",
                )
                await send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "patch_ack",
                        "resource": data.resource,
                        "resource_id": data.resource_id,
                        "timestamp": data.timestamp,
                    },
                )
            elif msg_type == "list":
                snapshot = await context.config_manager.get_config_list()
                await send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "config_list",
                        "timestamp": snapshot.timestamp,
                        "data": snapshot.data,
                    },
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported sync message: {msg_type}")
    except (AuthenticationError, HTTPException) as exc:
        import traceback

        traceback.print_exc()
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        import traceback

        traceback.print_exc()
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        if sender_task:
            sender_task.cancel()
            with suppress(asyncio.CancelledError):
                await sender_task
        if queue is not None:
            context.config_manager.unsubscribe_updates(queue)
