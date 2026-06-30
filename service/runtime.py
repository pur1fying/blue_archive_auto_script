from __future__ import annotations

import asyncio
import copy
import io
import json
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from .conf import ConfigInitializer
from .conf import resolve_config_dir
from .injection import apply_service_injections
from .utils.broadcast import BroadcastChannel
from .utils.timestamps import unix_timestamp_ms
from .update import (
    read_setup_toml,
    repo_sha_test_configs,
    check_for_update,
    test_all_repo_sha,
    test_repo_sha,
    update_to_latest,
    update_to_latest_with_progress,
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

MAX_SHA_TEST_TIMEOUT = 10.0


def _is_android_runtime() -> bool:
    return os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}


def _coerce_sha_test_timeout(timeout: Any = None) -> float:
    try:
        value = float(timeout)
    except (TypeError, ValueError):
        return MAX_SHA_TEST_TIMEOUT
    return max(0.1, min(value, MAX_SHA_TEST_TIMEOUT))


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


class _AndroidDisplayResizeGuard:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_count = 0

    @staticmethod
    def _target_size() -> str:
        return os.getenv("BAAS_ANDROID_WM_SIZE", "720x1280").strip() or "720x1280"

    @staticmethod
    def _serial() -> str:
        return os.getenv("BAAS_ANDROID_U2_SERIAL", "127.0.0.1:7912").strip() or "127.0.0.1:7912"

    @staticmethod
    def _shell(command: str) -> Any:
        import uiautomator2 as u2

        serial = _AndroidDisplayResizeGuard._serial()
        target = serial if serial.startswith(("http://", "https://")) else f"http://{serial}"
        return u2.connect(target).shell(command)

    def activate(self, logger=None) -> None:
        if not _is_android_runtime():
            return
        with self._lock:
            self._active_count += 1
            if self._active_count != 1:
                return
        target_size = self._target_size()
        try:
            current = self._shell("wm size")
            if logger is not None:
                logger.info(f"Android display size before BAAS run: {current}")
                logger.info(f"Set Android display size to {target_size}.")
            self._shell(f"wm size {target_size}")
        except Exception as exc:
            with self._lock:
                self._active_count = max(0, self._active_count - 1)
            if logger is not None:
                logger.error("Failed to set Android display size.")
                logger.error(exc)
            raise

    def release(self, logger=None) -> None:
        if not _is_android_runtime():
            return
        with self._lock:
            if self._active_count <= 0:
                return
            self._active_count -= 1
            if self._active_count != 0:
                return
        try:
            if logger is not None:
                logger.info("Reset Android display size after BAAS run.")
            self._shell("wm size reset")
        except Exception as exc:
            if logger is not None:
                logger.error("Failed to reset Android display size.")
                logger.error(exc)


