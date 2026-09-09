from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from .constants import ARGON2_HASH_BYTES, ARGON2_MEMLIMIT, ARGON2_OPSLIMIT, ARGON2_SALT_BYTES
from .crypto import b64e


@dataclass
class PasswordState:
    initialized: bool = False
    pwd_epoch: int = 0
    pwd_salt: Optional[bytes] = None
    pwd_hash: Optional[bytes] = None

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "initialized": self.initialized,
            "pwd_epoch": self.pwd_epoch,
            "pwd_salt": b64e(self.pwd_salt) if self.pwd_salt else None,
            "argon2": {
                "algorithm": "argon2id",
                "opslimit": ARGON2_OPSLIMIT,
                "memlimit": ARGON2_MEMLIMIT,
                "salt_bytes": ARGON2_SALT_BYTES,
                "hash_bytes": ARGON2_HASH_BYTES,
            },
        }


@dataclass
class ActiveSession:
    session_id: str
    created_at: float
    expires_at: float
    pwd_epoch: int
    master_secret: bytes
    resume_secret: bytes
    control_queues: set[asyncio.Queue] = field(default_factory=set)


@dataclass
class RememberedLogin:
    token_id: str
    token_hash: bytes
    created_at: float
    expires_at: float
    pwd_epoch: int


@dataclass
class HandshakeContext:
    kind: str
    channel: str
    client_nonce: bytes
    server_nonce: bytes
    client_public_key: bytes
    server_private_key: X25519PrivateKey
    server_public_key: bytes
    transcript: bytes
    transcript_hash: bytes
    shared_key: bytes
    preauth_server_tx: bytes
    preauth_server_rx: bytes


