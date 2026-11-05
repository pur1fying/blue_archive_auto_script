"""Native shared slots. Semaphores transfer slot ownership between processes."""
from __future__ import annotations

import ctypes
import ctypes.util
import errno
import mmap
import os
import select
import struct
import sys
import threading
import time
from typing import Callable
from types import SimpleNamespace

if os.name == "nt":
    from ctypes import wintypes

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
SUPPORTED_PLATFORMS = ("win32", "linux")


def object_name(base: str, suffix: str = "") -> str:
    identifier = base.removeprefix("Local\\") if os.name == "nt" else base.removeprefix("/")
    if not identifier or len(identifier) > 120 or not all(
        ch.isascii() and (ch.isalnum() or ch in "-_") for ch in identifier
    ):
        raise ValueError("Shared-memory base must be a short local object name")
    if os.name == "nt":
        return (base if base.startswith("Local\\") else f"Local\\{base}") + suffix
    return f"/{identifier}{suffix}"


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


class _Timespec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]


def _posix_api(signatures: dict) -> SimpleNamespace:
    """Older glibc exposes shm/sem through librt/libpthread instead of libc."""
    libraries = [ctypes.CDLL(None, use_errno=True)]
    functions = {}
    candidates = iter(("rt", "pthread"))
    for name, (arguments, result) in signatures.items():
        function = next((getattr(library, name) for library in libraries if hasattr(library, name)), None)
        while function is None:
            candidate = next(candidates, None)
            if candidate is None:
                raise RuntimeError(f"POSIX shared-memory function is unavailable: {name}")
            soname = "librt.so.1" if candidate == "rt" else "libpthread.so.0"
            try:
                library = ctypes.CDLL(ctypes.util.find_library(candidate) or soname, use_errno=True)
            except OSError:
                continue
            libraries.append(library)
            function = getattr(library, name, None)
        function.argtypes = arguments
        function.restype = result
        functions[name] = function
    return SimpleNamespace(**functions, _libraries=libraries)


