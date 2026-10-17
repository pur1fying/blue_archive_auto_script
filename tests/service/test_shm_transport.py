from __future__ import annotations

import asyncio
import json
import runpy
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from service.transport.base import ChannelClosed
from service.transport.framing import KIND_BYTES, KIND_CLOSE, KIND_JSON
from service.transport.shm_endpoint import SharedMemoryWriter
from service.transport.shm_budget import InboundBudget
from service.transport.shm_native import (
    CHUNK_BYTES, HEADER_BYTES, MAX_PAYLOAD_BYTES, PACKET_HEADER, SLOT_COUNT, PacketDecoder, SharedMemorySession,
)

_WINDOWS = pytest.mark.skipif(sys.platform != "win32", reason="Windows shared memory only")
ROOT = Path(__file__).resolve().parents[2]


def _packet(stream: int, kind: int, payload: bytes) -> bytes:
    return PACKET_HEADER.pack(stream, kind, len(payload)) + payload


def _send(session, stream, kind, payload):
    packet = _packet(stream, kind, payload)
    for offset in range(0, len(packet), CHUNK_BYTES):
        session.write_chunk("r2p", packet[offset:offset + CHUNK_BYTES])


class _Receiver:
    def __init__(self, owner):
        self.owner = owner
        self.decoder = PacketDecoder()
        self.pending = []

    def receive(self):
        while not self.pending:
            self.pending.extend(self.decoder.feed(self.owner.read_chunk("p2r")))
        return self.pending.pop(0)


def test_shm_packets_reassemble_arbitrary_boundaries_and_keep_stream_order():
    expected = [(1, KIND_JSON, b'{"text":"hello"}'), (2, KIND_BYTES, b"x" * 100_001),
                (1, KIND_BYTES, b""), (2, KIND_CLOSE, b"")]
    data = b"".join(_packet(*packet) for packet in expected)
    decoder = PacketDecoder()
    received = []
    for start in range(0, len(data), 7):
        received.extend(decoder.feed(data[start:start + 7]))
    assert received == expected


@pytest.mark.parametrize("kind,length", [(99, 0), (KIND_JSON, MAX_PAYLOAD_BYTES + 1)])
def test_shm_rejects_invalid_kind_and_oversized_length_before_payload(kind, length):
    with pytest.raises(ValueError):
        PacketDecoder().feed(PACKET_HEADER.pack(1, kind, length))


def test_shm_writer_fast_path_avoids_executor_dispatch(monkeypatch):
    class AvailableSlots:
        def __init__(self):
            self.chunks = []

        def write_chunk(self, direction, chunk, *, block=True):
            assert direction == "p2r" and block is False
            self.chunks.append(chunk)
            return True

        def stop(self):
            pass

    async def no_executor(*args, **kwargs):
        raise AssertionError("A writable shared-memory slot should not use the executor")

    async def scenario():
        session = AvailableSlots()
        failures = []
        writer = SharedMemoryWriter(session, failures.append)
        try:
            await writer.write(1, KIND_BYTES, b"first")
            await writer.write(2, KIND_BYTES, b"second")
            decoder = PacketDecoder()
            packets = [packet for chunk in session.chunks for packet in decoder.feed(chunk)]
            assert packets == [(1, KIND_BYTES, b"first"), (2, KIND_BYTES, b"second")]
            assert failures == []
        finally:
            await writer.close()

    monkeypatch.setattr(asyncio, "to_thread", no_executor)
    asyncio.run(scenario())


def test_shm_cli_options_are_mutually_exclusive(monkeypatch):
    parse_args = runpy.run_path(str(ROOT / "main.service.py"))["parse_args"]
    monkeypatch.setattr(sys, "argv", ["main.service.py", "--shm-name", "baas-test"])
    assert parse_args().shm_name == "baas-test"
    monkeypatch.setattr(sys, "argv", ["main.service.py", "--pipe-name", "pipe", "--shm-name", "shm"])
    with pytest.raises(SystemExit) as error:
        parse_args()
    assert error.value.code == 2


