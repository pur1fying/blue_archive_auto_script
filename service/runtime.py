from __future__ import annotations

import asyncio
import copy
import datetime
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from .conf import ConfigInitializer
from .conf import resolve_config_dir
from .utils.broadcast import BroadcastChannel
from .update import (
    read_setup_toml,
    check_for_update,
    test_all_repo_sha,
    update_to_latest,
    validate_cdk,
    write_setup_toml,
)
from .update.setup_schema import migrate_to_current_schema

if TYPE_CHECKING:
    from core.Baas_thread import Baas_thread
    from core.config.config_set import ConfigSet
    from main import Main
    from .remote.scrcpy import ScrcpyClient

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


async def run_blocking(func, *args):
    """Run a blocking callable in the default executor and return its result.

    Args:
        func: Synchronous callable to execute without blocking the event loop.
        *args: Positional arguments forwarded to ``func``.

    Returns:
        The return value produced by ``func``.
    """
    return await asyncio.get_running_loop().run_in_executor(None, func, *args)


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
    config_set: "ConfigSet"
    baas: "Baas_thread"
    button_signal: _SignalHook
    update_signal: _SignalHook
    exit_signal: _SignalHook
    scrcpy_client: Optional["ScrcpyClient"] = None
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
        self._main: Optional["Main"] = None
        self._baas: Optional["Baas_thread"] = None
        self._baas_thread: Optional[threading.Thread] = None
        self._active_config_id: Optional[str] = None
        self._update_signal: Optional[_SignalHook] = None
        self._exit_signal: Optional[_SignalHook] = None
        self._event_map_inv: Dict[str, Dict[str, str]] = {}
        self.is_all_data_initialized: bool = False

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Attach the FastAPI event loop used for runtime status broadcasts.

        Args:
            loop: Running asyncio event loop.
        """
        self._loop = loop
        self._status_bus.set_loop(loop)

    # ------------------------------------------------------------------
    # public utility accessors
    # ------------------------------------------------------------------
    def get_main_log_queue(self):
        """Return the main BAAS logger queue, initializing `Main` if needed."""
        self._ensure_main_sync()
        assert self._main is not None
        return self._main.logger.log_collector

    def init_all_data(self, need_ocr_update_check=True):
        """Initialize shared BAAS data and publish readiness when complete."""
        assert self._main is not None
        self._ensure_config()
        status = self._main.init_all_data(need_ocr_update_check=need_ocr_update_check)
        if status:
            self._status_bus.publish_threadsafe({
                "is_all_data_initialized": True
            })
            self.is_all_data_initialized = True

    def get_log_sources(self) -> List[Tuple[Any, str]]:
        """Return per-session logger queues with their provider scopes."""
        sources: List[Tuple[Any, str]] = []
        for session in self._sessions.values():
            sources.append((session.baas.logger.log_collector, f"config:{session.config_id}"))
        return sources

    def current_status(self) -> Dict[str, Dict[str, Any]]:
        """Return a deep-copied snapshot of all runtime statuses."""
        with self._status_lock:
            return copy.deepcopy(self._statuses)

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    async def subscribe_status(self) -> asyncio.Queue:
        """Subscribe to runtime status updates.

        Returns:
            Queue receiving status push dictionaries.
        """
        if self._loop is None:
            raise RuntimeError("ServiceRuntime loop is not configured")
        return self._status_bus.subscribe()

    def unsubscribe_status(self, queue_obj: asyncio.Queue) -> None:
        """Remove a status queue returned by `subscribe_status`."""
        self._status_bus.unsubscribe(queue_obj)

    # ------------------------------------------------------------------
    # lifecycle helpers
    # ------------------------------------------------------------------
    def _ensure_main_sync(self) -> None:
        if self._main is not None:
            return
        from main import Main

        self._main = Main(ocr_needed=["en-us", "zh-cn"], jsonify=True, lazy_data=True)

    async def _ensure_main(self) -> None:
        await run_blocking(self._ensure_main_sync)

    def _ensure_config(self) -> None:
        config_dir_list = []
        config_root = self._project_root / "config"
        initializer = ConfigInitializer(self._project_root)
        config_root.mkdir(exist_ok=True)
        for _dir_ in os.listdir(config_root):
            config_dir = config_root / _dir_
            if config_dir.is_dir():
                files = os.listdir(config_dir)
                if 'config.json' in files:
                    initializer.check_config(_dir_)
                    config_dir_list.append(_dir_)
        if len(config_dir_list) == 0:
            initializer.check_config('default_config')

    async def ensure_ready(self) -> None:
        """Ensure lazy core `Main` initialization has completed."""
        await self._ensure_main()

    def _get_or_create_session(self, config_id: str) -> ConfigSession:
        session = self._sessions.get(config_id)
        if session is not None:
            return session
        from core.Baas_thread import Baas_thread
        from core.config.config_set import ConfigSet

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
        """Return an existing config session or create one.

        Args:
            config_id: BAAS config directory id.

        Returns:
            ConfigSession bound to the config id.
        """
        async with self._lock:
            session = self._sessions.get(config_id)
            if session is None:
                session = self._get_or_create_session(config_id)
        return session

    async def start_scheduler(self, config_id: str, set_log=None) -> Dict[str, Any]:
        """Start the scheduler thread for a config.

        Args:
            config_id: Target config id.
            set_log: Optional callback used to register runtime log queues.

        Returns:
            Status payload consumed by `/ws/trigger`.
        """
        async with self._lock:
            session = self._get_or_create_session(config_id)
            if set_log: set_log()
            if session.thread and session.thread.is_alive():
                return {"status": "already-running", "config_id": config_id}
            init_ok = await run_blocking(session.baas.init_all_data)
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
        """Stop the scheduler thread for a config if it is running."""
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

    async def stop_all_tasks(self) -> Dict[str, Any]:
        """Stop every running BAAS scheduler/solver session before installation work."""
        config_ids = list(self._sessions.keys())
        results = []
        for config_id in config_ids:
            results.append(await self.stop_scheduler(config_id))
        return {"status": "stopped", "results": results}

    async def solve_task(self, config_id: str, task_name: str, set_log=None) -> Dict[str, Any]:
        """Run one BAAS task in a daemon worker thread.

        Args:
            config_id: Target config id.
            task_name: Task command or legacy start_* alias.
            set_log: Optional callback used to register runtime log queues.

        Returns:
            Command result payload with normalized task name.
        """
        if task_name in _TASK_ALIAS:
            task_name = _TASK_ALIAS[task_name]
        async with self._lock:
            session = self._sessions.get(config_id)
            if session is None:
                session = self._get_or_create_session(config_id)
            if set_log: set_log()
            baas = session.baas
            needs_init = session.baas.scheduler is None

        if needs_init:
            await run_blocking(baas.init_all_data)

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

    async def require_remote_(self, config_id: str) -> Union["ScrcpyClient", None]:
        """Return a cached or newly initialized scrcpy client for a config.

        Args:
            config_id: Target config id whose BAAS connection supplies the device serial.

        Returns:
            Initialized ScrcpyClient.
        """
        from adbutils import adb
        from core.device.connection import Connection
        from .remote.scrcpy import ScrcpyClient

        session = await self.get_session(config_id)
        if session.scrcpy_client is not None:
            return session.scrcpy_client
        session = await self.get_session(config_id)
        connection = Connection(session.baas, skip_package_detection=True)
        connection = adb.device(connection.serial)
        session.scrcpy_client = await ScrcpyClient(connection).init()
        return session.scrcpy_client

    # noinspection PyBroadException
    async def control_device_(self, config_id: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Send a remote control operation to the scrcpy client.

        Args:
            config_id: Target config id.
            operation: Operation dictionary with type and data fields.

        Returns:
            Structured success/failure payload.
        """
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
        from core.device import emulator_manager

        adb_res = await run_blocking(emulator_manager.autosearch)
        return adb_res

    @staticmethod
    async def valid_cdk(cdk, channel=None):
        cdk_res = await run_blocking(validate_cdk, cdk, 3.0, channel)
        return cdk_res

    @staticmethod
    async def test_all_sha(channel=None):
        all_sha_res = await run_blocking(test_all_repo_sha, 3.0, channel)
        return all_sha_res

    async def check_for_update(self):
        all_update_res = await run_blocking(check_for_update)
        self.publish_version_update(all_update_res)
        return all_update_res

    @staticmethod
    async def update_setup_toml(payload: Dict[str, Any]) -> Dict[str, Any]:
        data, path = await run_blocking(read_setup_toml)
        data = migrate_to_current_schema(data)
        general = data.setdefault("general", {})
        if "channel" in payload:
            channel = str(payload["channel"]).strip().lower()
            if channel not in {"stable", "dev"}:
                raise ValueError(f"Unsupported update channel: {channel}")
            general["channel"] = channel
        if "shaMethod" in payload:
            general["get_remote_sha_method"] = payload["shaMethod"]
        if "updateMethod" in payload:
            general["get_remote_sha_method"] = payload["updateMethod"]
        if "mirrorcCdk" in payload:
            general["mirrorc_cdk"] = payload["mirrorcCdk"]
        await run_blocking(write_setup_toml, data, path)
        return {"status": "ok", "path": str(path), "data": data}

    async def add_config(self, name, server):
        """Create a new config directory with generated timestamp id."""
        serial_name = str(int(datetime.datetime.now().timestamp()))
        ConfigInitializer(self._project_root).check_config(serial_name, name=name, server=server)
        return {
            "serial": serial_name
        }

    async def update_to_latest(self):
        await self.stop_all_tasks()
        await run_blocking(update_to_latest, None)
        return {"status": "updated"}

    def publish_version_update(self, payload: Dict[str, Any]) -> None:
        if payload:
            self._status_bus.publish_threadsafe({"version": payload})

    async def remove_config(self, _id):
        """Remove a config directory after resolving it inside project config root."""
        target = resolve_config_dir(self._project_root / "config", _id)
        if target.exists():
            if not target.is_dir():
                raise ValueError(f"config path is not a directory: {_id}")
            shutil.rmtree(target)
        return {}

    # ------------------------------------------------------------------
    # signal handlers
    # ------------------------------------------------------------------
    def _handle_button_signal(self, config_id: str, payload: Any) -> None:
        self._update_status(config_id, button=payload)

    def _handle_update_signal(self, config_id: str, payload: Any) -> None:
        if self._event_map_inv.get(config_id) is None:
            self._event_map_inv.setdefault(config_id, {
                v: k
                for k, v in self._sessions[config_id].baas.scheduler.event_map.items()
            })
        _event_map_inv = self._event_map_inv[config_id]
        if isinstance(payload, list) and payload:
            current = _event_map_inv.get(payload[0], None)
            waiting = [
                value
                for item in payload
                if (value := _event_map_inv.get(item)) is not None
                   and value != current
            ]
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