class _PosixSharedMemorySession(SharedMemorySession):
    """Linux POSIX shm/sem peer using the same immutable v1 slot layout.

    The creating process owns the names. Attaching processes only close their
    mappings and semaphore handles; they never unlink another process's names.
    A latched stop semaphore and pidfd cancel waits within 50 milliseconds.
    """

    def __init__(self, base: str, *, create: bool = False, owner_pid: int | None = None) -> None:
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            raise RuntimeError("Shared-memory transport requires a 64-bit Linux desktop runtime")
        self.base = base
        self._closed = False
        self._view = None
        self._stop = None
        self._creator = create
        self._created_names: list[tuple[str, bytes]] = []
        self._semaphores: dict[str, int] = {}
        self._pidfd: int | None = None
        self._watched_pid = 0
        self._watched_start_time: str | None = None
        self._peer_lock = threading.Lock()
        self._stop_lock = threading.Lock()
        self._stop_requested = False
        self._indices = {(direction, role): 0 for direction in ("r2p", "p2r") for role in ("read", "write")}
        signatures = {
            "shm_open": ([ctypes.c_char_p, ctypes.c_int, ctypes.c_uint], ctypes.c_int),
            "shm_unlink": ([ctypes.c_char_p], ctypes.c_int),
            "sem_open": ([ctypes.c_char_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint], ctypes.c_void_p),
            "sem_close": ([ctypes.c_void_p], ctypes.c_int),
            "sem_unlink": ([ctypes.c_char_p], ctypes.c_int),
            "sem_trywait": ([ctypes.c_void_p], ctypes.c_int),
            "sem_timedwait": ([ctypes.c_void_p, ctypes.POINTER(_Timespec)], ctypes.c_int),
            "sem_post": ([ctypes.c_void_p], ctypes.c_int),
            "sem_getvalue": ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)], ctypes.c_int),
        }
        self._libc = _posix_api(signatures)
        try:
            name = object_name(base).encode("ascii")
            flags = os.O_RDWR | (os.O_CREAT | os.O_EXCL if create else 0)
            descriptor = self._libc.shm_open(name, flags, 0o600)
            if descriptor < 0:
                self._raise_oserror(name)
            if create:
                self._created_names.append(("shm", name))
            try:
                if create:
                    os.ftruncate(descriptor, MAPPING_BYTES)
                elif os.fstat(descriptor).st_size != MAPPING_BYTES:
                    raise ValueError("Shared-memory mapping size does not match protocol version 1")
                self._view = mmap.mmap(descriptor, MAPPING_BYTES, flags=mmap.MAP_SHARED,
                                       prot=mmap.PROT_READ | mmap.PROT_WRITE)
            finally:
                os.close(descriptor)
            if create:
                self._write(0, HEADER.pack(MAGIC, VERSION, HEADER_BYTES, SLOT_COUNT, SLOT_BYTES,
                                           MAX_PAYLOAD_BYTES, owner_pid or os.getpid()))
            header = HEADER.unpack(self._read(0, HEADER.size))
            if header[:6] != (MAGIC, VERSION, HEADER_BYTES, SLOT_COUNT, SLOT_BYTES, MAX_PAYLOAD_BYTES):
                raise ValueError("Shared-memory header does not match protocol version 1")
            self.owner_pid = header[6]
            if self.owner_pid <= 0:
                raise ValueError("Shared-memory owner PID must be positive")
            for direction in ("r2p", "p2r"):
                for role, initial in (("free", SLOT_COUNT), ("used", 0)):
                    key = f"{direction}_{role}"
                    self._semaphores[key] = self._open_semaphore(f"_{key}", create, initial)
            self._stop = self._open_semaphore("_stop", create, 0)
            self._check_peer()
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _raise_oserror(name: bytes | None = None) -> None:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), name.decode("ascii") if name else None)

    def _open_semaphore(self, suffix: str, create: bool, initial: int) -> int:
        name = object_name(self.base, suffix).encode("ascii")
        handle = self._libc.sem_open(name, os.O_CREAT | os.O_EXCL if create else 0, 0o600, initial)
        # glibc uses NULL for SEM_FAILED; accept the conventional -1 as well.
        if handle in (None, ctypes.c_void_p(-1).value):
            self._raise_oserror(name)
        if create:
            self._created_names.append(("sem", name))
        return handle

    def _read(self, offset: int, length: int) -> bytes:
        return self._view[offset:offset + length]

    def _write(self, offset: int, payload: bytes) -> None:
        self._view[offset:offset + len(payload)] = payload

    def new_wake_event(self) -> threading.Semaphore:
        return threading.Semaphore(0)

    def wake(self, event: threading.Semaphore) -> None:
        event.release()

    def wait_for_wake(self, event: threading.Semaphore) -> None:
        while True:
            self._check_cancelled()
            if event.acquire(timeout=0.05):
                self._check_cancelled()
                return

    def _check_cancelled(self) -> None:
        if self._closed:
            raise ChannelClosed("Shared-memory session closed")
        if self._stop is not None:
            value = ctypes.c_int()
            if self._libc.sem_getvalue(self._stop, ctypes.byref(value)) != 0:
                self._raise_oserror()
            if value.value > 0:
                raise ChannelClosed("Shared-memory session stopped")
        with self._peer_lock:
            self._check_peer()

    def _check_peer(self) -> None:
        pid = _U32.unpack(self._read(32, 4))[0] if self._creator else self.owner_pid
        if not pid:
            return  # The Python peer has not attached/published its PID yet.
        if pid != self._watched_pid:
            if self._pidfd is not None:
                os.close(self._pidfd)
                self._pidfd = None
            self._watched_pid = pid
            self._watched_start_time = None
            if hasattr(os, "pidfd_open"):
                try:
                    self._pidfd = os.pidfd_open(pid)
                except ProcessLookupError:
                    raise ChannelClosed("Shared-memory session owner exited") from None
                except OSError as exc:
                    if exc.errno not in (errno.ENOSYS, errno.EINVAL, errno.EPERM, errno.EACCES):
                        raise
        if self._pidfd is not None:
            poller = select.poll()
            poller.register(self._pidfd, select.POLLIN)
            if poller.poll(0):
                raise ChannelClosed("Shared-memory session owner exited")
        else:
            # A process may remain a zombie until its parent calls wait(), and
            # kill(pid, 0) also accepts a PID that has been recycled. Linux proc
            # state/starttime distinguishes both when pidfd is unavailable.
            try:
                with open(f"/proc/{pid}/stat", encoding="ascii") as process:
                    fields = process.read().rsplit(")", 1)[1].split()
                if fields[0] in ("Z", "X"):
                    raise ChannelClosed("Shared-memory session owner exited")
                if self._watched_start_time is None:
                    self._watched_start_time = fields[19]
                elif self._watched_start_time != fields[19]:
                    raise ChannelClosed("Shared-memory session owner exited")
            except FileNotFoundError:
                raise ChannelClosed("Shared-memory session owner exited") from None
            except PermissionError:
                pass
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                raise ChannelClosed("Shared-memory session owner exited") from None
            except PermissionError:
                pass

    def _acquire(self, semaphore: int, timeout: int) -> bool:
        deadline = None if timeout == 0xFFFFFFFF else time.monotonic() + timeout / 1000
        while True:
            self._check_cancelled()
            if timeout == 0:
                result = self._libc.sem_trywait(semaphore)
            else:
                remaining = 0.05 if deadline is None else max(0, min(0.05, deadline - time.monotonic()))
                absolute_ns = time.time_ns() + int(remaining * 1_000_000_000)
                absolute = _Timespec(*divmod(absolute_ns, 1_000_000_000))
                result = self._libc.sem_timedwait(semaphore, ctypes.byref(absolute))
            if result == 0:
                self._check_cancelled()
                return True
            error = ctypes.get_errno()
            if error not in (errno.EAGAIN, errno.EINTR, errno.ETIMEDOUT):
                self._raise_oserror()
            if timeout == 0 or (deadline is not None and time.monotonic() >= deadline):
                return False

    def _release(self, key: str) -> None:
        if self._libc.sem_post(self._semaphores[key]) != 0:
            self._raise_oserror()

    def stop(self) -> None:
        with self._stop_lock:
            if not self._closed and self._stop is not None and not self._stop_requested:
                if self._libc.sem_post(self._stop) != 0:
                    self._raise_oserror()
                self._stop_requested = True

    def close(self) -> None:
        """Close only after all session reader/writer workers have stopped."""
        if self._closed:
            return
        self._closed = True
        if self._view is not None:
            self._view.close()
            self._view = None
        if self._pidfd is not None:
            os.close(self._pidfd)
            self._pidfd = None
        if self._stop is not None:
            self._libc.sem_close(self._stop)
            self._stop = None
        for handle in self._semaphores.values():
            self._libc.sem_close(handle)
        self._semaphores.clear()
        for kind, name in reversed(self._created_names):
            getattr(self._libc, f"{kind}_unlink")(name)
        self._created_names.clear()


if sys.platform.startswith("linux"):
    SharedMemorySession = _PosixSharedMemorySession
