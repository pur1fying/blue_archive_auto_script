from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace

import pytest

from service.runtime import ServiceRuntime


def _runtime(tmp_path, outcomes):
    runtime = ServiceRuntime(tmp_path)
    guard, calls, initialization_markers = [], [], []
    entered, finish = threading.Event(), threading.Event()
    baas = SimpleNamespace(scheduler=None, flag_run=False, logger=None)

    def initialize():
        initialization_markers.append(baas.scheduler)
        baas.scheduler = object()  # Real initialization sets this before connecting the device.
        baas.flag_run = True
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def send(*args):
        calls.append(args)
        entered.set()
        finish.wait(2)
        return True

    baas.init_all_data = initialize
    baas.send = send
    session = SimpleNamespace(baas=baas, thread=None)
    runtime._sessions["bili"] = session
    runtime._android_display_guard = SimpleNamespace(
        activate=lambda logger: guard.append("activate"),
        release=lambda logger: guard.append("release"),
    )
    return runtime, session, guard, calls, initialization_markers, entered, finish


async def _start(runtime, mode):
    if mode == "single":
        return await runtime.solve_task("bili", "restart")
    return await runtime.start_scheduler("bili")


@pytest.mark.parametrize("mode", ["single", "scheduler"])
@pytest.mark.parametrize("failure", [False, ConnectionResetError("ADB connection reset (10054)")])
def test_failed_initialization_does_not_run_task_and_next_attempt_reinitializes(tmp_path, mode, failure):
    async def scenario():
        runtime, session, guard, calls, markers, entered, finish = _runtime(tmp_path, [failure, True])
        expected = "initialization failed.*task was not started" if failure is False else "10054"
        with pytest.raises((RuntimeError, ConnectionResetError), match=expected):
            await _start(runtime, mode)

        assert session.thread is None
        assert session.baas.scheduler is None and session.baas.flag_run is False
        assert calls == [] and guard == ["activate", "release"]
        status = runtime.current_status()["bili"]
        assert status["running"] is False and status["is_flag_run"] is False
        assert status["exit_code"] == 1 and status["current_task"] is None

        await _start(runtime, mode)
        assert await asyncio.to_thread(entered.wait, 1)
        thread = session.thread
        finish.set()
        await asyncio.to_thread(thread.join, 2)
        assert not thread.is_alive()
        assert markers == [None, None]
        assert calls == ([("solve", "restart")] if mode == "single" else [("start",)])
        assert guard == ["activate", "release", "activate", "release"]
        assert runtime.current_status()["bili"]["exit_code"] is None

    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["single", "scheduler"])
def test_initialization_returning_none_remains_compatible(tmp_path, mode):
    async def scenario():
        runtime, session, guard, calls, _, entered, finish = _runtime(tmp_path, [None])
        await _start(runtime, mode)
        assert await asyncio.to_thread(entered.wait, 1)
        thread = session.thread
        finish.set()
        await asyncio.to_thread(thread.join, 2)
        assert not thread.is_alive()
        assert calls and guard == ["activate", "release"]
        assert runtime.current_status()["bili"]["exit_code"] is None

    asyncio.run(scenario())
