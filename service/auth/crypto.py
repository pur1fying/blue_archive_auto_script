from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .constants import ARGON2_HASH_BYTES, ARGON2_MEMLIMIT, ARGON2_OPSLIMIT
from .errors import AuthenticationError

try:
    from nacl import pwhash
except ModuleNotFoundError:  # pragma: no cover - surfaced explicitly at runtime
    pwhash = None


def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def canonical_dumps(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def hkdf_sha256(key_material: bytes, info: bytes, length: int, salt: Optional[bytes] = None) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    ).derive(key_material)


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def argon2(password: str, salt: bytes) -> bytes:
    if pwhash is None:
        raise RuntimeError("PyNaCl is required for Argon2id password derivation")
    return pwhash.argon2id.kdf(
        ARGON2_HASH_BYTES,
        password.encode("utf-8"),
        salt,
        opslimit=ARGON2_OPSLIMIT,
        memlimit=ARGON2_MEMLIMIT,
    )


def session_nonce(seq: int) -> bytes:
    if seq < 0:
        raise AuthenticationError("Sequence number underflow")
    return seq.to_bytes(12, "big", signed=False)
