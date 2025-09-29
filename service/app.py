from __future__ import annotations

import contextlib
import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, Union

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from .context import ServiceContext
from .encryption import AuthenticationError, CipherBox, HandshakeSession, HandshakeResponse
from .messages import (
    CommandMessage,
    SyncPatchMessage,
    SyncPullMessage, ProviderRequest
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_shared_secret() -> str:
    # secret = os.getenv("BAAS_SERVICE_SECRET")
    secret = "FOSL"
    if secret:
        return secret
    fallback = PROJECT_ROOT / "config" / "service.secret"
    if fallback.exists():
        return fallback.read_text(encoding="utf-8").strip()
    raise RuntimeError("Shared secret not configured. Set BAAS_SERVICE_SECRET or config/service.secret")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global _SHARED_SECRET
    _SHARED_SECRET = _load_shared_secret()
    await context.startup()

    yield

    await context.shutdown()


app = FastAPI(title="BAAS Service Mode", lifespan=lifespan)
context = ServiceContext(PROJECT_ROOT)

_SHARED_SECRET: Union[str, None] = None


@app.get("/health")
async def health() -> Dict[str, Any]:
    status = context.runtime.current_status()
    return {"ok": True, "status": status}


async def _perform_handshake(websocket: WebSocket) -> tuple[HandshakeSession, CipherBox]:
    if _SHARED_SECRET is None:
        raise RuntimeError("Shared secret not initialised")
    await websocket.accept()
    session = HandshakeSession(_SHARED_SECRET)
    challenge = session.issue_challenge()
    await websocket.send_json({"type": "handshake", "challenge": challenge.challenge, "algorithm": challenge.algorithm})
    raw = await websocket.receive_json()
    response = HandshakeResponse(**raw)
    session.verify(response.response)
    await websocket.send_json({"type": "handshake_ok"})
    return session, session.build_cipher()


async def _sync_sender(websocket: WebSocket, cipher, queue: asyncio.Queue) -> None:
    try:
        while True:
            payload = dict(await queue.get())
            payload.setdefault("direction", "push")
            encrypted = cipher.encrypt_json(payload)
            await websocket.send_text(encrypted)
    except asyncio.CancelledError:
        pass


@app.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket) -> None:
    queue = None
    sender_task = None
    try:
        _, cipher = await _perform_handshake(websocket)
        queue = await context.config_manager.subscribe_updates()
        sender_task = asyncio.create_task(_sync_sender(websocket, cipher, queue))
        while True:
            encrypted = await websocket.receive_text()
            message = cipher.decrypt_json(encrypted)
            msg_type = message.get("type")
            if msg_type == "pull":
                data = SyncPullMessage(**message)
                snapshot = await context.config_manager.get_snapshot(data.resource, data.resource_id)
                response = {
                    "type": "snapshot",
                    "resource": data.resource,
                    "resource_id": data.resource_id,
                    "timestamp": snapshot.timestamp,
                    "data": snapshot.data,
                }
                await websocket.send_text(cipher.encrypt_json(response))
            elif msg_type == "patch":
                data = SyncPatchMessage(**message)
                snapshot = await context.config_manager.apply_patch(
                    data.resource, data.resource_id, data.ops, data.timestamp, origin="frontend"
                )
                response = {
                    "type": "patch_ack",
                    "resource": data.resource,
                    "resource_id": data.resource_id,
                    "timestamp": snapshot.timestamp,
                }
                await websocket.send_text(cipher.encrypt_json(response))
            elif msg_type == "list":
                snapshot = await context.config_manager.get_config_list()
                response = {
                    "type": "config_list",
                    "timestamp": snapshot.timestamp,
                    "data": snapshot.data,
                }
                await websocket.send_text(cipher.encrypt_json(response))
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported sync message: {msg_type}")
    except (AuthenticationError, HTTPException) as exc:
        await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.close(code=1011, reason=str(exc))
    finally:
        if sender_task:
            sender_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sender_task
        if queue is not None:
            context.config_manager.unsubscribe_updates(queue)


