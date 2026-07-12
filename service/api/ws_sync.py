from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from service.auth import AuthenticationError, SecretStreamBox
from service.types import SyncPatchMessage, SyncPullMessage
from service.utils.diff import PatchConflictError

from .security import perform_business_resume, recv_stream_json, send_stream_json
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


async def sync_sender(
    websocket: WebSocket,
    stream: SecretStreamBox,
    queue: asyncio.Queue,
    send_lock: asyncio.Lock | None = None,
) -> None:
    send_lock = send_lock or asyncio.Lock()
    try:
        while True:
            payload = dict(await queue.get())
            payload.setdefault("direction", "push")
            async with send_lock:
                await send_stream_json(websocket, stream, payload)
    except asyncio.CancelledError:
        pass


async def apply_sync_patch(data: SyncPatchMessage) -> dict:
    """Apply one patch and return a recoverable response for stale snapshots."""
    try:
        await context.config_manager.apply_patch(
            data.resource,
            data.resource_id,
            data.ops,
            data.timestamp,
            origin="frontend",
        )
    except PatchConflictError as exc:
        snapshot = await context.config_manager.get_snapshot(data.resource, data.resource_id)
        _logger.info(
            "Sync patch conflict resource=%s resource_id=%s request_timestamp=%s snapshot_timestamp=%s",
            data.resource,
            data.resource_id,
            data.timestamp,
            snapshot.timestamp,
        )
        return {
            "type": "patch_conflict",
            "resource": data.resource,
            "resource_id": data.resource_id,
            "request_timestamp": data.timestamp,
            "timestamp": snapshot.timestamp,
            "data": snapshot.data,
            "error": str(exc),
        }
    return {
        "type": "patch_ack",
        "resource": data.resource,
        "resource_id": data.resource_id,
        "timestamp": data.timestamp,
    }


@router.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket) -> None:
    queue = None
    sender_task = None
    try:
        _logger.debug("Sync websocket connection started")
        _, stream = await perform_business_resume(websocket, channel="sync")
        _logger.debug("Sync websocket secure session resumed")
        send_lock = asyncio.Lock()
        queue = await context.config_manager.subscribe_updates()
        sender_task = asyncio.create_task(sync_sender(websocket, stream, queue, send_lock))
        while True:
            message = await recv_stream_json(websocket, stream)
            msg_type = message.get("type")
            if msg_type == "pull":
                data = SyncPullMessage(**message)
                _logger.debug("Sync pull resource=%s resource_id=%s", data.resource, data.resource_id)
                snapshot = await context.config_manager.get_snapshot(data.resource, data.resource_id)
                async with send_lock:
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
                _logger.debug(
                    "Sync patch resource=%s resource_id=%s operations=%s",
                    data.resource,
                    data.resource_id,
                    len(data.ops),
                )
                response = await apply_sync_patch(data)
                async with send_lock:
                    await send_stream_json(websocket, stream, response)
            elif msg_type == "list":
                snapshot = await context.config_manager.get_config_list()
                async with send_lock:
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
        _logger.warning("Sync websocket authentication/protocol failure: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        _logger.debug("Sync websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        _logger.exception("Sync websocket failed: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        if sender_task:
            sender_task.cancel()
            with suppress(asyncio.CancelledError):
                await sender_task
        if queue is not None:
            context.config_manager.unsubscribe_updates(queue)
        _logger.debug("Sync websocket closed")
