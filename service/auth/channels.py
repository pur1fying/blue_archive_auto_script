from __future__ import annotations

import json
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from .crypto import b64d, b64e, canonical_dumps, session_nonce
from .errors import AuthenticationError

try:
    from nacl import bindings as sodium_bindings
except ModuleNotFoundError:  # pragma: no cover - surfaced explicitly at runtime
    sodium_bindings = None


class JsonChaChaChannel:
    """Small framed JSON channel using direction-bound ChaCha20-Poly1305 keys."""

    def __init__(self, *, tx_key: bytes, rx_key: bytes) -> None:
        self._tx = ChaCha20Poly1305(tx_key)
        self._rx = ChaCha20Poly1305(rx_key)
        self._tx_seq = 0
        self._rx_seq = 0

    def encrypt(self, payload: dict[str, Any]) -> dict[str, Any]:
        seq = self._tx_seq
        self._tx_seq += 1
        nonce = session_nonce(seq)
        aad = canonical_dumps({"seq": seq, "type": "secure"})
        plaintext = canonical_dumps(payload)
        ciphertext = self._tx.encrypt(nonce, plaintext, aad)
        return {
            "type": "secure",
            "seq": seq,
            "ciphertext": b64e(ciphertext),
        }

    def decrypt(self, message: dict[str, Any]) -> dict[str, Any]:
        if message.get("type") != "secure":
            raise AuthenticationError("Encrypted control frame expected")
        seq = int(message["seq"])
        if seq != self._rx_seq:
            raise AuthenticationError("Control frame sequence mismatch")
        self._rx_seq += 1
        nonce = session_nonce(seq)
        aad = canonical_dumps({"seq": seq, "type": "secure"})
        plaintext = self._rx.decrypt(nonce, b64d(message["ciphertext"]), aad)
        return json.loads(plaintext.decode("utf-8"))

    def set_rx_seq(self, seq: int) -> None:
        self._rx_seq = seq


class SecretStreamBox:
    """Directional XChaCha20 secretstream state with context-bound AAD."""

    def __init__(self, *, tx_key: bytes, rx_key: bytes, aad_prefix: bytes) -> None:
        if sodium_bindings is None:
            raise RuntimeError("PyNaCl is required for secretstream websocket transport")
        self._aad_prefix = aad_prefix
        self._tx_seq = 0
        self._rx_seq = 0
        self._tx_state = sodium_bindings.crypto_secretstream_xchacha20poly1305_state()
        self._rx_state = sodium_bindings.crypto_secretstream_xchacha20poly1305_state()
        self.tx_header = sodium_bindings.crypto_secretstream_xchacha20poly1305_init_push(self._tx_state, tx_key)
        self._rx_key = rx_key

    def init_pull(self, header: bytes) -> None:
        sodium_bindings.crypto_secretstream_xchacha20poly1305_init_pull(self._rx_state, header, self._rx_key)

    def encrypt(self, payload: bytes, *, final: bool = False) -> bytes:
        tag = (
            sodium_bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL
            if final
            else sodium_bindings.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE
        )
        aad = self._aad(self._tx_seq)
        self._tx_seq += 1
        return sodium_bindings.crypto_secretstream_xchacha20poly1305_push(self._tx_state, payload, aad, tag)

    def decrypt(self, ciphertext: bytes) -> bytes:
        aad = self._aad(self._rx_seq)
        self._rx_seq += 1
        plaintext, tag = sodium_bindings.crypto_secretstream_xchacha20poly1305_pull(self._rx_state, ciphertext, aad)
        if tag not in (
            sodium_bindings.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE,
            sodium_bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL,
        ):
            raise AuthenticationError("Unexpected stream tag received")
        return plaintext

    def _aad(self, seq: int) -> bytes:
        return self._aad_prefix + seq.to_bytes(8, "big", signed=False)


