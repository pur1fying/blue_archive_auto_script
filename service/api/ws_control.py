from __future__ import annotations

import asyncio
import logging
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
_logger = logging.getLogger(__name__)


async def _stop_control_senders(*tasks: Optional[asyncio.Task]) -> None:
    for task in tasks:
        if task is not None:
            task.cancel()
    for task in tasks:
        if task is not None:
            with suppress(asyncio.CancelledError):
                await task


@router.websocket("/ws/control")
async def websocket_control(websocket: WebSocket) -> None:
    revoke_queue = None
    sender_task = heartbeat_task = None
    write_lock = asyncio.Lock()
    session: Optional[ActiveSession] = None
    try:
        _logger.debug("Control websocket connection started")
        handshake, preauth_channel, _ = await begin_server_hello(websocket, kind="control", channel="control")
        _logger.debug("Control websocket server hello completed")
        request = preauth_channel.decrypt(await websocket.receive_json())
        _logger.debug("Control websocket preauth request received type=%s", request.get("type"))
        session, control_channel = await finalize_control_auth(
            websocket,
            handshake=handshake,
            preauth_channel=preauth_channel,
            request=request,
        )
        if session is None:
            raise ValueError("Session not found")
        _logger.info("Control websocket authenticated session_id=%s", session.session_id)
        revoke_queue = context.auth_manager.subscribe_control(session.session_id)
        sender_task = asyncio.create_task(
            control_sender(
                websocket,
                control_channel=control_channel,
                revoke_queue=revoke_queue,
                write_lock=write_lock,
            )
        )
        heartbeat_task = asyncio.create_task(
            control_heartbeat_sender(
                websocket,
                control_channel=control_channel,
                interval=3.0,
                write_lock=write_lock,
            )
        )
        while True:
            message = control_channel.decrypt(await websocket.receive_json())
            msg_type = message.get("type")
            if msg_type == "ping":
                async with write_lock:
                    await websocket.send_json(control_channel.encrypt({"type": "pong", "timestamp": unix_timestamp_ms()}))
            elif msg_type == "change_password":
                new_password = message.get("new_password")
                if not isinstance(new_password, str) or not new_password.strip():
                    raise AuthenticationError("New key is required")
                request_id = message.get("request_id")
                if request_id is not None and (
                    not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 128
                ):
                    raise AuthenticationError("Invalid key change request ID")

                # Finish any in-flight write before cancelling senders, preserving
                # encrypted frame order and ownership through acknowledgement/close.
                async with write_lock:
                    await _stop_control_senders(sender_task, heartbeat_task)
                    sender_task = heartbeat_task = None
                    _logger.info("Key change requested session_id=%s", session.session_id)
                    state = await context.auth_manager.change_password(
                        session_id=session.session_id, new_password=new_password
                    )
                    if request_id is not None:
                        await websocket.send_json(control_channel.encrypt({
                            "type": "key_changed",
                            "request_id": request_id,
                            "pwd_epoch": state.pwd_epoch,
                        }))
                    await websocket.send_json(control_channel.encrypt({
                        "type": "auth_revoked",
                        "reason": "password_changed",
                        "pwd_epoch": state.pwd_epoch,
                    }))
                    await websocket.close(code=4401, reason="password_changed")
                return
            else:
                raise AuthenticationError(f"Unsupported control message: {msg_type}")
    except (AuthenticationError, HTTPException) as exc:
        _logger.warning("Control websocket authentication/protocol failure: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        _logger.debug("Control websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        _logger.exception("Control websocket failed: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        if session is not None and revoke_queue is not None:
            context.auth_manager.unsubscribe_control(session.session_id, revoke_queue)
        await _stop_control_senders(sender_task, heartbeat_task)
        _logger.debug("Control websocket closed")
