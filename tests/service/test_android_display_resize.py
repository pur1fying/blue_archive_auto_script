from __future__ import annotations

import sys
from types import SimpleNamespace

from service.runtime import _AndroidDisplayResizeGuard


class _FakeDevice:
    def __init__(self, calls):
        self.calls = calls

    def shell(self, command: str):
        self.calls.append(command)
        if command == "wm size":
            return "Physical size: 1080x2400"
        return ""


class _FakeLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, message):
        self.warnings.append(message)


def test_android_display_guard_is_noop_outside_android(monkeypatch):
    monkeypatch.delenv("BAAS_ANDROID", raising=False)
    guard = _AndroidDisplayResizeGuard()

    guard.activate()
    guard.release()


def test_android_display_guard_does_not_resize_without_explicit_target(monkeypatch):
    calls = []

    def connect(target):
        assert target == "http://127.0.0.1:7912"
        return _FakeDevice(calls)

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.delenv("BAAS_ANDROID_WM_SIZE", raising=False)
    monkeypatch.delenv("BAAS_ANDROID_U2_SERIAL", raising=False)
    monkeypatch.setitem(sys.modules, "uiautomator2", SimpleNamespace(connect=connect))

    guard = _AndroidDisplayResizeGuard()
    guard.activate()
    guard.release()

    assert calls == []


def test_android_display_guard_sets_and_resets_explicit_size(monkeypatch):
    calls = []

    def connect(target):
        assert target == "http://127.0.0.1:7912"
        return _FakeDevice(calls)

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setenv("BAAS_ANDROID_WM_SIZE", "720x1280")
    monkeypatch.delenv("BAAS_ANDROID_U2_SERIAL", raising=False)
    monkeypatch.setitem(sys.modules, "uiautomator2", SimpleNamespace(connect=connect))

    guard = _AndroidDisplayResizeGuard()
    guard.activate()
    guard.release()

    assert calls == ["wm size", "wm size 720x1280", "wm size reset"]


def test_android_display_guard_uses_reference_count(monkeypatch):
    calls = []

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setenv("BAAS_ANDROID_WM_SIZE", "800x1280")
    monkeypatch.setenv("BAAS_ANDROID_U2_SERIAL", "http://localhost:7912")
    monkeypatch.setitem(
        sys.modules,
        "uiautomator2",
        SimpleNamespace(connect=lambda _target: _FakeDevice(calls)),
    )

    guard = _AndroidDisplayResizeGuard()
    guard.activate()
    guard.activate()
    guard.release()
    guard.release()

    assert calls == ["wm size", "wm size 800x1280", "wm size reset"]


def test_android_display_guard_force_restore_ignores_reference_count(monkeypatch):
    calls = []

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setitem(
        sys.modules,
        "uiautomator2",
        SimpleNamespace(connect=lambda _target: _FakeDevice(calls)),
    )

    guard = _AndroidDisplayResizeGuard()
    guard.activate()
    guard.activate()
    guard.force_restore()

    assert guard._active_count == 0
    assert calls == ["wm size reset"]


def test_android_display_guard_does_not_block_when_resize_fails(monkeypatch):
    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setenv("BAAS_ANDROID_WM_SIZE", "720x1280")

    def fail_shell(_command):
        raise RuntimeError("No adb exe could be found. Install adb on your system")

    monkeypatch.setattr(_AndroidDisplayResizeGuard, "_shell", staticmethod(fail_shell))

    logger = _FakeLogger()
    guard = _AndroidDisplayResizeGuard()

    guard.activate(logger)
    guard.release(logger)

    assert guard._active_count == 0
    assert "continue without resizing" in logger.warnings[0]
