from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace

import pytest

from service.runtime import ServiceRuntime


@pytest.mark.parametrize("requested,normalized", [("restart", "restart"), ("start_hard_task", "explore_hard_task")])
def test_single_task_accepts_canonical_and_legacy_names(tmp_path, monkeypatch, requested, normalized):
    async def scenario():
        runtime = ServiceRuntime(tmp_path)
        calls, updates = [], []
        completed = threading.Event()
        baas = SimpleNamespace(
            scheduler=object(), flag_run=False, logger=None,
            send=lambda *args: calls.append(args) or True,
        )
        runtime._sessions["bili"] = SimpleNamespace(baas=baas, thread=None)
        runtime._android_display_guard = SimpleNamespace(activate=lambda _: None, release=lambda _: None)
        monkeypatch.setattr("service.runtime._is_android_runtime", lambda: False)

        def status(_config_id, **changes):
            updates.append(changes)
            if changes.get("running") is False:
                completed.set()

        runtime._update_status = status
        result = await runtime.solve_task("bili", requested)
        assert await asyncio.to_thread(completed.wait, 2)
        assert result["task"] == normalized
        assert calls == [("solve", normalized)]
        assert updates[0]["current_task"] == requested
        assert updates[-1]["running"] is False
        assert updates[-1].get("exit_code") != 1

    asyncio.run(scenario())
