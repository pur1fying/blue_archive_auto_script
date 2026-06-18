from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey

from .channels import JsonChaChaChannel, SecretStreamBox
from .constants import (
    ARGON2_SALT_BYTES,
    DEFAULT_SERVER_SIGN_PUBLIC_KEY_B64,
    DEFAULT_SIGNING_SEED_B64,
    REMEMBER_TTL_SECONDS,
    SESSION_TTL_SECONDS, PROTOCOL_VERSION,
)
from .crypto import argon2, b64d, b64e, canonical_dumps, hkdf_sha256, hmac_sha256
from .errors import AuthenticationError
from .models import ActiveSession, HandshakeContext, PasswordState, RememberedLogin


class ServiceAuthManager:
    """Persists the system password verifier and manages authenticated sessions."""

    def __init__(self, project_root: Path) -> None:
        self._config_dir = project_root / "config"
        self._config_dir.mkdir(exist_ok=True)
        self._state_file = self._config_dir / "service_auth.json"
        self._ticket_file = self._config_dir / "service_ticket.key"
        self._remembered_file = self._config_dir / "service_remembered_logins.json"
        self._signing_file = self._config_dir / "service_signing_key.bin"
        self._lock = threading.RLock()
        self._sessions: dict[str, ActiveSession] = {}
        self._remembered_logins: dict[str, RememberedLogin] = {}

        self._password_state = self._load_password_state()
        self._signing_key = self._load_signing_key()
        self._verify_default_public_key()
        self._ticket_key = self._load_or_create_key(
            self._ticket_file,
            env_name="BAAS_SERVICE_TICKET_KEY_B64",
            default_factory=lambda: secrets.token_bytes(32),
        )
        self._remembered_logins = self._load_remembered_logins()

    @property
    def password_state(self) -> PasswordState:
        return self._password_state

    def server_public_key_b64(self) -> str:
        public_key = self._signing_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        return b64e(public_key)

    def issue_server_hello(self, hello: dict[str, Any], *, kind: str, channel: str) -> tuple[HandshakeContext, dict[str, Any]]:
        if hello.get("type") != "client_hello":
            raise AuthenticationError("Expected client_hello")
        if int(hello.get("version", 0)) != PROTOCOL_VERSION:
            raise AuthenticationError("Unsupported protocol version")

        try:
            client_nonce = b64d(hello["client_nonce"])
            client_public_bytes = b64d(hello["client_kx_pub"])
        except Exception as exc:  # noqa: BLE001 - normalized below
            raise AuthenticationError("Malformed client hello") from exc

        server_private = X25519PrivateKey.generate()
        server_public_bytes = server_private.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        public_state = self._password_state.as_public_dict()
        hello_core = {
            "type": "server_hello",
            "kind": kind,
            "channel": channel,
            "version": PROTOCOL_VERSION,
            "server_nonce": b64e(secrets.token_bytes(32)),
            "server_kx_pub": b64e(server_public_bytes),
            **public_state,
        }
        transcript = canonical_dumps(
            {
                "kind": kind,
                "channel": channel,
                "client": hello,
                "server": hello_core,
            }
        )
        signature = self._signing_key.sign(transcript)
        response = {
            **hello_core,
            "signature": b64e(signature),
            "server_sign_pub": self.server_public_key_b64(),
        }
        client_public = X25519PublicKey.from_public_bytes(client_public_bytes)
        shared = server_private.exchange(client_public)
        transcript_hash = hashlib.sha256(transcript).digest()
        preauth_server_tx = hkdf_sha256(shared, b"preauth:server-tx", 32, transcript_hash)
        preauth_server_rx = hkdf_sha256(shared, b"preauth:server-rx", 32, transcript_hash)
        context = HandshakeContext(
            kind=kind,
            channel=channel,
            client_nonce=client_nonce,
            server_nonce=b64d(str(hello_core["server_nonce"])),
            client_public_key=client_public_bytes,
            server_private_key=server_private,
            server_public_key=server_public_bytes,
            transcript=transcript,
            transcript_hash=transcript_hash,
            shared_key=shared,
            preauth_server_tx=preauth_server_tx,
            preauth_server_rx=preauth_server_rx,
        )
        return context, response

    def build_preauth_channel(self, handshake: HandshakeContext) -> JsonChaChaChannel:
        return JsonChaChaChannel(
            tx_key=handshake.preauth_server_tx,
            rx_key=handshake.preauth_server_rx,
        )

    def initialize_password(self, password: str) -> PasswordState:
        if not password.strip():
            raise AuthenticationError("Password is required")
        with self._lock:
            if self._password_state.initialized:
                raise AuthenticationError("Service is already initialized")
            self._password_state = self._password_state_for(password=password, epoch=1)
            self._save_password_state()
            return self._password_state

    def authenticate_control(self, handshake: HandshakeContext, proof: bytes) -> tuple[ActiveSession, JsonChaChaChannel]:
        password_state = self._password_state
        if not password_state.initialized or password_state.pwd_hash is None:
            raise AuthenticationError("Service password is not initialized")
        expected = hmac_sha256(password_state.pwd_hash, self._auth_context(handshake, password_state.pwd_epoch))
        if not hmac.compare_digest(expected, proof):
            raise AuthenticationError("Password proof verification failed")
        session = self._new_session(handshake, password_state)
        control_channel = self._build_control_channel(session)
        return session, control_channel

    def open_control_session_after_initialize(self, handshake: HandshakeContext) -> tuple[ActiveSession, JsonChaChaChannel]:
        password_state = self._password_state
        if not password_state.initialized:
            raise AuthenticationError("Service password is not initialized")
        session = self._new_session(handshake, password_state)
        return session, self._build_control_channel(session)

    def derive_password_proof_context(self, handshake: HandshakeContext, pwd_epoch: int) -> bytes:
        return self._auth_context(handshake, pwd_epoch)

    def issue_resume_ticket(self, session: ActiveSession) -> str:
        body = {
            "session_id": session.session_id,
            "pwd_epoch": session.pwd_epoch,
            "expires_at": session.expires_at,
        }
        payload = canonical_dumps(body)
        signature = hmac_sha256(self._ticket_key, payload)
        return f"{b64e(payload)}.{b64e(signature)}"

    def verify_remember_proof(self, *, session_id: str, proof: bytes) -> ActiveSession:
        session = self.get_session(session_id)
        expected = hmac_sha256(
            session.resume_secret,
            canonical_dumps(
                {
                    "type": "remember_session",
                    "session_id": session.session_id,
                    "pwd_epoch": session.pwd_epoch,
                }
            ),
        )
        if not hmac.compare_digest(expected, proof):
            raise AuthenticationError("Remember-session proof verification failed")
        return session

    def issue_remember_token(self, session: ActiveSession) -> tuple[str, float]:
        token_id = uuid.uuid4().hex
        token_secret = secrets.token_bytes(32)
        now = time.time()
        expires_at = now + REMEMBER_TTL_SECONDS
        remembered = RememberedLogin(
            token_id=token_id,
            token_hash=self._remember_token_hash(token_id, token_secret),
            created_at=now,
            expires_at=expires_at,
            pwd_epoch=session.pwd_epoch,
        )
        with self._lock:
            self._prune_expired_remembered_locked(now)
            self._remembered_logins[token_id] = remembered
            self._save_remembered_logins()
        return f"v1.{token_id}.{b64e(token_secret)}", expires_at

    def resume_control_session(self, handshake: HandshakeContext, remember_token: str) -> tuple[ActiveSession, JsonChaChaChannel]:
        remembered = self._verify_remember_token(remember_token)
        if remembered.pwd_epoch != self._password_state.pwd_epoch:
            raise AuthenticationError("Remembered login epoch is stale")
        master_secret = secrets.token_bytes(32)
        resume_secret = hkdf_sha256(master_secret, b"resume-secret", 32, handshake.transcript_hash)
        session = self._new_session_from_secrets(
            pwd_epoch=remembered.pwd_epoch,
            master_secret=master_secret,
            resume_secret=resume_secret,
        )
        return session, self._build_control_channel(session)

    def subscribe_control(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        with self._lock:
            session = self._require_session(session_id)
            session.control_queues.add(queue)
        return queue

    def unsubscribe_control(self, session_id: str, queue: asyncio.Queue) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session.control_queues.discard(queue)

    async def change_password(self, *, session_id: str, new_password: str, reason: str = "password_changed") -> PasswordState:
        if not new_password.strip():
            raise AuthenticationError("New password is required")
        with self._lock:
            session = self._require_session(session_id)
            next_epoch = session.pwd_epoch + 1
            self._password_state = self._password_state_for(password=new_password, epoch=next_epoch)
            self._save_password_state()
            self._remembered_logins.clear()
            self._save_remembered_logins()
            queues = self._collect_revocation_queues(reason=reason, pwd_epoch=next_epoch)
        await self._publish_queues(queues)
        return self._password_state

    async def force_reset_password(self, new_password: str, *, reason: str = "password_reset") -> PasswordState:
        if not new_password.strip():
            raise AuthenticationError("New password is required")
        with self._lock:
            next_epoch = max(self._password_state.pwd_epoch, 0) + 1
            self._password_state = self._password_state_for(password=new_password, epoch=next_epoch)
            self._save_password_state()
            self._remembered_logins.clear()
            self._save_remembered_logins()
            queues = self._collect_revocation_queues(reason=reason, pwd_epoch=next_epoch)
        await self._publish_queues(queues)
        return self._password_state

    def resume_business_session(
        self,
        *,
        handshake: HandshakeContext,
        session_id: str,
        socket_id: str,
        channel: str,
        resume_ticket: str,
        resume_mac: bytes,
    ) -> tuple[ActiveSession, JsonChaChaChannel, SecretStreamBox]:
        session = self._verify_resume_ticket(session_id, resume_ticket)
        if session.pwd_epoch != self._password_state.pwd_epoch:
            raise AuthenticationError("Session epoch is no longer current")
        expected = hmac_sha256(
            session.resume_secret,
            canonical_dumps(
                {
                    "transcript_hash": b64e(handshake.transcript_hash),
                    "session_id": session_id,
                    "socket_id": socket_id,
                    "channel": channel,
                    "pwd_epoch": session.pwd_epoch,
                }
            ),
        )
        if not hmac.compare_digest(expected, resume_mac):
            raise AuthenticationError("Resume proof verification failed")

        secure_channel = self.build_preauth_channel(handshake)
        tx_key, rx_key = self.derive_business_stream_keys(
            session=session,
            socket_id=socket_id,
            channel=channel,
            transcript_hash=handshake.transcript_hash,
        )
        stream_box = SecretStreamBox(
            tx_key=tx_key,
            rx_key=rx_key,
            aad_prefix=canonical_dumps(
                {
                    "session_id": session_id,
                    "socket_id": socket_id,
                    "channel": channel,
                    "pwd_epoch": session.pwd_epoch,
                }
            ),
        )
        return session, secure_channel, stream_box

    def derive_business_stream_keys(
        self,
        *,
        session: ActiveSession,
        socket_id: str,
        channel: str,
        transcript_hash: bytes,
    ) -> tuple[bytes, bytes]:
        base = hkdf_sha256(
            session.master_secret,
            canonical_dumps(
                {
                    "scope": "ws",
                    "session_id": session.session_id,
                    "socket_id": socket_id,
                    "channel": channel,
                    "pwd_epoch": session.pwd_epoch,
                }
            ),
            64,
            transcript_hash,
        )
        server_tx = hkdf_sha256(base[:32], b"secretstream:server-tx", 32, transcript_hash)
        server_rx = hkdf_sha256(base[32:], b"secretstream:server-rx", 32, transcript_hash)
        return server_tx, server_rx

    def close_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def _new_session(self, handshake: HandshakeContext, password_state: PasswordState) -> ActiveSession:
        if not isinstance(password_state.pwd_hash, bytes):
            raise AuthenticationError("Password hash is not bytes")
        master_secret = hkdf_sha256(
            handshake.shared_key + password_state.pwd_hash,
            b"master-secret",
            32,
            handshake.transcript_hash,
        )
        resume_secret = hkdf_sha256(master_secret, b"resume-secret", 32, handshake.transcript_hash)
        return self._new_session_from_secrets(
            pwd_epoch=password_state.pwd_epoch,
            master_secret=master_secret,
            resume_secret=resume_secret,
        )

    def _new_session_from_secrets(self, *, pwd_epoch: int, master_secret: bytes, resume_secret: bytes) -> ActiveSession:
        now = time.time()
        session = ActiveSession(
            session_id=uuid.uuid4().hex,
            created_at=now,
            expires_at=now + SESSION_TTL_SECONDS,
            pwd_epoch=pwd_epoch,
            master_secret=master_secret,
            resume_secret=resume_secret,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    @staticmethod
    def _build_control_channel(session: ActiveSession) -> JsonChaChaChannel:
        transcript_salt = hashlib.sha256(session.session_id.encode("utf-8")).digest()
        return JsonChaChaChannel(
            tx_key=hkdf_sha256(session.master_secret, b"control:server-tx", 32, transcript_salt),
            rx_key=hkdf_sha256(session.master_secret, b"control:server-rx", 32, transcript_salt),
        )

    def build_control_channel_for_session(self, session: ActiveSession) -> JsonChaChaChannel:
        return self._build_control_channel(session)

    def get_session(self, session_id: str) -> ActiveSession:
        with self._lock:
            return self._require_session(session_id)

    def _verify_resume_ticket(self, session_id: str, token: str) -> ActiveSession:
        try:
            payload_b64, signature_b64 = token.split(".", 1)
            payload = b64d(payload_b64)
            signature = b64d(signature_b64)
        except ValueError as exc:
            raise AuthenticationError("Malformed resume ticket") from exc
        expected_signature = hmac_sha256(self._ticket_key, payload)
        if not hmac.compare_digest(expected_signature, signature):
            raise AuthenticationError("Resume ticket signature mismatch")
        body = json.loads(payload.decode("utf-8"))
        if body.get("session_id") != session_id:
            raise AuthenticationError("Resume ticket session mismatch")
        with self._lock:
            session = self._require_session(session_id)
        if session.expires_at < time.time():
            raise AuthenticationError("Session has expired")
        if int(body.get("pwd_epoch", -1)) != session.pwd_epoch:
            raise AuthenticationError("Resume ticket epoch mismatch")
        return session

    def _verify_remember_token(self, token: str) -> RememberedLogin:
        try:
            version, token_id, secret_b64 = token.split(".", 2)
            token_secret = b64d(secret_b64)
        except Exception as exc:  # noqa: BLE001 - normalized below
            raise AuthenticationError("Malformed remember token") from exc
        if version != "v1" or not token_id:
            raise AuthenticationError("Unsupported remember token")
        now = time.time()
        with self._lock:
            self._prune_expired_remembered_locked(now)
            remembered = self._remembered_logins.get(token_id)
            if remembered is None:
                raise AuthenticationError("Unknown remembered login")
            expected = self._remember_token_hash(token_id, token_secret)
            if not hmac.compare_digest(expected, remembered.token_hash):
                raise AuthenticationError("Remember token verification failed")
            if remembered.expires_at < now:
                self._remembered_logins.pop(token_id, None)
                self._save_remembered_logins()
                raise AuthenticationError("Remembered login has expired")
            if remembered.pwd_epoch != self._password_state.pwd_epoch:
                raise AuthenticationError("Remembered login epoch mismatch")
            return remembered

    def _remember_token_hash(self, token_id: str, token_secret: bytes) -> bytes:
        return hmac_sha256(
            self._ticket_key,
            b"remember-token:" + token_id.encode("utf-8") + b":" + token_secret,
        )

    def _prune_expired_remembered_locked(self, now: Optional[float] = None) -> None:
        current = time.time() if now is None else now
        expired = [
            token_id
            for token_id, remembered in self._remembered_logins.items()
            if remembered.expires_at < current
        ]
        if not expired:
            return
        for token_id in expired:
            self._remembered_logins.pop(token_id, None)
        self._save_remembered_logins()

    @staticmethod
    def _auth_context(handshake: HandshakeContext, pwd_epoch: int) -> bytes:
        return hkdf_sha256(
            handshake.shared_key,
            f"auth-proof:{pwd_epoch}".encode("utf-8"),
            32,
            handshake.transcript_hash,
        )

    @staticmethod
    def _password_state_for(*, password: str, epoch: int) -> PasswordState:
        salt = secrets.token_bytes(ARGON2_SALT_BYTES)
        verifier = argon2(password, salt)
        return PasswordState(
            initialized=True,
            pwd_epoch=epoch,
            pwd_salt=salt,
            pwd_hash=verifier,
        )

    def _collect_revocation_queues(self, *, reason: str, pwd_epoch: int) -> list[tuple[asyncio.Queue, dict[str, Any]]]:
        queues: list[tuple[asyncio.Queue, dict[str, Any]]] = []
        for session in self._sessions.values():
            for queue in session.control_queues:
                queues.append(
                    (
                        queue,
                        {
                            "type": "auth_revoked",
                            "reason": reason,
                            "pwd_epoch": pwd_epoch,
                        },
                    )
                )
        self._sessions.clear()
        return queues

    @staticmethod
    async def _publish_queues(queues: list[tuple[asyncio.Queue, dict[str, Any]]]) -> None:
        for queue, payload in queues:
            await queue.put(payload)

    def _require_session(self, session_id: str) -> ActiveSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise AuthenticationError("Unknown or revoked session")
        if session.expires_at < time.time():
            self._sessions.pop(session_id, None)
            raise AuthenticationError("Session has expired")
        if session.pwd_epoch != self._password_state.pwd_epoch:
            self._sessions.pop(session_id, None)
            raise AuthenticationError("Session epoch is stale")
        return session

    def _load_password_state(self) -> PasswordState:
        if not self._state_file.exists():
            return PasswordState()
        payload = json.loads(self._state_file.read_text(encoding="utf-8"))
        return PasswordState(
            initialized=bool(payload.get("initialized", False)),
            pwd_epoch=int(payload.get("pwd_epoch", 0)),
            pwd_salt=b64d(payload["pwd_salt"]) if payload.get("pwd_salt") else None,
            pwd_hash=b64d(payload["pwd_hash"]) if payload.get("pwd_hash") else None,
        )

    def _save_password_state(self) -> None:
        payload = {
            "initialized": self._password_state.initialized,
            "pwd_epoch": self._password_state.pwd_epoch,
            "pwd_salt": b64e(self._password_state.pwd_salt) if self._password_state.pwd_salt else None,
            "pwd_hash": b64e(self._password_state.pwd_hash) if self._password_state.pwd_hash else None,
        }
        self._state_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_remembered_logins(self) -> dict[str, RememberedLogin]:
        if not self._remembered_file.exists():
            return {}
        payload = json.loads(self._remembered_file.read_text(encoding="utf-8"))
        remembered: dict[str, RememberedLogin] = {}
        for item in payload.get("logins", []):
            token_id = str(item.get("token_id", ""))
            if not token_id:
                continue
            remembered[token_id] = RememberedLogin(
                token_id=token_id,
                token_hash=b64d(item["token_hash"]),
                created_at=float(item.get("created_at", 0)),
                expires_at=float(item.get("expires_at", 0)),
                pwd_epoch=int(item.get("pwd_epoch", 0)),
            )
        return remembered

    def _save_remembered_logins(self) -> None:
        payload = {
            "logins": [
                {
                    "token_id": remembered.token_id,
                    "token_hash": b64e(remembered.token_hash),
                    "created_at": remembered.created_at,
                    "expires_at": remembered.expires_at,
                    "pwd_epoch": remembered.pwd_epoch,
                }
                for remembered in self._remembered_logins.values()
            ]
        }
        self._remembered_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_signing_key(self) -> Ed25519PrivateKey:
        env_seed = os.getenv("BAAS_SERVICE_SIGN_SEED_B64")
        if env_seed:
            return Ed25519PrivateKey.from_private_bytes(b64d(env_seed))
        if self._signing_file.exists():
            return Ed25519PrivateKey.from_private_bytes(self._signing_file.read_bytes())
        seed = b64d(DEFAULT_SIGNING_SEED_B64)
        self._signing_file.write_bytes(seed)
        return Ed25519PrivateKey.from_private_bytes(seed)

    def _verify_default_public_key(self) -> None:
        public_key = self._signing_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        if (
            not os.getenv("BAAS_SERVICE_SIGN_SEED_B64")
            and b64e(public_key) != DEFAULT_SERVER_SIGN_PUBLIC_KEY_B64
        ):
            raise RuntimeError(
                "Configured service signing key does not match the pinned frontend fallback public key. "
                "Provide a matching VITE_BAAS_SERVER_SIGN_PUBLIC_KEY_B64 when building the frontend."
            )

    @staticmethod
    def _load_or_create_key(path: Path, *, env_name: str, default_factory) -> bytes:
        env_value = os.getenv(env_name)
        if env_value:
            return b64d(env_value)
        if path.exists():
            return path.read_bytes()
        key = default_factory()
        path.write_bytes(key)
        return key


def verify_server_signature(
    *,
    expected_public_key_b64: str,
    transcript: bytes,
    signature_b64: str,
) -> None:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(b64d(expected_public_key_b64))
        public_key.verify(b64d(signature_b64), transcript)
    except InvalidSignature as exc:
        raise AuthenticationError("Server signature verification failed") from exc
