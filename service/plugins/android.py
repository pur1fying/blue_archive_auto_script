"""Chaquopy worker services: process ownership without forking the host JVM.

Two private Android services run trusted Python in independent processes. Their
native bridge owns leases and process cleanup. This is not a security sandbox.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any

from .errors import PluginError, require

MAX_REQUEST = 131072
MAX_RESPONSE = 131072


def _runtime():
    """Resolve public Chaquopy APIs lazily, only inside the Android backend."""
    try:
        from java import jclass

        platform = jclass("com.chaquo.python.Python").getPlatform()
        application = platform.getApplication()
        root = Path(str(application.getCacheDir().getCanonicalPath())) / "baas-plugin-jobs"
        bridge = jclass("io.github.kiramei.baas_tauri.PluginWorkerBridge")
        return bridge, root
    except Exception:
        raise PluginError("ANDROID_WORKER_UNAVAILABLE", "This Android client does not provide the plugin worker service; update the client.") from None


def _prepare(root: Path, request: bytes) -> Path:
    require(not root.is_symlink(), "ANDROID_WORKER_UNAVAILABLE", "Android plugin job storage is unsafe.")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="job-", dir=root))
    try:
        # The APK helper loads this standard-library-only module directly. No
        # service imports, inherited backend objects or login environment.
        (directory / "worker.py").write_bytes(Path(__file__).with_name("worker.py").read_bytes())
        descriptor = os.open(directory / "request.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(request)
            stream.flush()
            os.fsync(stream.fileno())
        return directory
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise


def _result(directory: Path) -> bytes | None:
    path = directory / "result.json"
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_RESPONSE,
            "INVALID_RESULT", "Android plugin worker returned an unsafe or oversized result file.")
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "INVALID_RESULT", "Android plugin result is not a regular file.")
            content = stream.read(MAX_RESPONSE + 1)
    except OSError:
        raise PluginError("INVALID_RESULT", "Android plugin worker result could not be read.") from None
    require(len(content) <= MAX_RESPONSE, "RESULT_TOO_LARGE", "Android plugin worker output exceeds its limit.")
    return content


def _lease(content: Any) -> dict:
    try:
        require(isinstance(content, str) and len(content) <= 4096, "ANDROID_WORKER_FAILED", "Android plugin worker returned invalid startup data.")
        lease = json.loads(content)
        require(isinstance(lease, dict) and type(lease.get("slot")) is int
                and lease["slot"] in {0, 1} and isinstance(lease.get("token"), str)
                and 0 < len(lease["token"]) <= 128 and type(lease.get("pid")) is int
                and lease["pid"] > 1 and lease["pid"] != os.getpid(),
                "ANDROID_WORKER_FAILED", "Android plugin worker returned invalid ownership data.")
        return lease
    except (ValueError, TypeError, RecursionError):
        raise PluginError("ANDROID_WORKER_FAILED", "Android plugin worker could not start.") from None


class AndroidWorkerPool:
    def __init__(self):
        self._queue = None

    def _available(self):
        if self._queue is None:
            self._queue = asyncio.Queue()
            self._queue.put_nowait(0)
            self._queue.put_nowait(1)
        return self._queue

    async def run(self, job_id: str, package_dir: Path, request: bytes, registry: dict) -> bytes:
        require(isinstance(request, bytes) and 0 < len(request) <= MAX_REQUEST,
                "PAYLOAD_TOO_LARGE", "Android plugin request exceeds its size limit.")
        bridge, root = await asyncio.to_thread(_runtime)
        queue = self._available()
        slot = await queue.get()
        directory = None
        lease = None
        try:
            preparing = asyncio.create_task(asyncio.to_thread(_prepare, root, request))
            try:
                directory = await asyncio.shield(preparing)
            except asyncio.CancelledError:
                directory = await preparing
                raise
            starting = asyncio.create_task(asyncio.to_thread(bridge.start, slot, str(directory), str(package_dir)))
            try:
                raw = await asyncio.shield(starting)
            except asyncio.CancelledError:
                # A JVM call can finish after Python cancellation. Wait for its
                # bounded startup handshake, collect ownership, then stop it.
                lease = _lease(str(await starting))
                raise
            lease = _lease(str(raw))
            require(lease["slot"] == slot and type(lease.get("group")) is int and lease["group"] == lease["pid"],
                    "ANDROID_WORKER_FAILED", "Android plugin worker did not establish its owned process group.")
            registry[job_id] = lease
            while True:
                content = await asyncio.to_thread(_result, directory)
                if content is not None:
                    return content
                running = await asyncio.to_thread(bridge.status, slot, lease["token"], lease["pid"])
                if not running:
                    # The worker may have committed its atomic result immediately
                    # before exiting, between the two polling operations.
                    content = await asyncio.to_thread(_result, directory)
                    require(content is not None, "WORKER_EXITED", "Android plugin worker exited without a result.")
                    return content
                await asyncio.sleep(0.05)
        except PluginError:
            raise
        except asyncio.CancelledError:
            raise
        except Exception:
            raise PluginError("ANDROID_WORKER_FAILED", "Android plugin worker could not complete the action.") from None
        finally:
            try:
                if lease is not None:
                    await asyncio.to_thread(bridge.stop, slot, lease["token"], lease["pid"])
            finally:
                registry.pop(job_id, None)
                if directory is not None:
                    await asyncio.to_thread(shutil.rmtree, directory, True)
                queue.put_nowait(slot)
