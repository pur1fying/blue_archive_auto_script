from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import uuid
from zipfile import ZipFile

import pytest

from service.plugins import PluginError, PluginManager
from service.runtime import ServiceRuntime

EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}


def device_host(tmp_path):
    profile = tmp_path / "config/one"
    profile.mkdir(parents=True)
    (profile / "config.json").write_text('{"name":"original"}')
    (profile / "event.json").write_text('{}')
    package = tmp_path / "bundled/baas.test-task"
    package.mkdir(parents=True)
    data = {"schema_version": 1, "api_version": 1, "id": "baas.test-task", "version": "1.0.0",
            "name": "Device", "description": "Device task", "permissions": ["device.tasks"], "settings_schema": EMPTY,
            "actions": [{"id": "lesson", "name": "Lesson", "execution": "device_task", "task_name": "lesson", "input_schema": EMPTY}]}
    (package / "plugin.json").write_text(json.dumps(data))
    runtime = ServiceRuntime(tmp_path)
    runtime._plugin_manager = PluginManager(tmp_path, runtime, bundled_root=tmp_path / "bundled")
    release = threading.Event()
    entered = threading.Event()
    stops = []

    class Baas:
        logger = SimpleNamespace()
        scheduler = object()
        flag_run = True

        def send(self, command, task=None):
            if command == "stop":
                stops.append(task)
                self.flag_run = False
                release.set()
                return True
            assert (command, task) == ("solve", "lesson")
            entered.set()
            release.wait(timeout=5)
            return True

    session = SimpleNamespace(baas=Baas(), thread=None)
    runtime._sessions["one"] = session
    return runtime, release, entered, stops, session


async def start_job(runtime):
    await runtime.plugins.set_enabled("one", {"plugin_id": "baas.test-task", "enabled": True})
    return await runtime.plugins.run("one", {"plugin_id": "baas.test-task", "action_id": "lesson", "input": {}, "request_id": str(uuid.uuid4())})


def test_device_job_remains_running_until_its_actual_thread_exits(tmp_path):
    runtime, release, entered, stops, session = device_host(tmp_path)

    async def scenario():
        job = await start_job(runtime)
        for _ in range(100):
            if entered.is_set():
                break
            await asyncio.sleep(0.01)
        assert entered.is_set()
        assert (await runtime.plugins.get_job("one", job["id"]))["state"] == "running"
        assert (await runtime.solve_task("one", "lesson"))["status"] == "already-running"
        release.set()
        for _ in range(100):
            state = await runtime.plugins.get_job("one", job["id"])
            if state["state"] == "succeeded":
                break
            await asyncio.sleep(0.01)
        assert state["state"] == "succeeded" and state["result"]["completed"] is True
        assert stops == []
    asyncio.run(scenario())


def test_device_job_cancel_stops_owned_thread_and_never_stops_existing_scheduler(tmp_path):
    runtime, release, entered, stops, session = device_host(tmp_path)

    async def scenario():
        await runtime.solve_task("one", "lesson")
        job = await start_job(runtime)
        for _ in range(100):
            state = await runtime.plugins.get_job("one", job["id"])
            if state["state"] == "failed":
                break
            await asyncio.sleep(0.01)
        assert state["error"]["code"] == "DEVICE_BUSY"
        await runtime.plugins.cancel("one", job["id"])
        assert stops == [] and session.thread.is_alive()
        release.set()
        await asyncio.to_thread(session.thread.join, 1)
        release.clear()
        entered.clear()
        own = await start_job(runtime)
        for _ in range(100):
            if entered.is_set():
                break
            await asyncio.sleep(0.01)
        thread = session.thread
        assert (await runtime.plugins.cancel("one", own["id"]))["state"] == "cancelled"
        assert len(stops) == 1 and not thread.is_alive()
    asyncio.run(scenario())


def test_cancel_during_initialization_keeps_lock_and_prevents_late_task_start(tmp_path):
    runtime, release, entered, stops, session = device_host(tmp_path)
    init_started = None
    init_finished = None
    session.baas.scheduler = None

    async def initialize(config_id, baas):
        init_started.set()
        await init_finished.wait()
        baas.scheduler = object()

    runtime._initialize_baas = initialize

    async def scenario():
        nonlocal init_started, init_finished
        init_started = asyncio.Event()
        init_finished = asyncio.Event()
        job = await start_job(runtime)
        await init_started.wait()
        assert (await runtime.plugins.cancel("one", job["id"]))["state"] == "cancelled"
        assert runtime._async_lock().locked()
        init_finished.set()
        for _ in range(100):
            if not runtime._async_lock().locked():
                break
            await asyncio.sleep(0.01)
        assert not runtime._async_lock().locked()
        assert not entered.is_set() and session.thread is None
    asyncio.run(scenario())