def _default_status(config_id: str) -> Dict[str, Any]:
    return {
        "config_id"    : config_id,
        "running"      : False,
        "is_flag_run"  : False,
        "button"       : None,
        "current_task" : None,
        "waiting_tasks": [],
        "exit_code"    : None,
        "timestamp"    : unix_timestamp_ms(),
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
        self._lock: Optional[asyncio.Lock] = None
        self._main: Optional["Main"] = None
        self._baas: Optional["Baas_thread"] = None
        self._baas_thread: Optional[threading.Thread] = None
        self._active_config_id: Optional[str] = None
        self._update_signal: Optional[_SignalHook] = None
        self._exit_signal: Optional[_SignalHook] = None
        self._event_map_inv: Dict[str, Dict[str, str]] = {}
        self._android_active_config_id: Optional[str] = None
        self._android_display_guard = _AndroidDisplayResizeGuard()
        self.is_all_data_initialized: bool = False

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Attach the FastAPI event loop used for runtime status broadcasts.

        Args:
            loop: Running asyncio event loop.
        """
        self._loop = loop
        self._status_bus.set_loop(loop)

    def _async_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

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
        apply_service_injections()
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
        apply_service_injections()
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
        async with self._async_lock():
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
        async with self._async_lock():
            session = self._get_or_create_session(config_id)
            if set_log: set_log()
            if session.thread and session.thread.is_alive():
                return {"status": "already-running", "config_id": config_id}
            await run_blocking(self._android_display_guard.activate, session.baas.logger)
            try:
                init_ok = await run_blocking(session.baas.init_all_data)
            except Exception:
                await run_blocking(self._android_display_guard.release, session.baas.logger)
                raise
            if not init_ok:
                await run_blocking(self._android_display_guard.release, session.baas.logger)
                raise RuntimeError("Baas_thread initialization failed")

            def runner() -> None:
                try:
                    session.baas.send("start")
                finally:
                    self._android_display_guard.release(session.baas.logger)
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
        async with self._async_lock():
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

    def set_android_active_config(self, config_id: str) -> Dict[str, Any]:
        self._android_active_config_id = config_id
        return {"status": "ok", "config_id": config_id}

    async def toggle_android_active_config(self) -> Dict[str, Any]:
        config_id = self._android_active_config_id
        if not config_id:
            config_ids = self._list_config_ids_sync()
            config_id = config_ids[0] if config_ids else None
        if not config_id:
            return {"status": "no-config"}
        running = bool(self.current_status().get(config_id, {}).get("running"))
        if running:
            result = await self.stop_scheduler(config_id)
            return {"status": "stopped", "config_id": config_id, "data": result}
        result = await self.start_scheduler(config_id)
        return {"status": "started", "config_id": config_id, "data": result}

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
            _original_task_name = task_name
            task_name = _TASK_ALIAS[task_name]
        async with self._async_lock():
            session = self._sessions.get(config_id)
            if session is None:
                session = self._get_or_create_session(config_id)
            if set_log: set_log()
            if session.thread and session.thread.is_alive():
                return {"status": "already-running", "config_id": config_id}
            baas = session.baas
            needs_init = session.baas.scheduler is None

            if needs_init:
                await run_blocking(self._android_display_guard.activate, baas.logger)
                try:
                    await run_blocking(baas.init_all_data)
                except Exception:
                    await run_blocking(self._android_display_guard.release, baas.logger)
                    raise
            elif _is_android_runtime():
                await run_blocking(self._android_display_guard.activate, baas.logger)

            def _call() -> None:
                try:
                    self._update_status(
                        config_id,
                        running=True,
                        is_flag_run=True,
                        exit_code=None,
                        current_task=_original_task_name,
                        waiting_tasks=[]
                    )
                    baas.flag_run = True
                    baas.send("solve", task_name)
                finally:
                    self._android_display_guard.release(baas.logger)
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
        if os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}:
            raise RuntimeError("Remote control is disabled on Android")
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
        if os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}:
            return {"status": "disabled", "config_id": config_id, "result": 1}
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
        if os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}:
            configured = os.getenv("BAAS_ANDROID_ADB_SERIAL", "").strip()
            candidates = [configured] if configured else []
            candidates.extend(["127.0.0.1:5555", "localhost:5555"])
            return list(dict.fromkeys(item for item in candidates if item))

        from core.device import emulator_manager

        adb_res = await run_blocking(emulator_manager.autosearch)
        return adb_res

    @staticmethod
    async def valid_cdk(cdk, channel=None):
        cdk_res = await run_blocking(validate_cdk, cdk, 3.0, channel)
        return cdk_res

    @staticmethod
    async def test_all_sha(channel=None, timeout=None):
        all_sha_res = await run_blocking(
            test_all_repo_sha,
            _coerce_sha_test_timeout(timeout),
            channel,
        )
        return all_sha_res

    @staticmethod
    async def test_all_sha_stream(channel=None, timeout=None):
        request_timeout = _coerce_sha_test_timeout(timeout)

        async def test_one(config: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return await run_blocking(test_repo_sha, config, request_timeout)
            except Exception as exc:  # noqa: BLE001 - keep one failed source from stopping the stream
                method = config.get("method")
                return {
                    "name"    : config.get("name"),
                    "method"  : getattr(method, "name", str(method)),
                    "duration": 0,
                    "success" : False,
                    "value"   : None,
                    "error"   : str(exc),
                }

        tasks = [
            asyncio.create_task(test_one(config))
            for config in repo_sha_test_configs(channel)
        ]
        try:
            for task in asyncio.as_completed(tasks):
                yield await task
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

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
        if "noUpdate" in payload:
            general["no_update"] = bool(payload["noUpdate"])
        if "no_update" in payload:
            general["no_update"] = bool(payload["no_update"])
        if "gitBackend" in payload:
            general["git_backend"] = str(payload["gitBackend"])
        if "git_backend" in payload:
            general["git_backend"] = str(payload["git_backend"])
        await run_blocking(write_setup_toml, data, path)
        return {"status": "ok", "path": str(path), "data": data}

    async def add_config(self, name, server):
        """Create a new config directory with generated timestamp id."""
        serial_name = self._new_config_id()
        ConfigInitializer(self._project_root).check_config(serial_name, name=name, server=server)
        return {
            "serial": serial_name
        }

    def _new_config_id(self) -> str:
        config_root = self._project_root / "config"
        while True:
            config_id = str(int(time.time() * 1000))
            if not (config_root / config_id).exists():
                return config_id
            time.sleep(0.001)

    def _config_path(self, config_id: str) -> Path:
        return resolve_config_dir(self._project_root / "config", config_id)

    def _read_config_name(self, config_id: str) -> Optional[str]:
        path = self._config_path(config_id) / "config.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        name = data.get("name")
        return str(name).strip() if name is not None else None

    def _unique_config_name(self, base_name: str, *, exclude_id: Optional[str] = None) -> str:
        existing = {
            name
            for config_id in self._list_config_ids_sync()
            if config_id != exclude_id
            for name in [self._read_config_name(config_id)]
            if name
        }
        candidate = f"{base_name}_copy"
        index = 2
        while candidate in existing:
            candidate = f"{base_name}_copy{index}"
            index += 1
        return candidate

    def _list_config_ids_sync(self) -> List[str]:
        config_root = self._project_root / "config"
        if not config_root.exists():
            return []
        ids: List[str] = []
        for child in config_root.iterdir():
            if child.is_dir() and (child / "config.json").exists() and (child / "event.json").exists():
                ids.append(child.name)
        return sorted(ids)

    def _copy_config_sync(self, source_id: str) -> Dict[str, Any]:
        source = self._config_path(source_id)
        if not source.is_dir():
            raise ValueError(f"config not found: {source_id}")

        target_id = self._new_config_id()
        target = self._config_path(target_id)
        shutil.copytree(source, target)

        config_path = target / "config.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        base_name = str(config_data.get("name") or source_id).strip() or source_id
        config_data["name"] = self._unique_config_name(base_name, exclude_id=source_id)
        config_path.write_text(json.dumps(config_data, ensure_ascii=False, indent=2), encoding="utf-8")

        ConfigInitializer(self._project_root).check_config(target_id)
        return {"serial": target_id, "name": config_data["name"]}

    async def copy_config(self, config_id: str) -> Dict[str, Any]:
        return await run_blocking(self._copy_config_sync, config_id)

    def _export_config_sync(self, config_id: str) -> Dict[str, Any]:
        source = self._config_path(config_id)
        if not source.is_dir():
            raise ValueError(f"config not found: {config_id}")
        config_path = source / "config.json"
        if not config_path.exists():
            raise ValueError(f"config.json not found for config: {config_id}")

        config_name = self._read_config_name(config_id) or config_id
        safe_name = "".join(c if c not in '<>:"/\\|?*' else "_" for c in config_name).strip() or config_id
        buffer = io.BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source).as_posix())
        return {
            "filename": f"{safe_name}.zip",
            "content": buffer.getvalue(),
        }

    async def export_config(self, config_id: str) -> Dict[str, Any]:
        return await run_blocking(self._export_config_sync, config_id)

    @staticmethod
    def _safe_zip_members(archive: ZipFile) -> List[str]:
        members: List[str] = []
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            parts = [part for part in name.split("/") if part]
            if not parts or any(part == ".." for part in parts):
                raise ValueError(f"unsafe archive path: {info.filename}")
            if Path(name).is_absolute():
                raise ValueError(f"unsafe archive path: {info.filename}")
            if not info.is_dir():
                members.append(name)
        return members

    @staticmethod
    def _archive_root_prefix(members: List[str]) -> str:
        if "config.json" in members:
            return ""
        top_levels = {member.split("/", 1)[0] for member in members if "/" in member}
        if len(top_levels) == 1:
            prefix = next(iter(top_levels)) + "/"
            if f"{prefix}config.json" in members:
                return prefix
        raise ValueError("archive must contain config.json")

    def _import_config_sync(self, content: bytes) -> Dict[str, Any]:
        try:
            with ZipFile(io.BytesIO(content)) as archive:
                members = self._safe_zip_members(archive)
                prefix = self._archive_root_prefix(members)
                config_member = f"{prefix}config.json"
                config_data = json.loads(archive.read(config_member).decode("utf-8"))
                config_name = str(config_data.get("name") or "").strip()
                if not config_name:
                    raise ValueError("imported config.json must contain name")

                target_id = self._new_config_id()
                target = self._config_path(target_id)
                target.mkdir(parents=True)
                for member in members:
                    if not member.startswith(prefix):
                        continue
                    relative = member[len(prefix):]
                    if not relative:
                        continue
                    target_file = target / Path(relative)
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_bytes(archive.read(member))
        except BadZipFile as exc:
            raise ValueError("invalid config archive") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("invalid config.json in archive") from exc

        ConfigInitializer(self._project_root).check_config(target_id)
        for existing_id in self._list_config_ids_sync():
            if existing_id != target_id and self._read_config_name(existing_id) == config_name:
                shutil.rmtree(self._config_path(existing_id))
        return {"serial": target_id, "name": config_name}

    async def import_config(self, content: bytes) -> Dict[str, Any]:
        return await run_blocking(self._import_config_sync, content)

    async def update_to_latest(self):
        await self.stop_all_tasks()
        result = await run_blocking(update_to_latest, None)
        if isinstance(result, dict):
            return result
        return {"status": "updated"}

    async def update_to_latest_stream(self):
        await self.stop_all_tasks()
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        def progress(stage: str, payload: Dict[str, Any]) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "progress", "stage": stage, **payload})

        def worker() -> None:
            try:
                result = update_to_latest_with_progress(None, progress=progress)
                if not isinstance(result, dict):
                    result = {"status": "updated"}
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "result", "result": result})
            except Exception as exc:  # noqa: BLE001 - surfaced through stream response
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "error": str(exc)})

        thread = threading.Thread(target=worker, name="baas-update-stream", daemon=True)
        thread.start()
        while True:
            event = await queue.get()
            yield event
            if event.get("type") in {"result", "error"}:
                break

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
            status["timestamp"] = unix_timestamp_ms()
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
