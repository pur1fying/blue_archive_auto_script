from __future__ import annotations

import asyncio
import hashlib
import secrets
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient

from service.api import security, ws_control
from service.auth import AuthenticationError, JsonChaChaChannel, ServiceAuthManager, b64d, b64e
from service.auth import manager as auth_manager_module
from service.auth.crypto import canonical_dumps, hkdf_sha256, hmac_sha256


def _test_verifier(password, salt):
    return hashlib.sha256(password.encode("utf-8") + salt).digest()


class _ControlClient:
    """Speak the actual encrypted control protocol against the ASGI endpoint."""

    def __init__(self, websocket):
        self.websocket = websocket
        private_key = X25519PrivateKey.generate()
        client_hello = {
            "type": "client_hello",
            "version": 1,
            "client_nonce": b64e(secrets.token_bytes(32)),
            "client_kx_pub": b64e(private_key.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw
            )),
        }
        websocket.send_json(client_hello)
        self.hello = websocket.receive_json()
        hello_core = {
            key: value for key, value in self.hello.items()
            if key not in {"signature", "server_sign_pub"}
        }
        transcript = canonical_dumps({
            "kind": "control", "channel": "control", "client": client_hello, "server": hello_core
        })
        self.transcript_hash = hashlib.sha256(transcript).digest()
        self.shared = private_key.exchange(X25519PublicKey.from_public_bytes(b64d(self.hello["server_kx_pub"])))
        self.preauth = JsonChaChaChannel(
            tx_key=hkdf_sha256(self.shared, b"preauth:server-rx", 32, self.transcript_hash),
            rx_key=hkdf_sha256(self.shared, b"preauth:server-tx", 32, self.transcript_hash),
        )

    def send_preauth(self, payload):
        self.websocket.send_json(self.preauth.encrypt(payload))

    def receive_preauth(self):
        return self.preauth.decrypt(self.websocket.receive_json())

    def authenticate(self, password):
        verifier = _test_verifier(password, b64d(self.hello["pwd_salt"]))
        context = hkdf_sha256(
            self.shared, f"auth-proof:{self.hello['pwd_epoch']}".encode("utf-8"), 32, self.transcript_hash
        )
        self.send_preauth({"type": "authenticate", "proof": b64e(hmac_sha256(verifier, context))})
        payload = self.receive_preauth()
        master_secret = hkdf_sha256(self.shared + verifier, b"master-secret", 32, self.transcript_hash)
        self._open_control(payload, master_secret)
        return payload

    def resume(self):
        self.send_preauth({"type": "resume_control"})
        payload = self.receive_preauth()
        if payload["type"] == "auth_ok":
            self._open_control(payload, b64d(payload["master_secret"]))
        return payload

    def _open_control(self, payload, master_secret):
        assert payload["type"] == "auth_ok"
        self.session_id = payload["session_id"]
        salt = hashlib.sha256(self.session_id.encode("utf-8")).digest()
        self.control = JsonChaChaChannel(
            tx_key=hkdf_sha256(master_secret, b"control:server-rx", 32, salt),
            rx_key=hkdf_sha256(master_secret, b"control:server-tx", 32, salt),
        )

    def send(self, payload):
        self.websocket.send_json(self.control.encrypt(payload))

    def receive(self):
        while True:
            payload = self.control.decrypt(self.websocket.receive_json())
            if payload["type"] != "heartbeat":
                return payload

    def assert_closed(self, code=4401):
        with pytest.raises(WebSocketDisconnect) as exc:
            self.receive()
        assert exc.value.code == code


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_manager_module, "argon2", _test_verifier)
    manager = ServiceAuthManager(tmp_path)
    initial_key = secrets.token_urlsafe(24)
    manager.initialize_password(initial_key)
    context = type("Context", (), {"auth_manager": manager})()
    monkeypatch.setattr(security, "context", context)
    monkeypatch.setattr(ws_control, "context", context)
    app = FastAPI()
    app.include_router(ws_control.router)
    with TestClient(app) as client:
        yield client, manager, initial_key, tmp_path


