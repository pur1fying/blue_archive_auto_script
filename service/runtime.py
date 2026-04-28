from __future__ import annotations

import asyncio
import datetime
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from adbutils import adb

from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet
from core.device import emulator_manager
from core.device.connection import Connection
from main import Main
from .broadcast import BroadcastChannel
from .lib.scrcpy import ScrcpyClient
from .utils import *

_TASK_ALIAS = {
    "start_hard_task"                 : "explore_hard_task",
    "start_normal_task"               : "explore_normal_task",
    "start_fhx"                       : "de_clothes",
    "start_main_story"                : "main_story",
    "start_group_story"               : "group_story",
    "start_mini_story"                : "mini_story",
    "start_explore_activity_story"    : "explore_activity_story",
    "start_explore_activity_mission"  : "explore_activity_mission",
    "start_explore_activity_challenge": "explore_activity_challenge",
}


class _SignalHook:
    def __init__(self, callback) -> None:
        self._callback = callback

    def emit(self, payload):  # noqa: ANN001 - Qt compatible signature
        self._callback(payload)


def _default_status(config_id: str) -> Dict[str, Any]:
    return {
        "config_id"    : config_id,
        "running"      : False,
        "is_flag_run"  : False,
        "button"       : None,
        "current_task" : None,
        "waiting_tasks": [],
        "exit_code"    : None,
        "timestamp"    : time.time(),
    }


@dataclass
class ConfigSession:
    config_id: str
    config_set: ConfigSet
    baas: Baas_thread
    button_signal: _SignalHook
    update_signal: _SignalHook
    exit_signal: _SignalHook
    scrcpy_client: ScrcpyClient = None
    thread: Optional[threading.Thread] = None
    status: Dict[str, Any] = field(default_factory=dict)


