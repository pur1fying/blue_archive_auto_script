from __future__ import annotations

import asyncio
import copy
import io
import json
import os
from pathlib import Path
import signal
import stat
from types import SimpleNamespace
import uuid
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import psutil

import pytest

from service.plugins import PluginError, PluginManager
from service.plugins.schema import validate_manifest

EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}


def manifest(plugin_id="example.test", timeout=3):
    return {"schema_version": 1, "api_version": 1, "id": plugin_id, "version": "1.0.0",
            "name": {"en": "Test", "zh": "测试"}, "description": "Test plugin", "permissions": ["compute"],
            "settings_schema": {"type": "object", "properties": {"count": {"type": "integer", "default": 2, "minimum": 0}}, "additionalProperties": False},
            "actions": [{"id": "run", "name": "Run", "execution": "compute", "entrypoint": "main:run", "input_schema": EMPTY, "timeout_seconds": timeout}]}


def profile(root, name="one"):
    path = root / "config" / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "config.json").write_text('{"name":"test"}')
    (path / "event.json").write_text('{}')
    return path


def package(root, source="def run(context, inputs): return context['settings']", data=None):
    data = data or manifest()
    folder = root / "plugins" / data["id"]
    folder.mkdir(parents=True)
    (folder / "plugin.json").write_text(json.dumps(data))
    (folder / "main.py").write_text(source)
    return folder


def host(tmp_path):
    profile(tmp_path)
    return PluginManager(tmp_path, SimpleNamespace(), bundled_root=tmp_path / "bundled")


async def enabled(manager, plugin_id="example.test"):
    return await manager.set_enabled("one", {"plugin_id": plugin_id, "enabled": True, "trust_code": True})


async def run(manager, plugin_id="example.test", **kwargs):
    return await manager.run("one", {"plugin_id": plugin_id, "action_id": "run", "input": {}, "request_id": str(uuid.uuid4()), **kwargs})


async def finish(manager, job):
    for _ in range(200):
        state = await manager.get_job("one", job["id"])
        if state["state"] not in {"queued", "running"}:
            return state
        await asyncio.sleep(0.02)
    pytest.fail("Plugin job did not settle")


def test_discovery_never_imports_disabled_external_code_and_trust_is_per_profile(tmp_path):
    marker = tmp_path / "imported"
    package(tmp_path, f"from pathlib import Path\nPath({str(marker)!r}).touch()\ndef run(context, inputs): return True")
    manager = host(tmp_path)
    profile(tmp_path, "two")

    async def scenario():
        catalog = await manager.catalog("one")
        assert catalog["plugins"][0]["enabled"] is False
        assert catalog["plugins"][0]["trusted"] is False
        assert not marker.exists()
        with pytest.raises(PluginError, match="Enable and trust"):
            await run(manager)
        with pytest.raises(PluginError) as error:
            await manager.set_enabled("one", {"plugin_id": "example.test", "enabled": True})
        assert error.value.code == "TRUST_REQUIRED"
        await enabled(manager)
        assert not marker.exists()
        assert (await manager.catalog("two"))["plugins"][0]["enabled"] is False
        assert (await finish(manager, await run(manager)))["result"] is True
        assert marker.exists()
    asyncio.run(scenario())


def test_settings_atomic_revision_defaults_and_config_boundaries(tmp_path):
    package(tmp_path)
    manager = host(tmp_path)
    profile(tmp_path, "two")

    async def scenario():
        assert (await manager.settings("one", "example.test"))["values"] == {"count": 2}
        result = await manager.update_settings("one", {"plugin_id": "example.test", "revision": 0, "values": {"count": 5}})
        assert result["revision"] == 1
        assert json.loads((tmp_path / "config/one/plugins.json").read_text())["plugins"]["example.test"]["values"] == {"count": 5}
        for values, revision, code in [({"count": 6}, 0, "REVISION_CONFLICT"), ({"count": True}, 1, "INVALID_SETTINGS"), ({"count": 6, "unknown": True}, 1, "INVALID_SETTINGS")]:
            with pytest.raises(PluginError) as exc:
                await manager.update_settings("one", {"plugin_id": "example.test", "revision": revision, "values": values})
            assert exc.value.code == code
        assert (await manager.settings("two", "example.test"))["values"] == {"count": 2}
        for config_id in ("../one", "one/../one", "missing", "one\\other", " one", "one ", " one "):
            with pytest.raises(PluginError):
                await manager.settings(config_id, "example.test")
        outside = tmp_path / "outside.json"
        outside.write_text("private")
        (tmp_path / "config/one/plugins.json").unlink()
        (tmp_path / "config/one/plugins.json").symlink_to(outside)
        with pytest.raises(PluginError):
            await manager.settings("one", "example.test")
        assert outside.read_text() == "private"
    asyncio.run(scenario())


