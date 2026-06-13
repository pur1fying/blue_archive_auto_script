from __future__ import annotations

import asyncio
import contextlib
import json
import os
import time
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
# from starlette.staticfiles import StaticFiles

from .context import ServiceContext
from .encryption import (
    ActiveSession,
    AuthenticationError,
    HandshakeContext,
    JsonChaChaChannel,
    PROTOCOL_VERSION,
    SecretStreamBox,
    b64d,
    b64e,
)
from .lib.scrcpy import EVENT_STREAM
from .messages import CommandMessage, ProviderRequest, SyncPatchMessage, SyncPullMessage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMEMBER_COOKIE_NAME = "baas_remember"
REMEMBER_COOKIE_MAX_AGE = int(os.getenv("BAAS_REMEMBER_TTL_SECONDS", str(60 * 60 * 24 * 180)))
context = ServiceContext(PROJECT_ROOT)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await context.startup()
    yield
    await context.shutdown()


app = FastAPI(title="BAAS Service Mode", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origin_regex=os.getenv(
        "BAAS_SERVICE_CORS_ORIGIN_REGEX",
        r"^https?://(localhost|tauri\.localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$",
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _is_allowed_origin(origin: str | None, host: str | None) -> bool:
    if not origin:
        return True
    allowed = {item.strip() for item in os.getenv("BAAS_SERVICE_ALLOWED_ORIGINS", "").split(",") if item.strip()}
    if origin in allowed:
        return True
    parsed = urlparse(origin)
    origin_host = parsed.hostname
    host_value = host or ""
    if host_value.startswith("[") and "]" in host_value:
        request_host = host_value[1:].split("]", 1)[0]
    else:
        request_host = host_value.split(":", 1)[0]
    if origin_host in {"localhost", "127.0.0.1", "::1", "tauri.localhost"}:
        return True
    return bool(origin_host and request_host and origin_host == request_host)


def _cookie_secure(request: Request) -> bool:
    forced = os.getenv("BAAS_REMEMBER_COOKIE_SECURE")
    if forced is not None:
        return forced.lower() in {"1", "true", "yes", "on"}
    return request.url.scheme == "https"


def _auth_ok_payload(session: ActiveSession, *, include_session_secrets: bool = False) -> dict[str, Any]:
    payload = {
        "type": "auth_ok",
        "protocol_version": PROTOCOL_VERSION,
        "session_id": session.session_id,
        "resume_ticket": context.auth_manager.issue_resume_ticket(session),
        "expires_at": session.expires_at,
        "pwd_epoch": session.pwd_epoch,
        "pwd_salt": context.auth_manager.password_state.as_public_dict()["pwd_salt"],
        "argon2": context.auth_manager.password_state.as_public_dict()["argon2"],
    }
    if include_session_secrets:
        payload["master_secret"] = b64e(session.master_secret)
        payload["resume_secret"] = b64e(session.resume_secret)
    return payload


async def _send_stream_json(websocket: WebSocket, stream: SecretStreamBox, payload: dict[str, Any]) -> None:
    await websocket.send_bytes(stream.encrypt(_json_bytes(payload)))


async def _recv_stream_json(websocket: WebSocket, stream: SecretStreamBox) -> dict[str, Any]:
    frame = await websocket.receive_bytes()
    plaintext = stream.decrypt(frame)
    return json.loads(plaintext.decode("utf-8"))


async def _begin_server_hello(websocket: WebSocket, *, kind: str, channel: str) -> tuple[
    HandshakeContext, JsonChaChaChannel, dict[str, Any]]:
    if not _is_allowed_origin(websocket.headers.get("origin"), websocket.headers.get("host")):
        await websocket.close(code=4403, reason="Origin is not allowed")
        raise AuthenticationError("Origin is not allowed")
    await websocket.accept()
    hello = await websocket.receive_json()
    handshake, response = context.auth_manager.issue_server_hello(hello, kind=kind, channel=channel)
    await websocket.send_json(response)
    secure = context.auth_manager.build_preauth_channel(handshake)
    return handshake, secure, hello


def _decode_control_auth_proof(request: dict[str, Any]) -> bytes:
    proof = request.get("proof")
    if not isinstance(proof, str):
        raise AuthenticationError("Password proof is missing")
    return b64d(proof)


async def _finalize_control_auth(
    websocket: WebSocket,
    *,
    handshake: HandshakeContext,
    preauth_channel: JsonChaChaChannel,
    request: dict[str, Any],
) -> tuple[ActiveSession, JsonChaChaChannel]:
    include_session_secrets = False
    if request.get("type") == "resume_control":
        token = websocket.cookies.get(REMEMBER_COOKIE_NAME, "")
        if token:
            try:
                session, control_channel = context.auth_manager.resume_control_session(handshake, token)
                include_session_secrets = True
            except AuthenticationError:
                session = control_channel = None  # type: ignore[assignment]
            else:
                await websocket.send_json(
                    preauth_channel.encrypt(
                        _auth_ok_payload(session, include_session_secrets=include_session_secrets)
                    )
                )
                return session, control_channel
        await websocket.send_json(preauth_channel.encrypt({"type": "resume_unavailable"}))
        request = preauth_channel.decrypt(await websocket.receive_json())

    if not context.auth_manager.password_state.initialized:
        if request.get("type") != "initialize":
            raise AuthenticationError("Initialization is required")
        password = str(request.get("password", ""))
        context.auth_manager.initialize_password(password)
        session, control_channel = context.auth_manager.open_control_session_after_initialize(handshake)
    else:
        if request.get("type") != "authenticate":
            raise AuthenticationError("Password authentication is required")
        session, control_channel = context.auth_manager.authenticate_control(
            handshake,
            proof=_decode_control_auth_proof(request),
        )
    await websocket.send_json(
        preauth_channel.encrypt(_auth_ok_payload(session, include_session_secrets=include_session_secrets))
    )
    return session, control_channel


async def _control_sender(
    websocket: WebSocket,
    *,
    control_channel: JsonChaChaChannel,
    revoke_queue: asyncio.Queue,
) -> None:
    try:
        while True:
            payload = await revoke_queue.get()
            await websocket.send_json(control_channel.encrypt(payload))
            if payload.get("type") == "auth_revoked":
                await websocket.close(code=4401, reason=payload.get("reason", "revoked"))
                return
    except asyncio.CancelledError:
        pass
    except WebSocketDisconnect:
        pass


async def _control_heartbeat_sender(
    websocket: WebSocket,
    *,
    control_channel: JsonChaChaChannel,
    interval: float,
) -> None:
    try:
        while True:
            await websocket.send_json(
                control_channel.encrypt(
                    {
                        "type": "heartbeat",
                        "timestamp": time.time(),
                    }
                )
            )
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass


@app.post("/auth/remember")
async def remember_auth(request: Request, response: Response, payload: dict[str, Any]) -> Dict[str, Any]:
    try:
        session_id = str(payload.get("session_id", ""))
        proof = b64d(str(payload.get("proof", "")))
        session = context.auth_manager.verify_remember_proof(session_id=session_id, proof=proof)
        token, expires_at = context.auth_manager.issue_remember_token(session)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    max_age = max(0, min(REMEMBER_COOKIE_MAX_AGE, int(expires_at - time.time())))
    response.set_cookie(
        REMEMBER_COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=_cookie_secure(request),
        samesite="lax",
        path="/",
    )
    return {"ok": True, "expires_at": expires_at}


@app.post("/auth/logout")
async def logout_auth(request: Request, response: Response) -> Dict[str, Any]:
    response.delete_cookie(
        REMEMBER_COOKIE_NAME,
        httponly=True,
        secure=_cookie_secure(request),
        samesite="lax",
        path="/",
    )
    return {"ok": True}


@app.get("/health")
async def health() -> Dict[str, Any]:
    statuses = context.runtime.current_status()
    auth_state = context.auth_manager.password_state
    return {
        "ok": True,
        "statuses": statuses,
        "auth": {
            "initialized": auth_state.initialized,
            "pwd_epoch": auth_state.pwd_epoch,
            "server_sign_public_key": context.auth_manager.server_public_key_b64(),
        },
    }


@app.websocket("/ws/control")
async def websocket_control(websocket: WebSocket) -> None:
    revoke_queue = None
    sender_task = heartbeat_task = None
    session: ActiveSession | None = None
    try:
        handshake, preauth_channel, _ = await _begin_server_hello(websocket, kind="control", channel="control")
        request = preauth_channel.decrypt(await websocket.receive_json())
        session, control_channel = await _finalize_control_auth(
            websocket,
            handshake=handshake,
            preauth_channel=preauth_channel,
            request=request,
        )
        revoke_queue = context.auth_manager.subscribe_control(session.session_id)
        sender_task = asyncio.create_task(
            _control_sender(
                websocket,
                control_channel=control_channel,
                revoke_queue=revoke_queue,
            )
        )
        heartbeat_task = asyncio.create_task(
            _control_heartbeat_sender(
                websocket,
                control_channel=control_channel,
                interval=3.0,
            )
        )
        while True:
            message = control_channel.decrypt(await websocket.receive_json())
            msg_type = message.get("type")
            if msg_type == "ping":
                await websocket.send_json(control_channel.encrypt({"type": "pong", "timestamp": time.time()}))
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


async def _perform_business_resume(
    websocket: WebSocket,
    *,
    channel: str,
) -> tuple[ActiveSession, SecretStreamBox]:
    handshake, preauth_channel, hello = await _begin_server_hello(websocket, kind="resume", channel=channel)
    if hello.get("channel") != channel:
        raise AuthenticationError("Requested channel does not match websocket endpoint")
    request = preauth_channel.decrypt(await websocket.receive_json())
    if request.get("type") != "resume_proof":
        raise AuthenticationError("Resume proof is required")
    session, secure_channel, stream_box = context.auth_manager.resume_business_session(
        handshake=handshake,
        session_id=str(hello.get("session_id", "")),
        socket_id=str(hello.get("socket_id", "")),
        channel=channel,
        resume_ticket=str(hello.get("resume_ticket", "")),
        resume_mac=b64d(str(request.get("resume_mac", ""))),
    )
    await websocket.send_json(
        secure_channel.encrypt(
            {
                "type": "resume_ok",
                "session_id": session.session_id,
                "pwd_epoch": session.pwd_epoch,
                "server_header": b64e(stream_box.tx_header),
            }
        )
    )
    ready_back = await websocket.receive_json()
    secure_channel.set_rx_seq(1)
    ready = secure_channel.decrypt(ready_back)
    if ready.get("type") != "stream_ready":
        raise AuthenticationError("Client stream header is required")
    stream_box.init_pull(b64d(str(ready.get("client_header", ""))))
    return session, stream_box


async def _sync_sender(websocket: WebSocket, stream: SecretStreamBox, queue: asyncio.Queue) -> None:
    try:
        while True:
            payload = dict(await queue.get())
            payload.setdefault("direction", "push")
            await _send_stream_json(websocket, stream, payload)  # type: ignore
    except asyncio.CancelledError:
        pass


@app.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket) -> None:
    queue = None
    sender_task = None
    try:
        _, stream = await _perform_business_resume(websocket, channel="sync")
        queue = await context.config_manager.subscribe_updates()
        sender_task = asyncio.create_task(_sync_sender(websocket, stream, queue))
        while True:
            message = await _recv_stream_json(websocket, stream)
            msg_type = message.get("type")
            if msg_type == "pull":
                data = SyncPullMessage(**message)
                snapshot = await context.config_manager.get_snapshot(data.resource, data.resource_id)
                await _send_stream_json(
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
                await _send_stream_json(
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
                await _send_stream_json(
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


async def _provider_sender(websocket: WebSocket, stream: SecretStreamBox, queue: asyncio.Queue,
                           envelope_type: str) -> None:
    try:
        while True:
            payload = await queue.get()
            if envelope_type == "status":
                response = {"type": envelope_type, "status": payload}
            else:
                response = {"type": envelope_type, "entry": payload}
            await _send_stream_json(websocket, stream, response)
    except asyncio.CancelledError:
        pass


@app.websocket("/ws/provider")
async def websocket_provider(websocket: WebSocket) -> None:
    log_queue = status_queue = None
    log_task = status_task = None
    try:
        _, stream = await _perform_business_resume(websocket, channel="provider")
        history = context.log_manager.get_history()
        scopes = context.log_manager.get_scopes()
        await _send_stream_json(websocket, stream, {"type": "logs_full", "scopes": scopes, "entries": history})
        await _send_stream_json(websocket, stream, {"type": "status", "status": context.runtime.current_status()})
        if context.runtime.is_all_data_initialized:
            await _send_stream_json(websocket, stream, {"type": "status", "status": {"is_all_data_initialized": True}})
        log_queue = await context.log_manager.subscribe()
        status_queue = await context.runtime.subscribe_status()
        log_task = asyncio.create_task(_provider_sender(websocket, stream, log_queue, "log"))
        status_task = asyncio.create_task(_provider_sender(websocket, stream, status_queue, "status"))
        while True:
            message = await _recv_stream_json(websocket, stream)
            req_type = message.get("type")
            if req_type == "static_request":
                ProviderRequest(**message)
                snapshot = await context.config_manager.get_static_snapshot()
                await _send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "static_snapshot",
                        "timestamp": snapshot.timestamp,
                        "data": snapshot.data,
                    },
                )
            elif req_type == "status_request":
                await _send_stream_json(websocket, stream,
                                        {"type": "status", "status": context.runtime.current_status()})
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


@app.websocket("/ws/trigger")
async def websocket_trigger(websocket: WebSocket) -> None:
    try:
        _, stream = await _perform_business_resume(websocket, channel="trigger")
        while True:
            message = await _recv_stream_json(websocket, stream)
            cmd = CommandMessage(**message)
            response_payload: Dict[str, Any]
            try:
                if cmd.command == "start_scheduler":
                    if not cmd.config_id:
                        raise ValueError("config_id is required for start_scheduler")
                    result = await context.runtime.start_scheduler(
                        cmd.config_id,
                        set_log=context.ensure_runtime_logger_attached,
                    )
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "stop_scheduler":
                    if not cmd.config_id:
                        raise ValueError("config_id is required for stop_scheduler")
                    result = await context.runtime.stop_scheduler(cmd.config_id)
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "solve":
                    if not cmd.config_id:
                        raise ValueError("config_id is required for solve")
                    task = cmd.payload.get("task")
                    if not task:
                        raise ValueError("task is required for solve command")
                    result = await context.runtime.solve_task(
                        cmd.config_id,
                        task,
                        set_log=context.ensure_runtime_logger_attached,
                    )
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command.startswith("start_"):
                    if not cmd.config_id:
                        raise ValueError(f"config_id is required for command '{cmd.command}'")
                    result = await context.runtime.solve_task(
                        config_id=cmd.config_id,
                        task_name=cmd.command,
                        set_log=context.ensure_runtime_logger_attached,
                    )
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command.startswith("add_config"):
                    name = cmd.payload.get("name")
                    server = cmd.payload.get("server")
                    if not server or not name:
                        raise ValueError("server and name are required for add_config")
                    result = await context.runtime.add_config(name, server)
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command.startswith("remove_config"):
                    config_id = cmd.payload.get("id")
                    if not config_id:
                        raise ValueError("id is required for remove_config")
                    result = await context.runtime.remove_config(config_id)
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "detect_adb":
                    result = await context.runtime.detect_adb()
                    response_payload = {"status": "ok", "data": {"addresses": result}}
                elif cmd.command == "valid_cdk":
                    result = await context.runtime.valid_cdk(cmd.payload["cdk"])
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "test_all_sha":
                    result = await context.runtime.test_all_sha()
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "check_for_update":
                    result = await context.runtime.check_for_update()
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "update_setup_toml":
                    result = await context.runtime.check_for_update()
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "update_to_latest":
                    result = await context.runtime.update_to_latest()
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "control_device":
                    if not cmd.config_id:
                        raise ValueError(f"config_id is required for command '{cmd.command}'")
                    if not cmd.payload.get("operation"):
                        raise ValueError(f"operation is required for command '{cmd.command}'")
                    result = await context.runtime.control_device_(cmd.config_id, cmd.payload.get("operation"))
                    response_payload = {"status": "ok", "data": result}
                elif cmd.command == "status":
                    response_payload = {"status": "ok", "data": context.runtime.current_status()}
                else:
                    raise ValueError(f"Unsupported command '{cmd.command}'")
            except Exception as inner_exc:  # noqa: BLE001 - returned to frontend
                response_payload = {"status": "error", "error": str(inner_exc)}
            await _send_stream_json(
                websocket,
                stream,
                {
                    "type": "command_response",
                    "command": cmd.command,
                    **response_payload,
                    "timestamp": cmd.timestamp,
                },
            )
    except (AuthenticationError, HTTPException) as exc:
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))