@pytest.mark.parametrize("request_id", [None, "5edc188a-33b6-4f54-a830-c0481da903c9"])
def test_authenticated_key_change_delivers_ack_before_revocation(service, request_id, caplog):
    client, manager, initial_key, root = service
    new_key = secrets.token_urlsafe(24)
    request = {"type": "change_password", "new_password": new_key}
    if request_id is not None:
        request["request_id"] = request_id
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(initial_key)
        control.send(request)
        if request_id is not None:
            assert control.receive() == {"type": "key_changed", "request_id": request_id, "pwd_epoch": 2}
        assert control.receive() == {"type": "auth_revoked", "reason": "password_changed", "pwd_epoch": 2}
        control.assert_closed()
    assert manager.password_state.pwd_epoch == 2
    assert ServiceAuthManager(root).password_state.pwd_epoch == 2
    assert initial_key not in caplog.text
    assert new_key not in caplog.text
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(new_key)
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        with pytest.raises(WebSocketDisconnect) as exc:
            control.authenticate(initial_key)
        assert exc.value.code == 4401


@pytest.mark.parametrize("cookie", [None, "v1.forged.invalid"])
def test_unauthenticated_key_change_is_rejected_including_forged_cookie(service, cookie):
    client, manager, _, _ = service
    headers = {"cookie": f"baas_remember={cookie}"} if cookie else {}
    with client.websocket_connect("/ws/control", headers=headers) as websocket:
        control = _ControlClient(websocket)
        if cookie:
            assert control.resume() == {"type": "resume_unavailable"}
        control.send_preauth({"type": "change_password", "new_password": secrets.token_urlsafe(24)})
        with pytest.raises(WebSocketDisconnect) as exc:
            control.receive_preauth()
        assert exc.value.code == 4401
    assert manager.password_state.pwd_epoch == 1


@pytest.mark.parametrize("state", ["expired", "stale", "revoked"])
def test_key_change_rechecks_session_after_control_authentication(service, state):
    client, manager, initial_key, _ = service
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(initial_key)
        session = manager.get_session(control.session_id)
        if state == "expired":
            session.expires_at = time.time() - 1
        elif state == "stale":
            session.pwd_epoch = 0
        else:
            manager.close_session(session.session_id)
        control.send({"type": "change_password", "new_password": secrets.token_urlsafe(24), "request_id": "attempt"})
        control.assert_closed()
    assert manager.password_state.pwd_epoch == 1


@pytest.mark.parametrize("field,value", [
    ("new_password", None), ("new_password", 123), ("new_password", {}),
    ("new_password", ""), ("new_password", " \n "),
    ("request_id", 123), ("request_id", {}), ("request_id", ""), ("request_id", "x" * 129),
])
def test_key_change_rejects_invalid_payload_without_changing_state(service, field, value):
    client, manager, initial_key, _ = service
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(initial_key)
        request = {"type": "change_password", "new_password": secrets.token_urlsafe(24), "request_id": "attempt"}
        request[field] = value
        control.send(request)
        control.assert_closed()
    assert manager.password_state.pwd_epoch == 1


def test_key_change_revokes_other_connections_and_remembered_logins(service):
    client, manager, initial_key, _ = service
    with client.websocket_connect("/ws/control") as first_socket, client.websocket_connect("/ws/control") as second_socket:
        first = _ControlClient(first_socket)
        first.authenticate(initial_key)
        second = _ControlClient(second_socket)
        second.authenticate(initial_key)
        token, _ = manager.issue_remember_token(manager.get_session(second.session_id))
        with client.websocket_connect("/ws/control", headers={"cookie": f"baas_remember={token}"}) as remembered_socket:
            remembered = _ControlClient(remembered_socket)
            assert remembered.resume()["type"] == "auth_ok"
            remembered.send({"type": "change_password", "new_password": secrets.token_urlsafe(24), "request_id": "remembered"})
            assert remembered.receive()["type"] == "key_changed"
            assert remembered.receive()["type"] == "auth_revoked"
            remembered.assert_closed()
            assert first.receive()["type"] == "auth_revoked"
            first.assert_closed()
            assert second.receive()["type"] == "auth_revoked"
            second.assert_closed()
        for session_id in (first.session_id, second.session_id, remembered.session_id):
            with pytest.raises(AuthenticationError):
                manager.get_session(session_id)
        with client.websocket_connect("/ws/control", headers={"cookie": f"baas_remember={token}"}) as websocket:
            control = _ControlClient(websocket)
            assert control.resume() == {"type": "resume_unavailable"}
    assert manager.password_state.pwd_epoch == 2


