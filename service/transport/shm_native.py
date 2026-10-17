"""Windows shared slots. Semaphores transfer slot ownership between processes."""
from __future__ import annotations

import ctypes
import os
import struct
from ctypes import wintypes
from typing import Callable

from .base import ChannelClosed

MAGIC = b"BAASSHM1"
VERSION = 1
HEADER_BYTES = 256
SLOT_COUNT = 64
SLOT_BYTES = 65536
CHUNK_BYTES = SLOT_BYTES - 4
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024
MAPPING_BYTES = HEADER_BYTES + 2 * SLOT_COUNT * SLOT_BYTES
HEADER = struct.Struct("<8sIIIIII")
PACKET_HEADER = struct.Struct("<IBI")
_U32 = struct.Struct("<I")


def object_name(base: str, suffix: str = "") -> str:
    identifier = base.removeprefix("Local\\")
    if not identifier or len(identifier) > 120 or not all(
        ch.isascii() and (ch.isalnum() or ch in "-_") for ch in identifier
    ):
        raise ValueError("Shared-memory base must be a short local object name")
    return (base if base.startswith("Local\\") else f"Local\\{base}") + suffix


class PacketDecoder:
    """Reassemble logical packets across arbitrary slot boundaries."""

    def __init__(self, on_header: Callable | None = None, on_packet: Callable | None = None) -> None:
        self._buffer = bytearray()
        self._on_header = on_header
        self._on_packet = on_packet
        self._admitted = False

    def feed(self, chunk: bytes) -> list[tuple[int, int, bytes]]:
        self._buffer.extend(chunk)
        packets = []
        offset = 0
        while len(self._buffer) - offset >= PACKET_HEADER.size:
            stream, kind, length = PACKET_HEADER.unpack_from(self._buffer, offset)
            if kind not in (1, 2, 3, 4):
                raise ValueError(f"Unsupported shared-memory packet kind: {kind}")
            if length > MAX_PAYLOAD_BYTES:
                raise ValueError("Shared-memory payload exceeds the 64 MiB limit")
            if not self._admitted:
                if self._on_header is not None:
                    self._on_header(stream, kind, length)
                self._admitted = True
            packet_end = offset + PACKET_HEADER.size + length
            if len(self._buffer) < packet_end:
                break
            packet = (stream, kind, bytes(self._buffer[offset + PACKET_HEADER.size:packet_end]))
            if self._on_packet is None:
                packets.append(packet)
            else:
                self._on_packet(*packet)
            self._admitted = False
            offset = packet_end
        if offset:
            del self._buffer[:offset]
        return packets