async def _provider_sender(websocket: WebSocket, cipher, queue: asyncio.Queue, envelope_type: str) -> None:
    try:
        while True:
            payload = await queue.get()
            response = {"type": envelope_type, envelope_type: payload} if envelope_type == "status" else {
                "type": envelope_type, "entry": payload}
            await websocket.send_text(cipher.encrypt_json(response))
    except asyncio.CancelledError:
        pass


@app.websocket("/ws/provider")
async def websocket_provider(websocket: WebSocket) -> None:
    log_queue = status_queue = None
    log_task = status_task = None
    try:
        _, cipher = await _perform_handshake(websocket)
        history = context.log_manager.get_history()
        scopes = context.log_manager.get_scopes()
        await websocket.send_text(cipher.encrypt_json({"type": "logs_full", "scopes": scopes, "entries": history}))
        await websocket.send_text(cipher.encrypt_json({"type": "status", "status": context.runtime.current_status()}))
        if context.runtime.all_data_initialized:
            await websocket.send_text(cipher.encrypt_json({"type": "status", "status": {"all_data_initialized": True}}))
        log_queue = await context.log_manager.subscribe()
        status_queue = await context.runtime.subscribe_status()
        log_task = asyncio.create_task(_provider_sender(websocket, cipher, log_queue, "log"))
        status_task = asyncio.create_task(_provider_sender(websocket, cipher, status_queue, "status"))
        while True:
            encrypted = await websocket.receive_text()
            message = cipher.decrypt_json(encrypted)
            req_type = message.get("type")
            if req_type == "static_request":
                ProviderRequest(**message)
                snapshot = await context.config_manager.get_static_snapshot()
                await websocket.send_text(
                    cipher.encrypt_json(
                        {
                            "type": "static_snapshot",
                            "timestamp": snapshot.timestamp,
                            "data": snapshot.data,
                        }
                    )
                )
            elif req_type == "status_request":
                await websocket.send_text(
                    cipher.encrypt_json({"type": "status", "status": context.runtime.current_status()}))
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider message: {req_type}")
    except (AuthenticationError, HTTPException) as exc:
        await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.close(code=1011, reason=str(exc))
    finally:
        for task in (log_task, status_task):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        if log_queue is not None:
            context.log_manager.unsubscribe(log_queue)
        if status_queue is not None:
            context.runtime.unsubscribe_status(status_queue)


@app.websocket("/ws/receiver")
async def websocket_receiver(websocket: WebSocket) -> None:
    try:
        _, cipher = await _perform_handshake(websocket)
        while True:
            encrypted = await websocket.receive_text()
            message = cipher.decrypt_json(encrypted)
            cmd = CommandMessage(**message)
            response_payload: Dict[str, Any]
            try:
                if cmd.command == "start_scheduler":
                    if not cmd.config_id:
                        raise ValueError("config_id is required")
                    result = await context.runtime.start_scheduler(cmd.config_id)
                    context.ensure_runtime_logger_attached()
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "stop_scheduler":
                    result = await context.runtime.stop_scheduler()
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "solve":
                    task = cmd.payload.get("task")
                    if not task:
                        raise ValueError("task is required for solve command")
                    result = await context.runtime.solve_task(task)
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command.startswith("start_"):
                    result = await context.runtime.solve_task(cmd.command)
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "detect_adb":
                    result = await context.runtime.detect_adb()
                    response_payload = {"status": "ok", "data": {"addresses": result}}
                elif cmd.command == "status":
                    response_payload = {"status": "ok", "data": context.runtime.current_status()}
                else:
                    raise ValueError(f"Unsupported command '{cmd.command}'")
            except Exception as inner_exc:  # noqa: BLE001 - convert to payload
                response_payload = {"status": "error", "error": str(inner_exc)}
            await websocket.send_text(
                cipher.encrypt_json(
                    {
                        "type": "command_response",
                        "command": cmd.command,
                        **response_payload,
                        "timestamp": time.time(),
                    }
                )
            )
    except (AuthenticationError, HTTPException) as exc:
        await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.close(code=1011, reason=str(exc))