class ServiceRuntime:
    """Coordinates Baas_thread lifecycle and exposes async-friendly APIs."""

    def __init__(self, project_root: Path, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._project_root = project_root
        self._loop = loop
        self._status_bus = BroadcastChannel(loop)
        self._status_lock = threading.Lock()
        self._sessions: Dict[str, ConfigSession] = {}
        self._statuses: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._main: Optional[Main] = None
        self._baas: Optional[Baas_thread] = None
        self._baas_thread: Optional[threading.Thread] = None
        self._active_config_id: Optional[str] = None
        self._update_signal: Optional[_SignalHook] = None
        self._exit_signal: Optional[_SignalHook] = None
        self.is_all_data_initialized: bool = False

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

    def init_all_data(self):
        assert self._main is not None
        self._ensure_config()
        status = self._main.init_all_data()
        if status:
            self._status_bus.publish_threadsafe({
                "is_all_data_initialized": True
            })
            self.is_all_data_initialized = True

    def get_log_sources(self) -> List[Tuple[Any, str]]:
        sources: List[Tuple[Any, str]] = []
        for session in self._sessions.values():
            sources.append((session.baas.logger.log_collector, f"config:{session.config_id}"))
        return sources

    def current_status(self) -> Dict[str, Dict[str, Any]]:
        with self._status_lock:
            return {cid: dict(status) for cid, status in self._statuses.items()}

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

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
        self._main = Main(ocr_needed=["en-us", "zh-cn"], jsonify=True, lazy_data=True)

    async def _ensure_main(self) -> None:
        await asyncio.get_running_loop().run_in_executor(None, self._ensure_main_sync)  # type: ignore

    @staticmethod
    def _ensure_config() -> None:
        config_dir_list = []
        for _dir_ in os.listdir('./config'):
            if os.path.isdir(f'./config/{_dir_}'):
                files = os.listdir(f'./config/{_dir_}')
                if 'config.json' in files:
                    check_config(_dir_)
        if len(config_dir_list) == 0:
            check_config('default_config')

    async def ensure_ready(self) -> None:
        await self._ensure_main()

    def _get_or_create_session(self, config_id: str) -> ConfigSession:
        session = self._sessions.get(config_id)
        if session is not None:
            return session
        self._ensure_main_sync()
        assert self._main is not None
        config = ConfigSet(config_dir=config_id)
        button = _SignalHook(lambda payload: self._handle_button_signal(config_id, payload))
        update = _SignalHook(lambda payload: self._handle_update_signal(config_id, payload))
        exit_signal = _SignalHook(lambda payload: self._handle_exit_signal(config_id, payload))
        baas = Baas_thread(
            config,
            None,
            button,
            update,
            exit_signal,
            jsonify=True,
        )
        baas.set_ocr(self._main.ocr)
        status = _default_status(config_id)
        session = ConfigSession(
            config_id=config_id,
            config_set=config,
            baas=baas,
            button_signal=button,
            update_signal=update,
            exit_signal=exit_signal,
            status=status,
        )
        self._sessions[config_id] = session
        with self._status_lock:
            self._statuses[config_id] = status
        self._publish_status(config_id)
        return session

    async def get_session(self, config_id: str):
        async with self._lock:
            session = self._sessions.get(config_id)
            if session is None:
                session = self._get_or_create_session(config_id)
        return session

    async def start_scheduler(self, config_id: str, set_log=None) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        async with self._lock:
            session = self._get_or_create_session(config_id)
            if set_log: set_log()
            if session.thread and session.thread.is_alive():
                return {"status": "already-running", "config_id": config_id}
            init_ok = await loop.run_in_executor(None, session.baas.init_all_data)  # type: ignore
            if not init_ok:
                raise RuntimeError("Baas_thread initialization failed")

            def runner() -> None:
                try:
                    session.baas.send("start")
                finally:
                    session.thread = None
                    self._update_status(config_id, running=False, is_flag_run=session.baas.flag_run, current_task=None,
                                        waiting_tasks=[])

            thread = threading.Thread(
                target=runner,
                name=f"baas-scheduler-{config_id}",
                daemon=True,
            )
            session.thread = thread
            thread.start()
            self._update_status(config_id, running=True, is_flag_run=True, exit_code=None, current_task=None,
                                waiting_tasks=[])
            return {"status": "started", "config_id": config_id}

    async def stop_scheduler(self, config_id: str) -> Dict[str, Any]:
        async with self._lock:
            session = self._sessions.get(config_id)
            if session is None:
                return {"status": "unknown-config", "config_id": config_id}
            if not session.thread:
                self._update_status(config_id, running=False, is_flag_run=False, current_task=None, waiting_tasks=[])
                return {"status": "stopped", "config_id": config_id}
            session.baas.send("stop")
            thread = session.thread
            session.thread = None
        if thread and thread.is_alive():
            thread.join(timeout=10.0)
        self._update_status(config_id, running=False, is_flag_run=False, current_task=None, waiting_tasks=[])
        return {"status": "stopped", "config_id": config_id}

    async def solve_task(self, config_id: str, task_name: str, set_log=None) -> Dict[str, Any]:
        if task_name in _TASK_ALIAS:
            task_name = _TASK_ALIAS[task_name]
        loop = asyncio.get_running_loop()
        async with self._lock:
            session = self._sessions.get(config_id)
            if session is None:
                session = self._get_or_create_session(config_id)
            if set_log: set_log()
            baas = session.baas
            needs_init = session.baas.scheduler is None

        if needs_init:
            await loop.run_in_executor(None, baas.init_all_data)  # type: ignore

        def _call() -> None:
            try:
                self._update_status(
                    config_id,
                    running=True,
                    is_flag_run=True,
                    exit_code=None,
                    current_task=task_name,
                    waiting_tasks=[]
                )
                baas.flag_run = True
                baas.send("solve", task_name)
            finally:
                session.thread = None
                assert session is not None
                self._update_status(
                    config_id,
                    running=False,
                    is_flag_run=session.baas.flag_run,
                    current_task=None,
                    waiting_tasks=[]
                )

        thread = threading.Thread(
            target=_call,
            name=f"baas-solver-{task_name}-{config_id}",
            daemon=True,
        )
        session.thread = thread
        thread.start()

        return {"status": "ok", "task": task_name, "result": 0}

    async def require_remote_(self, config_id: str) -> ScrcpyClient:
        session = await self.get_session(config_id)
        if session.scrcpy_client is not None:
            return session.scrcpy_client
        session = await self.get_session(config_id)
        connection = Connection(session.baas)
        connection = adb.device(connection.serial)
        session.scrcpy_client = await ScrcpyClient(connection).init()
        return session.scrcpy_client

    # noinspection PyBroadException
    async def control_device_(self, config_id: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        session = await self.get_session(config_id)

        op_type = operation["type"]
        op_data = operation["data"]
        try:
            await loop.run_in_executor(None, {
                "click": lambda: session.scrcpy_client.control.touch(  # type: ignore
                    op_data["x"], op_data["y"]
                ),
                "swipe": lambda: session.scrcpy_client.control.swipe(  # type: ignore
                    op_data["fx"], op_data["fy"], op_data["tx"], op_data["ty"], op_data["dt"]
                )
            }[op_type])  # type: ignore

            return {"status": "ok", "config_id": config_id, "result": 0}
        except Exception:
            return {"status": "fail", "config_id": config_id, "result": 1}

    @staticmethod
    async def detect_adb() -> List[str]:
        loop = asyncio.get_running_loop()
        adb_res = await loop.run_in_executor(None, emulator_manager.autosearch)  # type: ignore
        return adb_res

    @staticmethod
    async def valid_cdk(cdk):
        loop = asyncio.get_running_loop()
        cdk_res = await loop.run_in_executor(None, validate_cdk, cdk)  # type: ignore
        return cdk_res

    @staticmethod
    async def test_all_sha():
        loop = asyncio.get_running_loop()
        all_sha_res = await loop.run_in_executor(None, test_all_repo_sha)  # type: ignore
        return all_sha_res

    @staticmethod
    async def check_for_update():
        loop = asyncio.get_running_loop()
        all_update_res = await loop.run_in_executor(None, check_for_update)  # type: ignore
        return all_update_res

    @staticmethod
    async def add_config(name, server):
        serial_name = str(int(datetime.datetime.now().timestamp()))
        check_config(serial_name, name=name, server=server)
        return {
            "serial": serial_name
        }

    @staticmethod
    async def update_to_latest():
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, update_to_latest, None)
        return {"status": "updated"}

    @staticmethod
    async def remove_config(_id):
        shutil.rmtree(f'./config/{_id}')
        return {}

    # ------------------------------------------------------------------
    # signal handlers
    # ------------------------------------------------------------------
    def _handle_button_signal(self, config_id: str, payload: Any) -> None:
        self._update_status(config_id, button=payload)

    def _handle_update_signal(self, config_id: str, payload: Any) -> None:
        if isinstance(payload, list) and payload:
            current = payload[0]
            waiting = [item for item in payload if item != current]
        else:
            current = None
            waiting = []
        self._update_status(config_id, current_task=current, waiting_tasks=waiting)

    def _handle_exit_signal(self, config_id: str, payload: Any) -> None:
        self._update_status(config_id, running=False, is_flag_run=False, exit_code=payload)

    def _update_status(self, config_id: str, **changes: Any) -> None:
        with self._status_lock:
            status = self._statuses.setdefault(config_id, _default_status(config_id))
            status.update(changes)
            status["timestamp"] = time.time()
            snapshot = dict(status)
        self._publish_status(config_id, snapshot)

    def _publish_status(self, config_id: str, snapshot: Optional[Dict[str, Any]] = None) -> None:
        if snapshot is None:
            with self._status_lock:
                status = self._statuses.get(config_id)
                if status is None:
                    return
                snapshot = dict(status)
        if self._loop:
            self._status_bus.publish_threadsafe({"config_id": config_id, "status": snapshot})