def test_shm_setup_schema_retains_explicit_transport_marker(tmp_path):
    from service.conf.manager import ConfigManager
    from service.update.setup_schema import migrate_to_current_schema

    manager = ConfigManager(tmp_path)
    manager._setup_toml = {"general": {"transport": "pipe", "transport_version": 1}}
    unchanged = manager._merge_setup_toml({"channel": "stable"})
    assert unchanged["general"]["transport"] == "pipe"
    assert unchanged["general"]["transport_version"] == 1
    selected = manager._merge_setup_toml({"transport": "shm"})
    assert selected["general"]["transport"] == "shm"
    assert migrate_to_current_schema(selected)["general"]["transport_version"] == 1


@pytest.mark.parametrize("transport", ["websocket", "pipe", "shm", "unknown", None])
def test_transport_schema_normalizes_without_losing_legacy_choices(transport):
    from service.update.setup_schema import migrate_to_current_schema

    normalized = migrate_to_current_schema({"general": {"transport": transport}})
    expected = transport if transport in ("websocket", "pipe", "shm") else "websocket"
    assert normalized["general"]["transport"] == expected


@_WINDOWS
def test_shm_native_slots_wrap_and_apply_backpressure_without_dropping():
    owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
    peer = SharedMemorySession(owner.base)
    try:
        for cycle in range(3):
            for index in range(SLOT_COUNT):
                assert owner.write_chunk("r2p", f"{cycle}:{index}".encode(), block=False)
            assert not owner.write_chunk("r2p", b"must wait", block=False)
            for index in range(SLOT_COUNT):
                assert peer.read_chunk("r2p") == f"{cycle}:{index}".encode()
            assert peer.read_chunk("r2p", block=False) is None
        owner.stop()
        with pytest.raises(ChannelClosed):
            peer.read_chunk("r2p")
    finally:
        peer.close()
        owner.close()


@_WINDOWS
def test_shm_corrupt_slot_stops_session_instead_of_reusing_its_bytes():
    owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
    peer = SharedMemorySession(owner.base)
    try:
        owner.write_chunk("r2p", b"payload")
        owner._write(HEADER_BYTES, b"\0\0\0\0")
        with pytest.raises(ValueError, match="slot length"):
            peer.read_chunk("r2p")
        with pytest.raises(ChannelClosed):
            owner.write_chunk("r2p", b"next packet")
    finally:
        peer.close()
        owner.close()


@_WINDOWS
@pytest.mark.parametrize("loop_busy,consumer_delay", [(0.5, 0), (0, 0.002)])
def test_shm_inbound_byte_budget_backpressures_busy_loop_and_slow_consumer(loop_busy, consumer_delay):
    async def scenario():
        owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
        receiver = _Receiver(owner)
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "tests/service/shm_echo_peer.py"), "--shm-name", owner.base,
             "--report-budget"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        count = 256
        payload = b"x" * (128 * 1024)

        def produce():
            for _ in range(count):
                _send(owner, 1, KIND_BYTES, payload)

        def consume():
            for _ in range(count):
                assert receiver.receive() == (1, KIND_BYTES, payload)
            assert receiver.receive() == (1, KIND_CLOSE, b"")

        try:
            await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
            await asyncio.to_thread(_send, owner, 1, KIND_JSON,
                                    b'{"type":"open","channel":"echo","name":"stress"}')
            await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
            plan = json.dumps({"messages": ["bytes"] * count, "loop_busy_seconds": loop_busy,
                               "consume_delay_seconds": consumer_delay}).encode()
            await asyncio.to_thread(_send, owner, 1, KIND_JSON, plan)
            producer = asyncio.create_task(asyncio.to_thread(produce))
            await asyncio.sleep(0.15)
            assert not producer.done(), "32 MiB producer must wait while the consumer/loop is stalled"
            await asyncio.wait_for(asyncio.gather(producer, asyncio.to_thread(consume)), 10)
            owner.stop()
            await asyncio.to_thread(process.wait, 5)
            assert process.returncode == 0, process.stderr.read().decode(errors="replace")
            report = json.loads(process.stdout.read())
            assert 7 * 1024 * 1024 < report["inbound_peak_bytes"] <= 8 * 1024 * 1024
            assert report["inbound_retained_bytes"] == 0
        finally:
            owner.stop()
            if process.poll() is None:
                process.terminate()
                await asyncio.to_thread(process.wait, 5)
            owner.close()
            process.communicate()

    asyncio.run(scenario())