def test_replayed_key_change_frame_cannot_change_key_in_a_new_session(service):
    client, manager, initial_key, _ = service
    new_key = secrets.token_urlsafe(24)
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(initial_key)
        frame = control.control.encrypt({"type": "change_password", "new_password": new_key, "request_id": "original"})
        websocket.send_json(frame)
        assert control.receive()["type"] == "key_changed"
        assert control.receive()["type"] == "auth_revoked"
        control.assert_closed()
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(new_key)
        websocket.send_json(frame)
        control.assert_closed(code=1011)
    assert manager.password_state.pwd_epoch == 2


def test_duplicate_encrypted_control_frame_is_rejected(service):
    client, manager, initial_key, _ = service
    with client.websocket_connect("/ws/control") as websocket:
        control = _ControlClient(websocket)
        control.authenticate(initial_key)
        frame = control.control.encrypt({"type": "ping"})
        websocket.send_json(frame)
        assert control.receive()["type"] == "pong"
        websocket.send_json(frame)
        control.assert_closed()
    assert manager.password_state.pwd_epoch == 1


def test_key_change_finishes_in_flight_heartbeat_before_acknowledging(service, monkeypatch):
    _, manager, _, _ = service

    async def scenario():
        session = manager._new_session_from_secrets(
            pwd_epoch=1, master_secret=secrets.token_bytes(32), resume_secret=secrets.token_bytes(32)
        )
        server_channel = JsonChaChaChannel(tx_key=b"s" * 32, rx_key=b"c" * 32)
        client_channel = JsonChaChaChannel(tx_key=b"c" * 32, rx_key=b"s" * 32)
        request = client_channel.encrypt({
            "type": "change_password", "new_password": secrets.token_urlsafe(24), "request_id": "in-flight"
        })
        heartbeat_started, release_heartbeat, request_received = asyncio.Event(), asyncio.Event(), asyncio.Event()

        class Socket:
            received = 0

            def __init__(self):
                self.frames = []

            async def receive_json(self):
                self.received += 1
                if self.received == 1:
                    return {}
                await heartbeat_started.wait()
                request_received.set()
                return request

            async def send_json(self, frame):
                if frame["seq"] == 0:
                    heartbeat_started.set()
                    await release_heartbeat.wait()
                self.frames.append(frame)

            async def close(self, *, code, reason):
                assert (code, reason) == (4401, "password_changed")

        class Preauth:
            def decrypt(self, frame):
                return frame

        async def begin(*args, **kwargs):
            return None, Preauth(), {}

        async def finalize(*args, **kwargs):
            return session, server_channel

        monkeypatch.setattr(ws_control, "begin_server_hello", begin)
        monkeypatch.setattr(ws_control, "finalize_control_auth", finalize)
        socket = Socket()
        task = asyncio.create_task(ws_control.websocket_control(socket))
        try:
            await asyncio.wait_for(request_received.wait(), timeout=1)
            await asyncio.sleep(0)
            assert manager.password_state.pwd_epoch == 1
        finally:
            release_heartbeat.set()
        await asyncio.wait_for(task, timeout=1)
        assert [client_channel.decrypt(frame)["type"] for frame in socket.frames] == [
            "heartbeat", "key_changed", "auth_revoked"
        ]

    asyncio.run(scenario())
