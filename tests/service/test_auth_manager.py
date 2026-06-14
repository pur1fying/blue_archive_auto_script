from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

import pytest

from service.auth import manager as auth_manager_module
from service.auth import AuthenticationError, ServiceAuthManager, canonical_dumps, hmac_sha256


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