def test_stop_all_tasks_reaps_compute_workers(tmp_path):
    runtime, release, entered, stops, session = device_host(tmp_path)
    package = tmp_path / "bundled/baas.test-task"
    data = json.loads((package / "plugin.json").read_text())
    data["permissions"] = ["compute"]
    data["actions"] = [{"id": "sleep", "name": "Sleep", "execution": "compute", "entrypoint": "main:run", "input_schema": EMPTY}]
    (package / "plugin.json").write_text(json.dumps(data))
    (package / "main.py").write_text("def run(context, inputs):\n import time\n time.sleep(30)")

    async def scenario():
        await runtime.plugins.set_enabled("one", {"plugin_id": "baas.test-task", "enabled": True})
        job = await runtime.plugins.run("one", {"plugin_id": "baas.test-task", "action_id": "sleep", "input": {}, "request_id": str(uuid.uuid4())})
        for _ in range(100):
            if runtime.plugins._processes:
                break
            await asyncio.sleep(0.01)
        assert runtime.plugins._processes
        await runtime.stop_all_tasks()
        assert runtime.plugins._processes == {}
        assert (await runtime.plugins.get_job("one", job["id"]))["state"] == "cancelled"
    asyncio.run(scenario())


def test_imported_profile_preserves_plugin_settings_but_discards_code_trust(tmp_path, monkeypatch):
    from service import runtime as runtime_module
    runtime = ServiceRuntime(tmp_path)
    (tmp_path / "config").mkdir()
    data = {"schema_version": 1, "plugins": {"example.test": {"enabled": True, "trusted_digest": "forged", "values": {"count": 5}, "revision": 4}}}
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as zipped:
        zipped.writestr("config.json", '{"name":"imported"}')
        zipped.writestr("event.json", '{}')
        zipped.writestr("plugins.json", json.dumps(data))
    monkeypatch.setattr(runtime_module, "ConfigInitializer", lambda _: SimpleNamespace(check_config=lambda _: None))
    imported = runtime._import_config_sync(buffer.getvalue())
    record = json.loads((tmp_path / "config" / imported["serial"] / "plugins.json").read_text())["plugins"]["example.test"]
    assert record == {"enabled": False, "values": {"count": 5}, "revision": 4}


def test_shipping_bundled_manifests_use_supported_host_contract(tmp_path):
    manager = PluginManager(tmp_path, SimpleNamespace())
    catalog = asyncio.run(manager.catalog())
    assert catalog["errors"] == []
    assert {p["id"] for p in catalog["plugins"]} >= {"baas.task-launcher"}


@pytest.mark.parametrize("member", ["./plugins.json", "folder/../plugins.json", "plugins.json.", "plugins.json ", "folder//plugins.json"])
def test_profile_import_rejects_aliases_that_could_bypass_trust_reset(tmp_path, member):
    runtime = ServiceRuntime(tmp_path)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as zipped:
        zipped.writestr("config.json", '{"name":"imported"}')
        zipped.writestr(member, '{"schema_version":1,"plugins":{}}')
    with pytest.raises(ValueError, match="unsafe archive path"):
        runtime._import_config_sync(buffer.getvalue())
    assert not (tmp_path / "config").exists()


def test_profile_import_uppercase_plugin_state_is_also_distrusted(tmp_path, monkeypatch):
    from service import runtime as runtime_module
    runtime = ServiceRuntime(tmp_path)
    (tmp_path / "config").mkdir()
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as zipped:
        zipped.writestr("config.json", '{"name":"imported"}')
        zipped.writestr("PLUGINS.JSON", json.dumps({"schema_version": 1, "plugins": {"example.test": {"enabled": True, "trusted_digest": "known", "values": {}}}}))
    monkeypatch.setattr(runtime_module, "ConfigInitializer", lambda _: SimpleNamespace(check_config=lambda _: None))
    result = runtime._import_config_sync(buffer.getvalue())
    state = json.loads((tmp_path / "config" / result["serial"] / "plugins.json").read_text())
    assert state["plugins"]["example.test"] == {"enabled": False, "values": {}}


def test_removed_profile_does_not_prevent_global_worker_cleanup(tmp_path):
    import shutil
    runtime, release, entered, stops, session = device_host(tmp_path)
    package = tmp_path / "bundled/baas.test-task"
    data = json.loads((package / "plugin.json").read_text())
    data["permissions"] = ["compute"]
    data["actions"] = [{"id": "sleep", "name": "Sleep", "execution": "compute", "entrypoint": "main:run", "input_schema": EMPTY}]
    (package / "plugin.json").write_text(json.dumps(data))
    (package / "main.py").write_text("def run(context, inputs):\n import time\n time.sleep(30)")

    async def scenario():
        await runtime.plugins.set_enabled("one", {"plugin_id": "baas.test-task", "enabled": True})
        await runtime.plugins.run("one", {"plugin_id": "baas.test-task", "action_id": "sleep", "input": {}, "request_id": str(uuid.uuid4())})
        for _ in range(100):
            if runtime.plugins._processes:
                break
            await asyncio.sleep(0.01)
        assert runtime.plugins._processes
        shutil.rmtree(tmp_path / "config/one")
        await runtime.stop_all_tasks()
        assert runtime.plugins._processes == {}
    asyncio.run(scenario())
