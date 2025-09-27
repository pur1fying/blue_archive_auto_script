from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet
from core.device import emulator_manager
from main import Main

from .broadcast import BroadcastChannel

_TASK_ALIAS = {
    "start_hard_task": "explore_hard_task",
    "start_normal_task": "explore_normal_task",
    "start_fhx": "de_clothes",
    "start_main_story": "main_story",
    "start_group_story": "group_story",
    "start_mini_story": "mini_story",
    "start_explore_activity_story": "explore_activity_story",
    "start_explore_activity_mission": "explore_activity_mission",
    "start_explore_activity_challenge": "explore_activity_challenge",
}


class _SignalHook:
    def __init__(self, callback) -> None:
        self._callback = callback

    def emit(self, payload):  # noqa: ANN001 - Qt compatible signature
        self._callback(payload)


class ServiceRuntime:
    """Coordinates Baas_thread lifecycle and exposes async-friendly APIs."""

    def __init__(self, project_root: Path, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._project_root = project_root
        self._loop = loop
        self._status_bus = BroadcastChannel(loop)
        self._status_lock = threading.Lock()
        self._status: Dict[str, Any] = {
            "running": False,
            "flag_run": False,
            "config_id": None,
            "button": None,
            "current_task": None,
            "waiting_tasks": [],
            "timestamp": time.time(),
        }
        self._lock = asyncio.Lock()
        self._main: Optional[Main] = None
        self._baas: Optional[Baas_thread] = None
        self._baas_thread: Optional[threading.Thread] = None
        self._active_config_id: Optional[str] = None
        self._button_signal: Optional[_SignalHook] = None
        self._update_signal: Optional[_SignalHook] = None
        self._exit_signal: Optional[_SignalHook] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._status_bus.set_loop(loop)

    # ------------------------------------------------------------------
    # public utility accessors
    # ------------------------------------------------------------------
    def get_main_log_queue(self):
        self._ensure_main_sync()
        assert self._main is not None
        return self._main.logger.log_collector

    def get_baas_log_queue(self) -> Tuple[Optional[Any], Optional[str]]:
        if self._baas is None or self._active_config_id is None:
            return None, None
        return self._baas.logger.log_collector, f"config:{self._active_config_id}"

    def get_active_config_id(self) -> Optional[str]:
        return self._active_config_id

    def current_status(self) -> Dict[str, Any]:
        with self._status_lock:
            return dict(self._status)

    async def subscribe_status(self) -> asyncio.Queue:
        if self._loop is None:
            raise RuntimeError("ServiceRuntime loop is not configured")
        return self._status_bus.subscribe()

    def unsubscribe_status(self, queue_obj: asyncio.Queue) -> None:
        self._status_bus.unsubscribe(queue_obj)

    # ------------------------------------------------------------------
    # lifecycle helpers
    # ------------------------------------------------------------------
    def _ensure_main_sync(self) -> None:
        if self._main is not None:
            return
        self._main = Main(ocr_needed=["en-us", "zh-cn"], jsonify=True)

    async def _ensure_main(self) -> None:
        await asyncio.get_running_loop().run_in_executor(None, self._ensure_main_sync)

    async def ensure_ready(self) -> None:
        await self._ensure_main()

    def _ensure_baas(self, config_id: str) -> None:
        self._ensure_main_sync()
        assert self._main is not None
        config = ConfigSet(config_dir=config_id)
        self._button_signal = _SignalHook(self._handle_button_signal)
        self._update_signal = _SignalHook(self._handle_update_signal)
        self._exit_signal = _SignalHook(self._handle_exit_signal)
        self._baas = Baas_thread(
            config,
            None,
            self._button_signal,
            self._update_signal,
            self._exit_signal,
            jsonify=True,
        )
        self._baas.set_ocr(self._main.ocr)
        self._active_config_id = config_id
        self._update_status(config_id=config_id, flag_run=False, running=False)

    async def start_scheduler(self, config_id: str) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        async with self._lock:
            if self._baas is None or self._active_config_id != config_id:
                await loop.run_in_executor(None, self._ensure_baas, config_id)
            assert self._baas is not None
            if self._baas_thread and self._baas_thread.is_alive():
                return {"status": "already-running", "config_id": self._active_config_id}
            init_ok = await loop.run_in_executor(None, self._baas.init_all_data)
            if not init_ok:
                raise RuntimeError("Baas_thread initialization failed")
            self._baas_thread = threading.Thread(
                target=self._baas.send,
                args=("start",),
                name=f"baas-scheduler-{config_id}",
                daemon=True,
            )
            self._baas_thread.start()
            self._update_status(running=True, flag_run=True)
            return {"status": "started", "config_id": self._active_config_id}

    async def stop_scheduler(self) -> Dict[str, Any]:
        async with self._lock:
            if self._baas is None:
                return {"status": "idle"}
            self._baas.send("stop")
            thread = self._baas_thread
            self._baas_thread = None
        if thread and thread.is_alive():
            thread.join(timeout=10.0)
        self._update_status(running=False, flag_run=False)
        return {"status": "stopped", "config_id": self._active_config_id}

    async def solve_task(self, task_name: str) -> Dict[str, Any]:
        if task_name in _TASK_ALIAS:
            task_name = _TASK_ALIAS[task_name]
        loop = asyncio.get_running_loop()
        async with self._lock:
            if self._baas is None:
                raise RuntimeError("Baas_thread is not initialized")
            baas = self._baas

        def _call() -> bool:
            return bool(baas.send("solve", task_name))

        result = await loop.run_in_executor(None, _call)
        return {"status": "ok", "task": task_name, "result": result}

    async def detect_adb(self) -> List[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, emulator_manager.autosearch)

    # ------------------------------------------------------------------
    # signal handlers
    # ------------------------------------------------------------------
    def _handle_button_signal(self, payload: Any) -> None:
        self._update_status(button=payload)

    def _handle_update_signal(self, payload: Any) -> None:
        if isinstance(payload, list) and payload:
            current = payload[0]
            waiting = list(payload[1:])
        else:
            current = None
            waiting = []
        self._update_status(current_task=current, waiting_tasks=waiting)

    def _handle_exit_signal(self, payload: Any) -> None:
        self._update_status(running=False, flag_run=False, exit_code=payload)

    def _update_status(self, **changes: Any) -> None:
        with self._status_lock:
            self._status.update(changes)
            self._status["timestamp"] = time.time()
            snapshot = dict(self._status)
        if self._loop:
            self._status_bus.publish_threadsafe(snapshot)