def test_changed_package_loses_trust_and_duplicate_builtin_id_is_blocked(tmp_path):
    folder = package(tmp_path)
    manager = host(tmp_path)

    async def scenario():
        await enabled(manager)
        (folder / "main.py").write_text("def run(context, inputs): return 'changed'")
        descriptor = (await manager.catalog("one"))["plugins"][0]
        assert descriptor["enabled"] is False and descriptor["trusted"] is False
        with pytest.raises(PluginError):
            await run(manager)
        builtin = tmp_path / "bundled/example.test"
        builtin.mkdir(parents=True)
        (builtin / "plugin.json").write_text(json.dumps(manifest()))
        assert (await manager.catalog("one"))["plugins"][0]["error"]["code"] == "DUPLICATE_PLUGIN"
        with pytest.raises(PluginError) as exc:
            await enabled(manager)
        assert exc.value.code == "DUPLICATE_PLUGIN"
    asyncio.run(scenario())


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(api_version=2),
    lambda d: d.update(schema_version=2),
    lambda d: d.update(permissions=["shell"]),
    lambda d: d["settings_schema"].update(additionalProperties=True),
    lambda d: d["actions"][0].update(execution="shell"),
    lambda d: d["actions"][0].update(entrypoint="../outside:run"),
    lambda d: d.update(contributions={"script": "alert(1)"}),
    lambda d: d.update(id="../test"),
])
def test_manifest_unknown_versions_and_capabilities_fail_closed(mutate):
    data = manifest()
    mutate(data)
    with pytest.raises(PluginError):
        validate_manifest(data)


def test_job_idempotency_profile_isolation_and_finite_result(tmp_path):
    package(tmp_path)
    manager = host(tmp_path)
    profile(tmp_path, "two")

    async def scenario():
        await enabled(manager)
        request_id = str(uuid.uuid4())
        job = await run(manager, request_id=request_id)
        again = await run(manager, request_id=request_id)
        assert job["id"] == again["id"]
        assert (await finish(manager, job))["result"] == {"count": 2}
        with pytest.raises(PluginError) as exc:
            await manager.get_job("two", job["id"])
        assert exc.value.code == "JOB_NOT_FOUND"
        await manager.stop_all()
        assert manager._processes == {}
    asyncio.run(scenario())


@pytest.mark.parametrize("source,code", [
    ("def run(context, inputs): raise RuntimeError('/private/key=secret')", "ACTION_FAILED"),
    ("def run(context, inputs): return 'x'*70000", "RESULT_TOO_LARGE"),
    ("def run(context, inputs): return float('nan')", "ACTION_FAILED"),
    ("def run(context, inputs):\n import os\n os._exit(7)", "WORKER_EXITED"),
])
def test_worker_failures_are_bounded_and_redacted(tmp_path, source, code):
    package(tmp_path, source)
    manager = host(tmp_path)

    async def scenario():
        await enabled(manager)
        result = await finish(manager, await run(manager))
        assert result["state"] == "failed"
        assert result["error"]["code"] == code
        assert "private" not in json.dumps(result) and "secret" not in json.dumps(result)
        assert manager._processes == {}
    asyncio.run(scenario())


@pytest.mark.parametrize("cancel", [False, True])
def test_timeout_and_cancel_reap_real_worker_and_its_children(tmp_path, cancel):
    marker = tmp_path / "worker.json"
    source = f"""def run(context, inputs):
 import os, subprocess, sys, time, json
 child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
 with open({str(marker)!r}, 'w') as stream: json.dump([os.getpid(),child.pid],stream)
 time.sleep(30)
"""
    package(tmp_path, source, manifest(timeout=3 if cancel else 0.3))
    manager = host(tmp_path)

    async def scenario():
        await enabled(manager)
        job = await run(manager)
        for _ in range(100):
            if marker.exists():
                break
            await asyncio.sleep(0.01)
        assert marker.exists()
        if cancel:
            with pytest.raises(PluginError) as exc:
                await manager.uninstall("example.test")
            assert exc.value.code == "PLUGIN_BUSY"
            state = await manager.cancel("one", job["id"])
            assert state["state"] == "cancelled"
        else:
            state = await finish(manager, job)
            assert state["error"]["code"] == "ACTION_TIMEOUT"
        assert manager._processes == {}
        worker, child = json.loads(marker.read_text())
        # A killed orphan can remain as a zombie until its OS parent reaps it.
        for process_id in (worker, child):
            for _ in range(100):
                try:
                    process = psutil.Process(process_id)
                    if process.status() == psutil.STATUS_ZOMBIE:
                        break
                except psutil.NoSuchProcess:
                    break
                await asyncio.sleep(0.01)
            else:
                pytest.fail("Cancelled plugin process or descendant is still alive")
    asyncio.run(scenario())


