from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from service.auth import ActiveSession, AuthenticationError
from service.utils.timestamps import unix_timestamp_ms

from .security import (
    begin_server_hello,
    control_heartbeat_sender,
    control_sender,
    finalize_control_auth,
)
from .state import context

router = APIRouter()


@router.websocket("/ws/control")
async def websocket_control(websocket: WebSocket) -> None:
    revoke_queue = None
    sender_task = heartbeat_task = None
    session: Optional[ActiveSession] = None
    try:
        handshake, preauth_channel, _ = await begin_server_hello(websocket, kind="control", channel="control")
        request = preauth_channel.decrypt(await websocket.receive_json())
        session, control_channel = await finalize_control_auth(
            websocket,
            handshake=handshake,
            preauth_channel=preauth_channel,
            request=request,
        )
        if session is None:
            raise ValueError("Session not found")
        revoke_queue = context.auth_manager.subscribe_control(session.session_id)
        sender_task = asyncio.create_task(
            control_sender(
                websocket,
                control_channel=control_channel,
                revoke_queue=revoke_queue,
            )
        )
        heartbeat_task = asyncio.create_task(
            control_heartbeat_sender(
                websocket,
                control_channel=control_channel,
                interval=3.0,
            )
        )
        while True:
            message = control_channel.decrypt(await websocket.receive_json())
            msg_type = message.get("type")
            if msg_type == "ping":
                await websocket.send_json(control_channel.encrypt({"type": "pong", "timestamp": unix_timestamp_ms()}))
            elif msg_type == "change_password":
                new_password = str(message.get("new_password", ""))
                await context.auth_manager.change_password(session_id=session.session_id, new_password=new_password)
                return
            else:
                raise AuthenticationError(f"Unsupported control message: {msg_type}")
    except (AuthenticationError, HTTPException) as exc:
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
        if session is not None and revoke_queue is not None:
            context.auth_manager.unsubscribe_control(session.session_id, revoke_queue)
        for task in (sender_task, heartbeat_task):
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
