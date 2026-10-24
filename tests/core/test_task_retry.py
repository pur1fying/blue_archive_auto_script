from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from core.Baas_thread import Baas_thread
from core.exception import FunctionCallTimeout, PackageIncorrect


def _thread():
    """Use the real solve method without initializing a device or task engine."""
    errors, recoveries, pushed = [], [], []
    thread = Baas_thread.__new__(Baas_thread)
    thread.flag_run = True
    thread.logger = SimpleNamespace(info=lambda message: None, error=errors.append)
    thread.deal_with_func_call_timeout = lambda: recoveries.append("timeout") or True
    thread.deal_with_package_incorrect = lambda package: recoveries.append(package) or True
    thread.push_and_log_error_msg = lambda *error: pushed.append(error)
    return thread, errors, recoveries, pushed


@pytest.mark.parametrize("failure", [FunctionCallTimeout(), PackageIncorrect("other.package")])
def test_solve_reports_exhausted_retries_and_returns_failure(monkeypatch, failure):
    thread, errors, recoveries, pushed = _thread()
    attempts = []

    def task(context):
        assert context is thread
        attempts.append(context)
        raise failure

    module = importlib.import_module("core.Baas_thread")
    monkeypatch.setitem(module.func_dict, "test_retry_task", task)

    assert thread.solve("test_retry_task") is False
    assert len(attempts) == 3
    assert len(recoveries) == 3  # Preserve the existing recovery after the last failure.
    assert len(errors) == 1
    assert "test_retry_task" in errors[0] and "3 attempts" in errors[0]
    assert pushed == []


def test_solve_succeeds_after_recovery_without_exhaustion_error(monkeypatch):
    thread, errors, recoveries, pushed = _thread()
    attempts = []

    def task(context):
        attempts.append(context)
        if len(attempts) == 1:
            raise FunctionCallTimeout()
        return True

    module = importlib.import_module("core.Baas_thread")
    monkeypatch.setitem(module.func_dict, "test_retry_task", task)

    assert thread.solve("test_retry_task") is True
    assert len(attempts) == 2
    assert recoveries == ["timeout"]
    assert errors == [] and pushed == []


def test_solve_keeps_immediate_recovery_failure_behavior(monkeypatch):
    thread, errors, _, pushed = _thread()
    thread.deal_with_func_call_timeout = lambda: False

    def task(context):
        raise FunctionCallTimeout()

    module = importlib.import_module("core.Baas_thread")
    monkeypatch.setitem(module.func_dict, "test_retry_task", task)

    assert thread.solve("test_retry_task") is False
    assert errors == []
    assert pushed == [("Function Call Timeout", "Failed to Restart Game when function call timeout")]


def test_solve_keeps_human_takeover_behavior(monkeypatch):
    thread, errors, recoveries, pushed = _thread()
    thread.flag_run = False

    def task(context):
        raise RuntimeError("stopped by user")

    module = importlib.import_module("core.Baas_thread")
    monkeypatch.setitem(module.func_dict, "test_retry_task", task)

    assert thread.solve("test_retry_task") is True
    assert errors == [] and recoveries == [] and pushed == []
