from __future__ import annotations

import json
import struct
from typing import Any

MAGIC = b"BPIP"
VERSION = 1
KIND_JSON = 1
KIND_BYTES = 2
KIND_CLOSE = 3
KIND_ERROR = 4
HEADER = struct.Struct("<4sBBI")
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024


def encode_frame(kind: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("Pipe payload exceeds the 64 MiB limit")
    return HEADER.pack(MAGIC, VERSION, kind, len(payload)) + payload


def encode_json(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return encode_frame(KIND_JSON, body)


class FrameDecoder:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        self._buffer.extend(data)
        frames: list[tuple[int, bytes]] = []
        while len(self._buffer) >= HEADER.size:
            magic, version, kind, payload_length = HEADER.unpack_from(self._buffer)
            if magic != MAGIC:
                raise ValueError("Invalid pipe frame magic")
            if version != VERSION:
                raise ValueError(f"Unsupported pipe protocol version: {version}")
            if payload_length > MAX_PAYLOAD_BYTES:
                raise ValueError("Pipe payload exceeds the 64 MiB limit")
            frame_length = HEADER.size + payload_length
            if len(self._buffer) < frame_length:
                break
            payload = bytes(self._buffer[HEADER.size:frame_length])
            del self._buffer[:frame_length]
            frames.append((kind, payload))
        return frames
