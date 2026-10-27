from __future__ import annotations

import secrets
import time
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient

from service.api import http, security, ws_control
from service.auth import AuthenticationError, ServiceAuthManager, b64e


class _PasswordState:
    initialized = True
    pwd_epoch = 7


class _AuthManager:
    password_state = _PasswordState()

    def __init__(self) -> None:
        self.fail_remember = False

    def server_public_key_b64(self) -> str:
        return "server-key"

    def verify_remember_proof(self, *, session_id: str, proof: bytes):
        if self.fail_remember:
            raise AuthenticationError("bad proof")
        assert session_id == "session-1"
        assert proof == b"proof"
        return SimpleNamespace(session_id=session_id)

    def issue_remember_token(self, session) -> tuple[str, float]:
        assert session.session_id == "session-1"
        return "remember-token", time.time() + 120


class _Runtime:
    def current_status(self):
        return {"default_config": {"running": False}}


def _client(monkeypatch, auth_manager: _AuthManager) -> TestClient:
    fake_context = SimpleNamespace(auth_manager=auth_manager, runtime=_Runtime())
    monkeypatch.setattr(http, "context", fake_context)
    app = FastAPI()
    app.include_router(http.router)
    return TestClient(app)


def test_health_contract(monkeypatch):
    client = _client(monkeypatch, _AuthManager())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["statuses"] == {"default_config": {"running": False}}
    assert payload["auth"] == {
        "initialized": True,
        "pwd_epoch": 7,
        "server_sign_public_key": "server-key",
        "key_reset_supported": True,
    }


def test_public_key_reset_capability_does_not_authorize_key_changes(monkeypatch, tmp_path):
    manager = ServiceAuthManager(tmp_path)
    manager.initialize_password(secrets.token_urlsafe(24))
    state = manager.password_state
    context = SimpleNamespace(auth_manager=manager, runtime=_Runtime())
    for module in (http, security, ws_control):
        monkeypatch.setattr(module, "context", context)
    app = FastAPI()
    app.include_router(http.router)
    app.include_router(ws_control.router)
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["auth"]["key_reset_supported"] is True
        assert "set-cookie" not in response.headers
        payload = {"type": "change_password", "new_password": secrets.token_urlsafe(24)}
        assert client.post("/health", json=payload).status_code == 405
        with client.websocket_connect("/ws/control") as websocket:
            websocket.send_json(payload)
            with pytest.raises(WebSocketDisconnect) as exc:
                websocket.receive_json()
            assert exc.value.code == 4401
    assert manager.password_state is state
    assert manager.password_state.pwd_epoch == 1


def test_remember_auth_sets_cookie(monkeypatch):
    client = _client(monkeypatch, _AuthManager())

    response = client.post("/auth/remember", json={"session_id": "session-1", "proof": b64e(b"proof")})

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "baas_remember=remember-token" in response.headers["set-cookie"]


def test_remember_auth_failure_returns_401(monkeypatch):
    auth_manager = _AuthManager()
    auth_manager.fail_remember = True
    client = _client(monkeypatch, auth_manager)

    response = client.post("/auth/remember", json={"session_id": "session-1", "proof": b64e(b"proof")})

    assert response.status_code == 401
    assert response.json()["detail"] == "bad proof"


def test_logout_deletes_cookie(monkeypatch):
    client = _client(monkeypatch, _AuthManager())

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "baas_remember=" in response.headers["set-cookie"]