@_WINDOWS
def test_shm_stop_unblocks_a_reader_waiting_for_inbound_byte_budget():
    async def scenario():
        owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
        receiver = _Receiver(owner)
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "tests/service/shm_echo_peer.py"), "--shm-name", owner.base,
             "--report-budget"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

        def produce():
            for _ in range(256):
                _send(owner, 1, KIND_BYTES, b"x" * (128 * 1024))

        try:
            await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
            await asyncio.to_thread(_send, owner, 1, KIND_JSON,
                                    b'{"type":"open","channel":"echo","name":"stress"}')
            await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
            await asyncio.to_thread(_send, owner, 1, KIND_JSON,
                                    b'{"messages":["bytes"],"consume_delay_seconds":10}')
            producer = asyncio.create_task(asyncio.to_thread(produce))
            await asyncio.sleep(0.15)
            assert not producer.done()
            owner.stop()
            with pytest.raises(ChannelClosed):
                await asyncio.wait_for(producer, 2)
            await asyncio.to_thread(process.wait, 3)
            assert process.returncode == 0, process.stderr.read().decode(errors="replace")
            report = json.loads(process.stdout.read())
            assert report["inbound_peak_bytes"] <= 8 * 1024 * 1024
            assert report["inbound_retained_bytes"] == 0
        finally:
            owner.stop()
            if process.poll() is None:
                process.terminate()
                await asyncio.to_thread(process.wait, 5)
            owner.close()
            process.communicate()

    asyncio.run(scenario())


@_WINDOWS
def test_shm_echo_peer_preserves_large_json_binary_empty_payload_and_reopen():
    async def scenario():
        owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
        receiver = _Receiver(owner)
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "tests/service/shm_echo_peer.py"), "--shm-name", owner.base],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            ready = await asyncio.wait_for(asyncio.to_thread(receiver.receive), 10)
            assert ready[:2] == (0, KIND_JSON)
            assert json.loads(ready[2]) == {"type": "ready", "transport": "shm", "version": 1}
            payloads = [
                (KIND_JSON, json.dumps({"text": "测试", "body": "x" * 100_001}, ensure_ascii=False,
                                      separators=(",", ":")).encode()),
                (KIND_BYTES, b""),
                (KIND_BYTES, bytes(range(256)) * 36_865),  # More than 9 MiB and two complete ring wraps.
            ]
            for stream in (1, 2):
                await asyncio.to_thread(_send, owner, stream, KIND_JSON,
                                        b'{"type":"open","channel":"echo","name":"test"}')
                opened = await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
                assert opened[:2] == (stream, KIND_JSON)
                assert json.loads(opened[2]) == {"type": "open_ok", "channel": "echo"}
                plan = json.dumps({"messages": ["json" if kind == KIND_JSON else "bytes" for kind, _ in payloads]}).encode()
                await asyncio.to_thread(_send, owner, stream, KIND_JSON, plan)
                for kind, payload in payloads:
                    _, echoed = await asyncio.wait_for(asyncio.gather(
                        asyncio.to_thread(_send, owner, stream, kind, payload),
                        asyncio.to_thread(receiver.receive),
                    ), 10)
                    assert echoed == (stream, kind, payload)
                assert await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5) == (stream, KIND_CLOSE, b"")
            owner.stop()
            await asyncio.to_thread(process.wait, 5)
            assert process.returncode == 0, process.stderr.read().decode(errors="replace")
        finally:
            owner.stop()
            if process.poll() is None:
                process.terminate()
                await asyncio.to_thread(process.wait, 5)
            owner.close()
            process.communicate()

    asyncio.run(scenario())


@_WINDOWS
def test_retired_stream_close_is_idempotent_and_keeps_other_streams_usable():
    async def scenario():
        owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
        receiver = _Receiver(owner)
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "tests/service/shm_echo_peer.py"), "--shm-name", owner.base],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

        async def receive():
            return await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)

        async def send(stream, kind, payload):
            await asyncio.to_thread(_send, owner, stream, kind, payload)

        async def open_stream(stream):
            await send(stream, KIND_JSON, b'{"type":"open","channel":"echo","name":"test"}')
            assert (await receive())[:2] == (stream, KIND_JSON)

        try:
            await receive()  # READY.
            await open_stream(1)
            await send(1, KIND_JSON, b'{"messages":["bytes"]}')  # Keep this handler active.
            await open_stream(2)
            await send(2, KIND_JSON, b'{"messages":[]}')
            assert await receive() == (2, KIND_CLOSE, b"")
            await asyncio.sleep(0.01)  # Let the completed handler retire its stream entry.
            await send(2, KIND_CLOSE, b"")
            await send(1, KIND_BYTES, b"other stream remains active")
            assert await receive() == (1, KIND_BYTES, b"other stream remains active")
            assert await receive() == (1, KIND_CLOSE, b"")
            await open_stream(3)
            await send(3, KIND_JSON, b'{"messages":[]}')
            assert await receive() == (3, KIND_CLOSE, b"")
            owner.stop()
            await asyncio.to_thread(process.wait, 5)
            assert process.returncode == 0, process.stderr.read().decode(errors="replace")
        finally:
            owner.stop()
            if process.poll() is None:
                process.terminate()
                await asyncio.to_thread(process.wait, 5)
            owner.close()
            process.communicate()

    asyncio.run(scenario())