@app.websocket("/ws/remote")
async def websocket_remote(websocket: WebSocket) -> None:
    listener = client = None
    sender_task = None
    send_queue: asyncio.Queue[bytes | None] | None = None

    # noinspection PyBroadException
    try:
        _, stream = await _perform_business_resume(websocket, channel="remote")
        message = await _recv_stream_json(websocket, stream)
        config_id = message.get("config_id")
        to_encrypt = message.get("decrypt", True)

        client = await context.runtime.require_remote_(config_id)

        send_queue = asyncio.Queue(maxsize=8)

        async def sender() -> None:
            try:
                while True:
                    item = await send_queue.get()  # type: ignore
                    if item is None:
                        break
                    await websocket.send_bytes(item)
            except WebSocketDisconnect:
                pass

        sender_task = asyncio.create_task(sender())

        client.set_proxy_callbacks(
            ws_to_adb=lambda data: stream.decrypt(data),
            adb_to_ws=lambda data: stream.encrypt(data) if to_encrypt else data,
        )

        if not client.alive:
            await client.init()

        await client.proxy_websocket(websocket)

        while client.alive:
            await asyncio.sleep(1.0)
    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        if sender_task is not None:
            with suppress(Exception):
                assert send_queue is not None
                await send_queue.put(None)
            with suppress(Exception):
                await sender_task
        if client is not None:
            client.remove_listener(EVENT_STREAM, listener)  # type: ignore

            if (not client.any_listener(EVENT_STREAM_ANNEXB) and  # type: ignore
                not client.any_listener(EVENT_STREAM_FMP4)):  # type: ignore
                client.stop()  # type: ignore[union-attr]


