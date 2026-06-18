from __future__ import annotations

import asyncio
import shutil
import sys
import types
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from service.conf import ConfigPathError, ensure_safe_config_id, resolve_config_dir
from service.runtime import ServiceRuntime
from service.update.setup_io import read_setup_toml, write_setup_toml


def _workspace_tmp() -> Path:
    root = Path("tests/service/.tmp") / uuid.uuid4().hex
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def test_config_id_path_safety():
    assert ensure_safe_config_id("default_config") == "default_config"
    with pytest.raises(ConfigPathError):
        ensure_safe_config_id("../outside")
    with pytest.raises(ConfigPathError):
        resolve_config_dir(Path("config"), "..\\outside")


def test_remove_config_dir_stays_inside_config_root():
    root = _workspace_tmp()
    try:
        target = root / "config" / "default_config"
        target.mkdir(parents=True)
        (target / "config.json").write_text("{}", encoding="utf-8")

        target = resolve_config_dir(root / "config", "default_config")
        if target.exists():
            shutil.rmtree(target)

        assert not target.exists()
        with pytest.raises(ConfigPathError):
            resolve_config_dir(root / "config", "../outside")
    finally:
        _cleanup(root)


def test_runtime_status_snapshot_is_deep_copy():
    runtime = ServiceRuntime(Path("project"))
    runtime._statuses["default_config"] = {"nested": {"running": False}}

    snapshot = runtime.current_status()
    snapshot["default_config"]["nested"]["running"] = True

    assert runtime.current_status()["default_config"]["nested"]["running"] is False


def test_runtime_remove_config_uses_project_root():
    root = _workspace_tmp()
    try:
        target = root / "config" / "default_config"
        target.mkdir(parents=True)
        runtime = ServiceRuntime(root)

        asyncio.run(runtime.remove_config("default_config"))

        assert not target.exists()
    finally:
        _cleanup(root)


def test_runtime_remote_connection_skips_package_detection(monkeypatch):
    calls = {}
    session = SimpleNamespace(baas=object(), scrcpy_client=None)
    runtime = ServiceRuntime(Path("project"))

    async def fake_get_session(config_id):
        calls["config_id"] = config_id
        return session

    class FakeConnection:
        def __init__(self, baas, skip_package_detection=False):
            calls["baas"] = baas
            calls["skip_package_detection"] = skip_package_detection
            self.serial = "127.0.0.1:5555"

    class FakeAdb:
        def device(self, serial):
            calls["serial"] = serial
            return "adb-device"

    class FakeScrcpyClient:
        def __init__(self, device):
            calls["device"] = device

        async def init(self):
            calls["scrcpy_initialized"] = True
            return "scrcpy-client"

    fake_adbutils = types.ModuleType("adbutils")
    fake_adbutils.adb = FakeAdb()
    fake_adbutils.AdbDevice = object
    fake_adbutils.AdbError = RuntimeError
    fake_adbutils.AdbTimeout = TimeoutError
    fake_adbutils.ForwardItem = object
    fake_errors = types.ModuleType("adbutils.errors")
    fake_errors.AdbError = RuntimeError
    fake_errors.AdbTimeout = TimeoutError

    monkeypatch.setitem(sys.modules, "adbutils", fake_adbutils)
    monkeypatch.setitem(sys.modules, "adbutils.errors", fake_errors)

    import core.device.connection as connection_module
    import service.remote.scrcpy as scrcpy_module

    monkeypatch.setattr(runtime, "get_session", fake_get_session)
    monkeypatch.setattr(connection_module, "Connection", FakeConnection)
    monkeypatch.setattr(scrcpy_module, "ScrcpyClient", FakeScrcpyClient)

    client = asyncio.run(runtime.require_remote_("default_config"))

    assert client == "scrcpy-client"
    assert session.scrcpy_client == "scrcpy-client"
    assert calls == {
        "config_id": "default_config",
        "baas": session.baas,
        "skip_package_detection": True,
        "serial": "127.0.0.1:5555",
        "device": "adb-device",
        "scrcpy_initialized": True,
    }


def test_setup_toml_io_round_trip():
    root = _workspace_tmp()
    setup_path = root / "setup.toml"
    try:
        data, path = read_setup_toml(setup_path)
        data.setdefault("general", {})["mirrorc_cdk"] = "abc"
        write_setup_toml(data, path)
        loaded, _ = read_setup_toml(setup_path)

        assert loaded["general"]["mirrorc_cdk"] == "abc"
        assert loaded["general"]["channel"] == "stable"
        assert "General" not in loaded
    finally:
        _cleanup(root)


def test_setup_toml_reads_tauri_camel_case_paths():
    root = _workspace_tmp()
    setup_path = root / "setup.toml"
    try:
        setup_path.write_text(
            """
schema_version = 1

[general]
mirrorcCdk = "abc"
channel = "dev"
getRemoteShaMethod = "github"
forceLaunch = true

[paths]
baasRootPath = "D:/BAAS"
tmpPath = "cache"
toolkitPath = "tools"

[python]
runtimePath = "C:/Python/python.exe"
pythonVersion = "3.11.0"

[repositories]
mainSources = []
cppSources = []
""".strip(),
            encoding="utf-8",
        )

        loaded, _ = read_setup_toml(setup_path)

        assert loaded["general"]["mirrorc_cdk"] == "abc"
        assert loaded["general"]["channel"] == "dev"
        assert loaded["general"]["get_remote_sha_method"] == "github"
        assert loaded["general"]["force_launch"] is True
        assert loaded["paths"]["baas_root_path"] == "D:/BAAS"
        assert loaded["paths"]["tmp_path"] == "cache"
        assert loaded["paths"]["toolkit_path"] == "tools"
        assert loaded["python"]["runtime_path"] == "C:/Python/python.exe"
        assert loaded["python"]["python_version"] == "3.11.0"
    finally:
        _cleanup(root)
