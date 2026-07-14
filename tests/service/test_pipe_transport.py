from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from service.transport.framing import (
    HEADER,
    KIND_BYTES,
    KIND_CLOSE,
    KIND_JSON,
    FrameDecoder,
    encode_frame,
    encode_json,
)
from service.transport.pipe_server import PipeTransportServer, _HANDLERS


def test_frame_decoder_accepts_fragmented_and_coalesced_frames():
    decoder = FrameDecoder()
    payload = encode_json({"type": "first"}) + encode_frame(KIND_BYTES, b"second")

    assert decoder.feed(payload[:7]) == []
    frames = decoder.feed(payload[7:])

    assert frames[0][0] == KIND_JSON
    assert json.loads(frames[0][1]) == {"type": "first"}
    assert frames[1] == (KIND_BYTES, b"second")


async def _read_frame(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    header = await reader.readexactly(HEADER.size)
    _, _, kind, length = HEADER.unpack(header)
    return kind, await reader.readexactly(length)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows named pipes only")
def test_named_pipe_channel_round_trip(monkeypatch):
    class EchoHandler:
        def __init__(self, context):
            self.context = context

        async def handle(self, endpoint):
            message = await endpoint.recv_json()
            binary = await endpoint.recv_bytes()
            await endpoint.send_json({"echo": message, "size": len(binary)})
            await endpoint.send_bytes(binary[::-1])

    async def scenario():
        monkeypatch.setitem(_HANDLERS, "test", EchoHandler)
        pipe_name = rf"\\.\pipe\baas-test-{uuid.uuid4().hex}"
        server = PipeTransportServer(pipe_name, SimpleNamespace())
        await server.start()
        try:
            loop = asyncio.get_running_loop()
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            transport, _ = await loop.create_pipe_connection(lambda: protocol, pipe_name)
            writer = asyncio.StreamWriter(transport, protocol, reader, loop)
            writer.write(encode_json({"type": "open", "channel": "test", "name": "smoke"}))
            await writer.drain()
            kind, payload = await _read_frame(reader)
            assert kind == KIND_JSON
            assert json.loads(payload) == {"type": "open_ok", "channel": "test"}

            writer.write(encode_json({"value": 42}) + encode_frame(KIND_BYTES, b"abcdef"))
            await writer.drain()
            kind, payload = await _read_frame(reader)
            assert kind == KIND_JSON
            assert json.loads(payload) == {"echo": {"value": 42}, "size": 6}
            assert await _read_frame(reader) == (KIND_BYTES, b"fedcba")
            assert (await _read_frame(reader))[0] == KIND_CLOSE
            writer.close()
        finally:
            await server.close()

    asyncio.run(scenario())


@pytest.mark.skipif(sys.platform == "win32", reason="Unix sockets are unavailable on Windows")
def test_unix_pipe_channel_round_trip(monkeypatch):
    class EchoHandler:
        def __init__(self, context):
            self.context = context

        async def handle(self, endpoint):
            message = await endpoint.recv_json()
            binary = await endpoint.recv_bytes()
            await endpoint.send_json({"echo": message, "size": len(binary)})
            await endpoint.send_bytes(binary[::-1])

    async def scenario():
        monkeypatch.setitem(_HANDLERS, "test", EchoHandler)
        socket_path = Path("/tmp") / f"baas-test-{uuid.uuid4().hex}.sock"
        socket_path.write_text("stale", encoding="utf-8")
        server = PipeTransportServer(str(socket_path), SimpleNamespace())
        await server.start()
        assert socket_path.exists()
        try:
            reader, writer = await asyncio.open_unix_connection(str(socket_path))
            writer.write(encode_json({"type": "open", "channel": "test", "name": "smoke"}))
            await writer.drain()
            kind, payload = await _read_frame(reader)
            assert kind == KIND_JSON
            assert json.loads(payload) == {"type": "open_ok", "channel": "test"}

            writer.write(encode_json({"value": 42}) + encode_frame(KIND_BYTES, b"abcdef"))
            await writer.drain()
            kind, payload = await _read_frame(reader)
            assert kind == KIND_JSON
            assert json.loads(payload) == {"echo": {"value": 42}, "size": 6}
            assert await _read_frame(reader) == (KIND_BYTES, b"fedcba")
            assert (await _read_frame(reader))[0] == KIND_CLOSE
            writer.close()
            await writer.wait_closed()
        finally:
            await server.close()
        assert not socket_path.exists()

    asyncio.run(scenario())
