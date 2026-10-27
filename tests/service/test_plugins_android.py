"""Android adapter protocol tests. Real Chaquopy/process ownership runs on-device."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import threading
import time
import uuid

import pytest

from service.plugins import PluginError
from service.plugins import android
from service.plugins.manager import PluginManager
from service.plugins.worker import execute_request


REQUEST = json.dumps({"entrypoint": "main:run", "input": {}, "context": {"api_version": 1, "settings": {"answer": 42}}}).encode()


class Bridge:
    def __init__(self, result=None, running=True, delay=0):
        self.result = result
        self.running = running
        self.delay = delay
        self.started = []
        self.stopped = []
        self.entered = threading.Event()
        self.directories = []

    def start(self, slot, directory, package):
        self.entered.set()
        if self.delay:
            time.sleep(self.delay)
        lease = {"slot": slot, "token": str(uuid.uuid4()), "pid": os.getpid() + 1000 + slot, "group": os.getpid() + 1000 + slot}
        self.started.append(lease)
        root = Path(directory)
        self.directories.append(root)
        assert json.loads((root / "request.json").read_bytes())["entrypoint"] == "main:run"
        assert "def execute_request(" in (root / "worker.py").read_text()
        if callable(self.result):
            self.result(root, Path(package))
        elif self.result is not None:
            temporary = root / ".result.tmp"
            temporary.write_bytes(self.result)
            temporary.replace(root / "result.json")
        return json.dumps(lease)

    def status(self, slot, token, pid):
        return self.running

    def stop(self, slot, token, pid):
        lease = next((lease for lease in self.started if lease["slot"] == slot and lease["token"] == token and lease["pid"] == pid), None)
        assert lease is not None, "adapter attempted to stop a lease it does not own"
        self.stopped.append(lease)
        return True


def runtime(monkeypatch, tmp_path, bridge):
    cache = tmp_path / "jobs"
    monkeypatch.setattr(android, "_runtime", lambda: (bridge, cache))
    package = tmp_path / "package"
    package.mkdir()
    (package / "main.py").write_text("def run(context, inputs): return context['settings']")
    return android.AndroidWorkerPool(), cache, package


def test_android_worker_uses_atomic_files_and_shared_execution_protocol(tmp_path, monkeypatch):
    def result(directory, package):
        response = execute_request(str(package), json.loads((directory / "request.json").read_bytes()))
        temporary = directory / ".result.tmp"
        temporary.write_bytes(json.dumps(response).encode())
        temporary.replace(directory / "result.json")
    bridge = Bridge(result=result)
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    registry = {}
    response = asyncio.run(pool.run("job", package, REQUEST, registry))
    assert PluginManager._worker_result(response) == {"answer": 42}
    assert bridge.stopped == bridge.started and registry == {}
    assert list(cache.iterdir()) == []


def test_android_startup_cancellation_waits_for_owned_lease_then_stops_it(tmp_path, monkeypatch):
    bridge = Bridge(delay=0.12)
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    registry = {}

    async def scenario():
        task = asyncio.create_task(pool.run("job", package, REQUEST, registry))
        for _ in range(100):
            if bridge.entered.is_set():
                break
            await asyncio.sleep(0.001)
        assert bridge.entered.is_set()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(scenario())
    assert len(bridge.started) == 1 and bridge.stopped == bridge.started
    assert registry == {} and list(cache.iterdir()) == []


def test_android_timeout_reclaims_its_native_worker_and_job_files(tmp_path, monkeypatch):
    bridge = Bridge()
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    registry = {}

    async def scenario():
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(pool.run("job", package, REQUEST, registry), timeout=0.1)
    asyncio.run(scenario())
    assert len(bridge.started) == 1 and bridge.stopped == bridge.started
    assert registry == {} and list(cache.iterdir()) == []


def test_android_pool_only_runs_two_native_slots_and_cancels_queued_jobs(tmp_path, monkeypatch):
    bridge = Bridge()
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    registry = {}

    async def scenario():
        tasks = [asyncio.create_task(pool.run(str(index), package, REQUEST, registry)) for index in range(3)]
        deadline = asyncio.get_running_loop().time() + 5
        while len(registry) < 2 and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.005)
        assert {lease["slot"] for lease in bridge.started} == {0, 1}
        assert len(registry) == 2
        tasks[-1].cancel()
        await asyncio.gather(tasks[-1], return_exceptions=True)
        assert len(bridge.started) == 2
        for task in tasks[:-1]:
            task.cancel()
        await asyncio.gather(*tasks[:-1], return_exceptions=True)
    asyncio.run(scenario())
    assert len(bridge.stopped) == 2 and registry == {}
    assert list(cache.iterdir()) == []


@pytest.mark.parametrize("mode,code", [("crash", "WORKER_EXITED"), ("oversize", "INVALID_RESULT"), ("symlink", "INVALID_RESULT")])
def test_android_crashed_or_unsafe_result_still_releases_lease(tmp_path, monkeypatch, mode, code):
    def result(directory, package):
        if mode == "oversize":
            (directory / "result.json").write_bytes(b"x" * (android.MAX_RESPONSE + 1))
        elif mode == "symlink":
            private = tmp_path / "private"
            private.write_text("secret")
            (directory / "result.json").symlink_to(private)
    bridge = Bridge(result=result, running=mode != "crash")
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    with pytest.raises(PluginError) as error:
        asyncio.run(pool.run("job", package, REQUEST, {}))
    assert error.value.code == code and "secret" not in str(error.value)
    assert bridge.stopped == bridge.started and list(cache.iterdir()) == []


def test_android_request_limit_is_checked_before_launch(tmp_path, monkeypatch):
    bridge = Bridge()
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    with pytest.raises(PluginError) as error:
        asyncio.run(pool.run("job", package, b"x" * (android.MAX_REQUEST + 1), {}))
    assert error.value.code == "PAYLOAD_TOO_LARGE"
    assert bridge.started == [] and not cache.exists()


def test_android_manager_never_uses_a_jvm_executable_as_a_worker(tmp_path, monkeypatch):
    bridge = Bridge(result=b'{"ok":true,"result":{"answer":42}}')
    pool, cache, package = runtime(monkeypatch, tmp_path, bridge)
    monkeypatch.setenv("BAAS_ANDROID", "1")

    async def forbidden(*args, **kwargs):
        pytest.fail("embedded Android runtime tried to launch sys.executable")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    manager = PluginManager(tmp_path, None)
    manager._android_workers = pool
    result = asyncio.run(manager._compute({"id": "job", "plugin_id": "example.test", "config_id": "one"},
                                          {"directory": package}, {"entrypoint": "main:run"}, {}, {"answer": 42}))
    assert result == {"answer": 42} and bridge.stopped == bridge.started


def test_shared_worker_rejects_bad_entrypoints_and_redacts_exceptions(tmp_path):
    (tmp_path / "main.py").write_text("def run(context, inputs): raise ValueError('/private/password=secret')")
    response = execute_request(str(tmp_path), json.loads(REQUEST))
    assert response == {"ok": False, "code": "ACTION_FAILED", "message": "Plugin action failed."}
    bad = json.loads(REQUEST)
    bad["entrypoint"] = "../private:run"
    assert execute_request(str(tmp_path), bad)["ok"] is False
