from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from service.api import commands
from service.types import CommandMessage


class _Runtime:
    def __init__(self) -> None:
        self.calls = []

    def current_status(self):
        return {"default_config": {"running": False}}

    async def solve_task(self, config_id, task_name, set_log=None):
        self.calls.append(("solve_task", config_id, task_name, bool(set_log)))
        return {"status": "ok", "task": task_name, "result": 0}

    async def detect_adb(self):
        return ["127.0.0.1:5555"]


def _cmd(command: str, **kwargs) -> CommandMessage:
    return CommandMessage(type="command", command=command, timestamp=1.0, **kwargs)


def test_execute_status_command(monkeypatch):
    runtime = _Runtime()
    monkeypatch.setattr(commands, "context", SimpleNamespace(runtime=runtime))

    result = asyncio.run(commands.execute_command(_cmd("status")))

    assert result == {"status": "ok", "data": {"default_config": {"running": False}}}


def test_execute_start_alias_dispatches_to_runtime(monkeypatch):
    runtime = _Runtime()
    fake_context = SimpleNamespace(runtime=runtime, ensure_runtime_logger_attached=lambda: None)
    monkeypatch.setattr(commands, "context", fake_context)

    result = asyncio.run(commands.execute_command(_cmd("start_normal_task", config_id="default_config")))

    assert result == {"status": "ok", "data": {"status": "ok", "task": "start_normal_task", "result": 0}}
    assert runtime.calls == [("solve_task", "default_config", "start_normal_task", True)]


def test_execute_detect_adb_envelope(monkeypatch):
    runtime = _Runtime()
    monkeypatch.setattr(commands, "context", SimpleNamespace(runtime=runtime))

    result = asyncio.run(commands.execute_command(_cmd("detect_adb")))

    assert result == {"status": "ok", "data": {"addresses": ["127.0.0.1:5555"]}}


def test_execute_unsupported_command_raises(monkeypatch):
    monkeypatch.setattr(commands, "context", SimpleNamespace(runtime=_Runtime()))

    with pytest.raises(ValueError, match="Unsupported command"):
        asyncio.run(commands.execute_command(_cmd("unknown")))
