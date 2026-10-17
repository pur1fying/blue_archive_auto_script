from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

import pytest

from service.auth import manager as auth_manager_module
from service.auth import (
    AuthenticationError,
    DEFAULT_SERVER_SIGN_PUBLIC_KEY_B64,
    DEFAULT_SIGNING_SEED_B64,
    ServiceAuthManager,
    b64d,
    canonical_dumps,
    hmac_sha256,
)


def _workspace_tmp() -> Path:
    root = Path("tests/service/.tmp") / uuid.uuid4().hex
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def test_auth_manager_password_change_revokes_sessions(monkeypatch):
    root = _workspace_tmp()
    monkeypatch.setattr(auth_manager_module, "argon2", lambda password, salt: (password.encode("utf-8") + b"0" * 32)[:32])
    try:
        manager = ServiceAuthManager(root)
        state = manager.initialize_password("secret")
        session = manager._new_session_from_secrets(
            pwd_epoch=state.pwd_epoch,
            master_secret=b"m" * 32,
            resume_secret=b"r" * 32,
        )
        queue = manager.subscribe_control(session.session_id)

        new_state = asyncio.run(manager.change_password(session_id=session.session_id, new_password="new-secret"))

        assert new_state.pwd_epoch == 2
        assert queue.get_nowait()["type"] == "auth_revoked"
        with pytest.raises(AuthenticationError, match="Unknown or revoked"):
            manager.get_session(session.session_id)
    finally:
        _cleanup(root)


def test_signing_key_defaults_to_frontend_pin(monkeypatch):
    root = _workspace_tmp()
    monkeypatch.delenv("BAAS_SERVICE_SIGN_SEED_B64", raising=False)
    try:
        manager = ServiceAuthManager(root)

        assert manager.server_public_key_b64() == DEFAULT_SERVER_SIGN_PUBLIC_KEY_B64
        assert (root / "config" / "service_signing_key.bin").read_bytes() == b64d(DEFAULT_SIGNING_SEED_B64)
    finally:
        _cleanup(root)


def test_stale_signing_key_is_replaced_with_default(monkeypatch):
    root = _workspace_tmp()
    monkeypatch.delenv("BAAS_SERVICE_SIGN_SEED_B64", raising=False)
    try:
        signing_file = root / "config" / "service_signing_key.bin"
        signing_file.parent.mkdir(parents=True, exist_ok=True)
        signing_file.write_bytes(b"x" * 32)

        manager = ServiceAuthManager(root)

        assert manager.server_public_key_b64() == DEFAULT_SERVER_SIGN_PUBLIC_KEY_B64
        assert signing_file.read_bytes() == b64d(DEFAULT_SIGNING_SEED_B64)
    finally:
        _cleanup(root)


def test_remember_proof_and_token_round_trip(monkeypatch):
    root = _workspace_tmp()
    monkeypatch.setattr(auth_manager_module, "argon2", lambda password, salt: (password.encode("utf-8") + b"0" * 32)[:32])
    try:
        manager = ServiceAuthManager(root)
        state = manager.initialize_password("secret")
        session = manager._new_session_from_secrets(
            pwd_epoch=state.pwd_epoch,
            master_secret=b"m" * 32,
            resume_secret=b"r" * 32,
        )
        proof = hmac_sha256(
            session.resume_secret,
            canonical_dumps(
                {
                    "type": "remember_session",
                    "session_id": session.session_id,
                    "pwd_epoch": session.pwd_epoch,
                }
            ),
        )

        verified = manager.verify_remember_proof(session_id=session.session_id, proof=proof)
        token, expires_at = manager.issue_remember_token(verified)

        assert verified.session_id == session.session_id
        assert token.startswith("v1.")
        assert expires_at > verified.created_at
    finally:
        _cleanup(root)