class _Win32:
    def __init__(self) -> None:
        if os.name != "nt":
            raise RuntimeError("Shared-memory transport currently requires Windows")
        self.dll = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateFileMappingW": ([wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                    wintypes.DWORD, wintypes.LPCWSTR], wintypes.HANDLE),
            "OpenFileMappingW": ([wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "MapViewOfFile": ([wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                               ctypes.c_size_t], ctypes.c_void_p),
            "UnmapViewOfFile": ([ctypes.c_void_p], wintypes.BOOL),
            "CreateSemaphoreW": ([ctypes.c_void_p, wintypes.LONG, wintypes.LONG, wintypes.LPCWSTR], wintypes.HANDLE),
            "OpenSemaphoreW": ([wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "ReleaseSemaphore": ([wintypes.HANDLE, wintypes.LONG, ctypes.c_void_p], wintypes.BOOL),
            "CreateEventW": ([ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "OpenEventW": ([wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetEvent": ([wintypes.HANDLE], wintypes.BOOL),
            "WaitForMultipleObjects": ([wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE),
                                        wintypes.BOOL, wintypes.DWORD], wintypes.DWORD),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.dll, name)
            function.argtypes = arguments
            function.restype = result

    @staticmethod
    def checked(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())
        return value


class SharedMemorySession:
    """One duplex session; keep its reader/writer indices for its entire life.

    Production sessions are created by Rust. ``create`` is also exposed for
    native peer tests and uses exactly the same immutable header and objects.
    """

    def __init__(self, base: str, *, create: bool = False, owner_pid: int | None = None) -> None:
        self.base = base
        self._api = _Win32()
        self._handles: list[int] = []
        self._view = None
        self._closed = False
        self._indices = {(direction, role): 0 for direction in ("r2p", "p2r") for role in ("read", "write")}
        self._semaphores: dict[str, int] = {}
        dll = self._api.dll
        try:
            name = object_name(base)
            if create:
                mapping = self._own(dll.CreateFileMappingW(ctypes.c_void_p(-1), None, 4, 0, MAPPING_BYTES, name))
                if ctypes.get_last_error() == 183:
                    raise FileExistsError(f"Shared-memory session already exists: {name}")
            else:
                mapping = self._own(dll.OpenFileMappingW(0xF001F, False, name))
            self._view = self._api.checked(dll.MapViewOfFile(mapping, 0xF001F, 0, 0, MAPPING_BYTES))
            if create:
                self._write(0, HEADER.pack(MAGIC, VERSION, HEADER_BYTES, SLOT_COUNT, SLOT_BYTES,
                                           MAX_PAYLOAD_BYTES, owner_pid or os.getpid()))
            header = HEADER.unpack(self._read(0, HEADER.size))
            if header[:6] != (MAGIC, VERSION, HEADER_BYTES, SLOT_COUNT, SLOT_BYTES, MAX_PAYLOAD_BYTES):
                raise ValueError("Shared-memory header does not match protocol version 1")
            self.owner_pid = header[6]
            for direction in ("r2p", "p2r"):
                for role, initial in (("free", SLOT_COUNT), ("used", 0)):
                    key = f"{direction}_{role}"
                    sem_name = object_name(base, f"_{key}")
                    handle = (dll.CreateSemaphoreW(None, initial, SLOT_COUNT, sem_name) if create else
                              dll.OpenSemaphoreW(0x1F0003, False, sem_name))
                    self._semaphores[key] = self._own(handle)
            self._stop = self._own(dll.CreateEventW(None, True, False, object_name(base, "_stop")) if create else
                                   dll.OpenEventW(0x1F0003, False, object_name(base, "_stop")))
            self._owner = self._own(dll.OpenProcess(0x100000, False, self.owner_pid))
        except BaseException:
            self.close()
            raise

    @classmethod
    def create(cls, base: str, owner_pid: int | None = None) -> "SharedMemorySession":
        return cls(base, create=True, owner_pid=owner_pid)

    def _own(self, handle: int) -> int:
        self._api.checked(handle)
        self._handles.append(handle)
        return handle

    def _read(self, offset: int, length: int) -> bytes:
        return ctypes.string_at(self._view + offset, length)

    def _write(self, offset: int, payload: bytes) -> None:
        ctypes.memmove(self._view + offset, payload, len(payload))

    def publish_peer_pid(self) -> None:
        self._write(32, _U32.pack(os.getpid()))

    def new_wake_event(self) -> int:
        return self._own(self._api.dll.CreateEventW(None, False, False, None))

    def wake(self, event: int) -> None:
        self._api.checked(self._api.dll.SetEvent(event))

    def wait_for_wake(self, event: int) -> None:
        self._acquire(event, 0xFFFFFFFF)

    def _acquire(self, semaphore: int, timeout: int) -> bool:
        if self._closed:
            raise ChannelClosed("Shared-memory session closed")
        # Stop and owner death take priority even if a slot is available.
        handles = (wintypes.HANDLE * 3)(self._stop, self._owner, semaphore)
        result = self._api.dll.WaitForMultipleObjects(3, handles, False, timeout)
        if result in (0, 1):
            raise ChannelClosed("Shared-memory session stopped or its owner exited")
        if result == 2:
            return True
        if result == 258:
            return False
        raise ctypes.WinError(ctypes.get_last_error())

    def _release(self, key: str) -> None:
        self._api.checked(self._api.dll.ReleaseSemaphore(self._semaphores[key], 1, None))

    @staticmethod
    def _direction_offset(direction: str) -> int:
        if direction not in ("r2p", "p2r"):
            raise ValueError(f"Unknown shared-memory direction: {direction}")
        return HEADER_BYTES + (SLOT_COUNT * SLOT_BYTES if direction == "p2r" else 0)

    def write_chunk(self, direction: str, chunk: bytes, *, block: bool = True) -> bool:
        if not 0 < len(chunk) <= CHUNK_BYTES:
            raise ValueError("Shared-memory slot length must be between 1 and 65532")
        offset = self._direction_offset(direction)
        if not self._acquire(self._semaphores[f"{direction}_free"], 15_000 if block else 0):
            if block:
                self.stop()
                raise ChannelClosed("Shared-memory writer timed out waiting for a free slot")
            return False
        index = self._indices[direction, "write"]
        slot = offset + index * SLOT_BYTES
        self._write(slot + 4, chunk)
        self._write(slot, _U32.pack(len(chunk)))
        self._indices[direction, "write"] = (index + 1) % SLOT_COUNT
        self._release(f"{direction}_used")
        return True

    def read_chunk(self, direction: str, *, block: bool = True) -> bytes | None:
        offset = self._direction_offset(direction)
        if not self._acquire(self._semaphores[f"{direction}_used"], 0xFFFFFFFF if block else 0):
            return None
        index = self._indices[direction, "read"]
        slot = offset + index * SLOT_BYTES
        try:
            length = _U32.unpack(self._read(slot, 4))[0]
            if not 0 < length <= CHUNK_BYTES:
                self.stop()
                raise ValueError(f"Invalid shared-memory slot length: {length}")
            return self._read(slot + 4, length)
        finally:
            self._indices[direction, "read"] = (index + 1) % SLOT_COUNT
            self._release(f"{direction}_free")

    def stop(self) -> None:
        if not self._closed and hasattr(self, "_stop"):
            self._api.checked(self._api.dll.SetEvent(self._stop))

    def close(self) -> None:
        """Release handles after the caller has stopped and joined all workers."""
        if self._closed:
            return
        self._closed = True
        if self._view is not None:
            self._api.dll.UnmapViewOfFile(self._view)
            self._view = None
        for handle in reversed(self._handles):
            self._api.dll.CloseHandle(handle)
        self._handles.clear()
