from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Optional
from urllib.parse import urlparse

from fastapi import Request, WebSocket, WebSocketDisconnect

from service.auth import (
    ActiveSession,
    AuthenticationError,
    HandshakeContext,
    JsonChaChaChannel,
    PROTOCOL_VERSION,
    SecretStreamBox,
    b64d,
    b64e,
)

from .state import REMEMBER_COOKIE_NAME, context


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def is_allowed_origin(origin: Optional[str], host: Optional[str]) -> bool:
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


def cookie_secure(request: Request) -> bool:
    forced = os.getenv("BAAS_REMEMBER_COOKIE_SECURE")
    if forced is not None:
        return forced.lower() in {"1", "true", "yes", "on"}
    return request.url.scheme == "https"


def auth_ok_payload(session: ActiveSession, *, include_session_secrets: bool = False) -> dict:
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


async def send_stream_json(websocket: WebSocket, stream: SecretStreamBox, payload: dict) -> None:
    await websocket.send_bytes(stream.encrypt(json_bytes(payload)))


async def send_stream_bytes(websocket: WebSocket, stream: SecretStreamBox, payload: bytes) -> None:
    await websocket.send_bytes(stream.encrypt(payload))


async def recv_stream_json(websocket: WebSocket, stream: SecretStreamBox) -> dict:
    frame = await websocket.receive_bytes()
    plaintext = stream.decrypt(frame)
    return json.loads(plaintext.decode("utf-8"))


async def recv_stream_bytes(websocket: WebSocket, stream: SecretStreamBox) -> bytes:
    frame = await websocket.receive_bytes()
    return stream.decrypt(frame)


async def begin_server_hello(
    websocket: WebSocket,
    *,
    kind: str,
    channel: str,
) -> tuple[HandshakeContext, JsonChaChaChannel, dict]:
    if not is_allowed_origin(websocket.headers.get("origin"), websocket.headers.get("host")):
        await websocket.close(code=4403, reason="Origin is not allowed")
        raise AuthenticationError("Origin is not allowed")
    await websocket.accept()
    hello = await websocket.receive_json()
    handshake, response = context.auth_manager.issue_server_hello(hello, kind=kind, channel=channel)
    await websocket.send_json(response)
    secure = context.auth_manager.build_preauth_channel(handshake)
    return handshake, secure, hello


def decode_control_auth_proof(request: dict) -> bytes:
    proof = request.get("proof")
    if not isinstance(proof, str):
        raise AuthenticationError("Password proof is missing")
    return b64d(proof)


async def finalize_control_auth(
    websocket: WebSocket,
    *,
    handshake: HandshakeContext,
    preauth_channel: JsonChaChaChannel,
    request: dict,
) -> tuple[ActiveSession, JsonChaChaChannel]:
    include_session_secrets = False
    if request.get("type") == "resume_control":
        token = websocket.cookies.get(REMEMBER_COOKIE_NAME, "")
        if token:
            try:
                session, control_channel = context.auth_manager.resume_control_session(handshake, token)
                include_session_secrets = True
            except AuthenticationError:
                # noinspection PyUnusedLocal
                session = control_channel = None  # type: ignore[assignment]
            else:
                await websocket.send_json(
                    preauth_channel.encrypt(
                        auth_ok_payload(session, include_session_secrets=include_session_secrets)
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
            proof=decode_control_auth_proof(request),
        )
    await websocket.send_json(
        preauth_channel.encrypt(auth_ok_payload(session, include_session_secrets=include_session_secrets))
    )
    return session, control_channel


async def control_sender(
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


async def control_heartbeat_sender(
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


async def perform_business_resume(
    websocket: WebSocket,
    *,
    channel: str,
) -> tuple[ActiveSession, SecretStreamBox]:
    handshake, preauth_channel, hello = await begin_server_hello(websocket, kind="resume", channel=channel)
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
