from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from service.api import security
from service.auth import AuthenticationError, JsonChaChaChannel, b64e


class _PasswordState:
    initialized = False
    pwd_epoch = 1

    def as_public_dict(self):
        return {"pwd_salt": "salt", "argon2": {"time_cost": 1}}


class _AuthManager:
    def __init__(self) -> None:
        self.password_state = _PasswordState()
        self.initialized_password = None

    def issue_resume_ticket(self, session):
        return f"ticket:{session.session_id}"

    def initialize_password(self, password: str):
        self.initialized_password = password
        self.password_state.initialized = True

    def open_control_session_after_initialize(self, handshake):
        return (
            SimpleNamespace(
                session_id="session-1",
                expires_at=123.0,
                pwd_epoch=1,
                master_secret=b"master",
                resume_secret=b"resume",
            ),
            SimpleNamespace(name="control-channel"),
        )


class _PreauthChannel:
    def __init__(self, decrypted=None) -> None:
        self._decrypted = decrypted or {}

    def encrypt(self, payload):
        return {"encrypted": payload}

    def decrypt(self, payload):
        return self._decrypted if payload == "next" else payload


class _WebSocket:
    def __init__(self) -> None:
        self.cookies = {}
        self.sent_json = []
        self.received_json = []

    async def send_json(self, payload):
        self.sent_json.append(payload)

    async def receive_json(self):
        return self.received_json.pop(0)


class _Stream:
    def encrypt(self, data: bytes) -> bytes:
        return b"enc:" + data

    def decrypt(self, data: bytes) -> bytes:
        return data.removeprefix(b"enc:")


class _StreamWebSocket:
    def __init__(self, inbound: bytes) -> None:
        self.inbound = inbound
        self.sent = []

    async def send_bytes(self, payload: bytes) -> None:
        self.sent.append(payload)

    async def receive_bytes(self) -> bytes:
        return self.inbound


def test_origin_policy_allows_local_and_same_host(monkeypatch):
    assert security.is_allowed_origin(None, "example.com") is True
    assert security.is_allowed_origin("http://localhost:3000", "example.com") is True
    assert security.is_allowed_origin("http://192.168.1.10:5173", "192.168.1.10:8190") is True
    assert security.is_allowed_origin("http://evil.example", "service.example") is False

    monkeypatch.setenv("BAAS_SERVICE_ALLOWED_ORIGINS", "https://allowed.example")
    assert security.is_allowed_origin("https://allowed.example", "service.example") is True


def test_stream_json_uses_binary_frames():
    websocket = _StreamWebSocket(b'enc:{"type":"ping"}')
    stream = _Stream()

    asyncio.run(security.send_stream_json(websocket, stream, {"type": "pong"}))
    payload = asyncio.run(security.recv_stream_json(websocket, stream))

    assert websocket.sent == [b'enc:{"type":"pong"}']
    assert payload == {"type": "ping"}


def test_json_chacha_channel_round_trip():
    server_tx = b"1" * 32
    client_tx = b"2" * 32
    server = JsonChaChaChannel(tx_key=server_tx, rx_key=client_tx)
    client = JsonChaChaChannel(tx_key=client_tx, rx_key=server_tx)

    frame = server.encrypt({"type": "hello"})

    assert client.decrypt(frame) == {"type": "hello"}


def test_finalize_control_auth_initialize_envelope(monkeypatch):
    auth_manager = _AuthManager()
    monkeypatch.setattr(security, "context", SimpleNamespace(auth_manager=auth_manager))
    websocket = _WebSocket()

    session, channel = asyncio.run(
        security.finalize_control_auth(
            websocket,
            handshake=SimpleNamespace(),
            preauth_channel=_PreauthChannel(),
            request={"type": "initialize", "password": "secret"},
        )
    )

    assert auth_manager.initialized_password == "secret"
    assert session.session_id == "session-1"
    assert channel.name == "control-channel"
    assert websocket.sent_json[0]["encrypted"]["type"] == "auth_ok"
    assert websocket.sent_json[0]["encrypted"]["resume_ticket"] == "ticket:session-1"


def test_business_resume_rejects_channel_mismatch(monkeypatch):
    async def fake_begin_server_hello(websocket, *, kind, channel):
        return SimpleNamespace(), _PreauthChannel(), {"channel": "provider"}

    monkeypatch.setattr(security, "begin_server_hello", fake_begin_server_hello)

    with pytest.raises(AuthenticationError, match="Requested channel"):
        asyncio.run(security.perform_business_resume(_WebSocket(), channel="sync"))


def test_business_resume_requires_resume_proof(monkeypatch):
    async def fake_begin_server_hello(websocket, *, kind, channel):
        ws = websocket
        ws.received_json.append({"type": "not_resume_proof"})
        return SimpleNamespace(), _PreauthChannel(), {"channel": "sync"}

    monkeypatch.setattr(security, "begin_server_hello", fake_begin_server_hello)

    with pytest.raises(AuthenticationError, match="Resume proof"):
        asyncio.run(security.perform_business_resume(_WebSocket(), channel="sync"))