@app.websocket("/ws/remote_test")
async def websocket_remote_test(websocket: WebSocket) -> None:
    listener = client = None
    sender_task = None
    send_queue: asyncio.Queue[bytes | None] | None = None

    # noinspection PyBroadException
    try:
        await websocket.accept()
        # frame = await websocket.receive_text()
        # message = json.loads(frame)
        # config_id = message.get("config_id")
        config_id = "default_config"

        client = await context.runtime.require_remote_(config_id)

        # loop = asyncio.get_running_loop()
        send_queue = asyncio.Queue(maxsize=8)

        # async def sender() -> None:
        #     try:
        #         while True:
        #             item = await send_queue.get()  # type: ignore
        #             if item is None:
        #                 break
        #             await websocket.send_bytes(item)
        #     except WebSocketDisconnect:
        #         pass
        #
        # sender_task = asyncio.create_task(sender())

        # def listener(encoded_stream: bytes) -> None:
        #     # noinspection PyBroadException
        #     try:
        #         payload = encoded_stream
        #         # payload = stream.encrypt(encoded_stream)
        #
        #         def _push() -> None:
        #             assert send_queue is not None
        #             if send_queue.full():
        #                 with suppress(asyncio.QueueEmpty):
        #                     send_queue.get_nowait()
        #             with suppress(asyncio.QueueFull):
        #                 send_queue.put_nowait(payload)
        #
        #         loop.call_soon_threadsafe(_push)  # type: ignore
        #     except Exception:
        #         import traceback
        #         traceback.print_exc()
        #
        # client.add_listener(EVENT_STREAM, listener)

        if not client.alive:
            await client.init()

        await client.proxy_websocket(websocket)

        while client.alive:
            await asyncio.sleep(1.0)
    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        if sender_task is not None:
            with suppress(Exception):
                assert send_queue is not None
                await send_queue.put(None)
            with suppress(Exception):
                await sender_task
        if client is not None:
            client.remove_listener(EVENT_STREAM, listener)  # type: ignore

            if (not client.any_listener(EVENT_STREAM_ANNEXB) and  # type: ignore
                not client.any_listener(EVENT_STREAM_FMP4)):  # type: ignore
                client.stop()  # type: ignore[union-attr]
# TODO: Temporarily commented
# app.mount("/", StaticFiles(directory="service/dist", html=True), name="static")