def archive(files):
    data = io.BytesIO()
    with ZipFile(data, "w", ZIP_DEFLATED) as zipped:
        for name, contents in files.items():
            zipped.writestr(name, contents)
    return data.getvalue()


def test_install_does_not_import_and_uninstall_clears_trust(tmp_path):
    manager = host(tmp_path)
    marker = tmp_path / "imported"
    data = archive({"plugin.json": json.dumps(manifest()), "main.py": f"open({str(marker)!r},'w').write('executed')"})

    async def scenario():
        installed = await manager.install(data)
        assert installed["trusted"] is False and installed["enabled"] is False
        assert not marker.exists()
        await enabled(manager)
        await manager.uninstall("example.test")
        assert not (tmp_path / "plugins/example.test").exists()
        assert "example.test" not in json.loads((tmp_path / "config/one/plugins.json").read_text())["plugins"]
    asyncio.run(scenario())


@pytest.mark.parametrize("name", ["../escaped", "/absolute", "a/../../escaped", "a\\..\\escaped", "C:/escaped", "__pycache__/main.pyc", "./main.py", "main.py.", "dir//file", "aux.py"])
def test_install_rejects_zip_traversal_and_bytecode(tmp_path, name):
    manager = host(tmp_path)
    with pytest.raises(PluginError) as exc:
        asyncio.run(manager.install(archive({name: "bad", "plugin.json": json.dumps(manifest()), "main.py": ""})))
    assert exc.value.code == "UNSAFE_ARCHIVE"
    assert not (tmp_path / "escaped").exists()
    assert list((tmp_path / "plugins").iterdir()) == []


def test_install_rejects_symbolic_links_and_inflated_packages(tmp_path):
    manager = host(tmp_path)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as zipped:
        link = ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        zipped.writestr(link, "../private")
    with pytest.raises(PluginError) as exc:
        asyncio.run(manager.install(buffer.getvalue()))
    assert exc.value.code == "UNSAFE_ARCHIVE"
    with pytest.raises(PluginError) as exc:
        asyncio.run(manager.install(archive({"huge": "x" * (33 * 1024 * 1024)})))
    assert exc.value.code == "PACKAGE_TOO_LARGE"


def test_one_corrupt_manifest_does_not_break_catalog_of_valid_plugins(tmp_path):
    package(tmp_path)
    bad = manifest("example.overflow")
    bad["settings_schema"]["properties"]["count"]["default"] = 10 ** 400
    package(tmp_path, data=bad)
    manager = host(tmp_path)
    catalog = asyncio.run(manager.catalog())
    assert [p["id"] for p in catalog["plugins"]] == ["example.test"]
    assert catalog["errors"][0]["plugin_id"] == "example.overflow"


def test_cancel_queued_job_never_spawns_and_queue_capacity_is_enforced(tmp_path):
    package(tmp_path, "def run(context, inputs):\n import time\n time.sleep(30)")
    manager = host(tmp_path)

    async def scenario():
        await enabled(manager)
        jobs = [await run(manager) for _ in range(8)]
        with pytest.raises(PluginError) as exc:
            await run(manager)
        assert exc.value.code == "JOB_QUEUE_FULL"
        queued = await manager.get_job("one", jobs[-1]["id"])
        assert queued["state"] == "queued"
        assert (await manager.cancel("one", queued["id"]))["state"] == "cancelled"
        assert queued["id"] not in manager._processes
        await manager.stop_all()
        assert manager._processes == {} and manager._tasks == {}
    asyncio.run(scenario())


def test_zip_implicit_directories_count_toward_package_limit(tmp_path):
    manager = host(tmp_path)
    files = {f"d{index}/child/file.txt": "x" for index in range(100)}
    with pytest.raises(PluginError) as exc:
        asyncio.run(manager.install(archive(files)))
    assert exc.value.code == "PACKAGE_TOO_LARGE"
    assert list((tmp_path / "plugins").iterdir()) == []


def test_slow_discovery_does_not_block_the_service_event_loop(tmp_path, monkeypatch):
    import time
    package(tmp_path)
    manager = host(tmp_path)
    discover = manager._discover
    entered = __import__("threading").Event()

    def slow_discover():
        entered.set()
        time.sleep(0.15)
        return discover()

    monkeypatch.setattr(manager, "_discover", slow_discover)

    async def scenario():
        task = asyncio.create_task(manager.catalog("one"))
        for _ in range(50):
            if entered.is_set():
                break
            await asyncio.sleep(0.001)
        assert entered.is_set()
        ticks = 0
        while not task.done():
            ticks += 1
            await asyncio.sleep(0.005)
        assert ticks >= 3
        assert (await task)["errors"] == []
    asyncio.run(scenario())
