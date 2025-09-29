from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from typing import Any, Union

from cryptography.fernet import Fernet, InvalidToken


class AuthenticationError(Exception):
    """Raised when the websocket handshake fails."""


@dataclass
class HandshakeChallenge:
    challenge: str
    algorithm: str = "HMAC-SHA256"

@dataclass
class HandshakeResponse:
    response: str

class HandshakeSession:
    """One-time handshake helper coordinating challenge/response."""

    def __init__(self, shared_secret: str) -> None:
        if not shared_secret:
            raise AuthenticationError("Shared secret is not configured")
        self._shared_secret = shared_secret.encode("utf-8")
        self._challenge_bytes: Union[bytes, None] = None

    def issue_challenge(self) -> HandshakeChallenge:
        self._challenge_bytes = secrets.token_bytes(32)
        challenge = base64.urlsafe_b64encode(self._challenge_bytes).decode("ascii")
        return HandshakeChallenge(challenge=challenge)

    def verify(self, response: str) -> None:
        if self._challenge_bytes is None:
            raise AuthenticationError("Handshake challenge was not issued")
        expected = hmac.new(self._shared_secret, self._challenge_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, response):
            raise AuthenticationError("Invalid handshake response")

    def build_cipher(self) -> "CipherBox":
        return CipherBox(self._shared_secret.decode("utf-8"))


class CipherBox:
    """Symmetric encryption box backed by Fernet."""

    def __init__(self, shared_secret: str) -> None:
        digest = hashlib.sha256(shared_secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        self._fernet = Fernet(key)

    def encrypt_json(self, payload: dict[str, Any]) -> str:
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return self._fernet.encrypt(data).decode("utf-8")

    def decrypt_json(self, token: str) -> dict[str, Any]:
        try:
            data = self._fernet.decrypt(token.encode("utf-8"))
            
        except InvalidToken as exc:
            print("INVALID")
            raise AuthenticationError("Encrypted payload could not be authenticated") from exc
        return json.loads(data.decode("utf-8"))