@_WINDOWS
def test_cancelling_shm_sender_cannot_truncate_an_inflight_large_packet():
    async def scenario():
        owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
        peer = SharedMemorySession(owner.base)
        failures = []
        writer = SharedMemoryWriter(peer, failures.append)
        receiver = _Receiver(owner)
        payload = b"x" * (6 * 1024 * 1024)
        try:
            sender = asyncio.create_task(writer.write(1, KIND_BYTES, payload))
            await asyncio.sleep(0.02)  # Fill the ring and block partway through the first packet.
            sender.cancel()
            with pytest.raises(asyncio.CancelledError):
                await sender
            next_sender = asyncio.create_task(writer.write(2, KIND_BYTES, b"next packet"))
            first = await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
            second = await asyncio.wait_for(asyncio.to_thread(receiver.receive), 5)
            await asyncio.wait_for(next_sender, 5)
            assert first == (1, KIND_BYTES, payload)
            assert second == (2, KIND_BYTES, b"next packet")
            assert failures == []
        finally:
            owner.stop()
            await writer.close()
            peer.close()
            owner.close()

    asyncio.run(scenario())


@_WINDOWS
def test_shm_budget_admits_one_maximum_packet_before_allocating_its_body():
    owner = SharedMemorySession.create("baas-test-" + uuid.uuid4().hex)
    peer = SharedMemorySession(owner.base)
    budget = InboundBudget(peer)
    leases = []
    try:
        decoder = PacketDecoder(lambda stream, kind, length: leases.append(budget.acquire(stream, length)))
        assert decoder.feed(PACKET_HEADER.pack(1, KIND_BYTES, MAX_PAYLOAD_BYTES)) == []
        assert MAX_PAYLOAD_BYTES < budget.used_bytes < MAX_PAYLOAD_BYTES + 128
        assert budget.try_acquire(1, 0) is None
        assert budget.try_acquire(2, 0) is None
        leases.pop().release()
        small = budget.acquire(2, 100)
        assert budget.try_acquire(1, MAX_PAYLOAD_BYTES) is None
        small.release()
        assert budget.used_bytes == 0
    finally:
        for lease in leases:
            lease.release()
        budget.close()
        owner.stop()
        peer.close()
        owner.close()


@_WINDOWS
@pytest.mark.parametrize("waiting_for", ["slot", "byte_budget"])
def test_shm_wait_detects_owner_process_death(waiting_for):
    base = "baas-test-" + uuid.uuid4().hex
    code = (
        "from service.transport.shm_native import SharedMemorySession; "
        f"session=SharedMemorySession.create({base!r}); "
        "print('ready',flush=True); input()"
    )
    process = subprocess.Popen([sys.executable, "-c", code], cwd=ROOT, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peer = None
    budget = None
    lease = None
    try:
        assert process.stdout.readline() == b"ready\r\n"
        peer = SharedMemorySession(base)
        with ThreadPoolExecutor(max_workers=1) as pool:
            if waiting_for == "byte_budget":
                budget = InboundBudget(peer, total_bytes=100, stream_bytes=100)
                lease = budget.acquire(1, 1)
                waiting = pool.submit(budget.acquire, 1, 1)
            else:
                waiting = pool.submit(peer.read_chunk, "r2p")
            process.terminate()
            process.wait(timeout=5)
            with pytest.raises(ChannelClosed, match="owner exited"):
                waiting.result(timeout=2)
    finally:
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=5)
        if lease is not None:
            lease.release()
        if budget is not None:
            budget.close()
        if peer is not None:
            peer.close()
