from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

from service.runtime import ServiceRuntime


def test_scheduler_failure_publishes_nonzero_exit_code():
    release = threading.Event()

    class FakeBaas:
        flag_run = True

        @staticmethod
        def init_all_data():
            return True

        @staticmethod
        def send(message):
            assert message == "start"
            release.wait(timeout=2)
            return False

    runtime = ServiceRuntime(Path("project"))
    session = SimpleNamespace(baas=FakeBaas(), thread=None)
    runtime._get_or_create_session = lambda _config_id: session

    asyncio.run(runtime.start_scheduler("default_config"))
    thread = session.thread
    release.set()
    thread.join(timeout=2)

    status = runtime.current_status()["default_config"]
    assert status["running"] is False
    assert status["exit_code"] == 1


def test_scheduler_normal_stop_does_not_publish_failure_exit_code():
    release = threading.Event()

    class FakeBaas:
        flag_run = False

        @staticmethod
        def init_all_data():
            return True

        @staticmethod
        def send(message):
            assert message == "start"
            release.wait(timeout=2)
            return True

    runtime = ServiceRuntime(Path("project"))
    session = SimpleNamespace(baas=FakeBaas(), thread=None)
    runtime._get_or_create_session = lambda _config_id: session

    asyncio.run(runtime.start_scheduler("default_config"))
    thread = session.thread
    release.set()
    thread.join(timeout=2)

    status = runtime.current_status()["default_config"]
    assert status["running"] is False
    assert status["exit_code"] is None


def test_single_task_failure_publishes_nonzero_exit_code():
    release = threading.Event()

    class FakeBaas:
        flag_run = True
        scheduler = object()

        @staticmethod
        def send(message, task):
            assert (message, task) == ("solve", "explore_normal_task")
            release.wait(timeout=2)
            return False

    runtime = ServiceRuntime(Path("project"))
    session = SimpleNamespace(baas=FakeBaas(), thread=None)
    runtime._get_or_create_session = lambda _config_id: session

    asyncio.run(runtime.solve_task("default_config", "start_normal_task"))
    thread = session.thread
    release.set()
    thread.join(timeout=2)

    status = runtime.current_status()["default_config"]
    assert status["running"] is False
    assert status["exit_code"] == 1
