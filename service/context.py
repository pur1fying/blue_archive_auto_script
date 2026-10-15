from __future__ import annotations

import asyncio
import logging
import os
import threading
try:
    import tomllib  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[import]
from contextlib import suppress
from pathlib import Path
from typing import Optional

from .auth import ServiceAuthManager
from .conf.manager import ConfigManager
from .utils.logging import LogManager
from .runtime import ServiceRuntime
from .system_logging import install_asyncio_exception_handler

OCR_UPDATE_CHECK_ENV = "BAAS_SERVICE_OCR_UPDATE_CHECK"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _setup_no_update(project_root: Path) -> bool:
    setup_path = project_root / "setup.toml"
    if not setup_path.exists():
        return False
    try:
        with setup_path.open("rb") as file:
            data = tomllib.load(file)
    except Exception:
        return False
    general = data.get("general")
    legacy_general = data.get("General")
    if isinstance(general, dict) and isinstance(general.get("no_update"), bool):
        return general["no_update"]
    if isinstance(legacy_general, dict) and isinstance(legacy_general.get("no_update"), bool):
        return legacy_general["no_update"]
    return False


class ServiceContext:
    """Aggregates long-lived service components."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.auth_manager = ServiceAuthManager(project_root)
        self.config_manager = ConfigManager(project_root)
        self.runtime = ServiceRuntime(project_root)
        self.log_manager = LogManager()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._fs_task: Optional[asyncio.Task] = None
        self._update_check_task: Optional[asyncio.Task] = None
        self.no_update = _setup_no_update(project_root)
        self.need_ocr_update_check = _env_bool(OCR_UPDATE_CHECK_ENV, True) and not self.no_update

    async def startup(self) -> None:
        loop = asyncio.get_running_loop()
        install_asyncio_exception_handler(loop)
        logging.getLogger(__name__).info(
            "Service context startup project_root=%s no_update=%s ocr_update_check=%s",
            self.project_root,
            self.no_update,
            self.need_ocr_update_check,
        )
        self._loop = loop
        self.config_manager.set_loop(loop)
        self.runtime.set_loop(loop)
        self.log_manager.set_loop(loop)

        await self.runtime.ensure_ready()  # ensures OCR server is ready
        main_queue = self.runtime.get_main_log_queue()
        self.log_manager.register_queue(main_queue, scope="global")
        await self.log_manager.start()

        self._fs_task = asyncio.create_task(self.config_manager.watch_filesystem(), name="config-fs-watch")
        if not self.no_update:
            self._update_check_task = asyncio.create_task(
                self._periodic_update_check(),
                name="periodic-update-check",
            )
        threading.Thread(
            target=self.runtime.init_all_data,
            kwargs={"need_ocr_update_check": self.need_ocr_update_check},
            name="service-init-all-data",
            daemon=True,
        ).start()


    async def shutdown(self) -> None:
        logging.getLogger(__name__).info("Service context shutdown started")
        if self._fs_task:
            self._fs_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._fs_task
            self._fs_task = None
        if self._update_check_task:
            self._update_check_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._update_check_task
            self._update_check_task = None
        with suppress(Exception):
            await self.runtime.stop_all_tasks()
        await self.log_manager.stop()
        logging.getLogger(__name__).info("Service context shutdown completed")

    def ensure_runtime_logger_attached(self) -> None:
        for queue, scope in self.runtime.get_log_sources():
            self.log_manager.register_queue(queue, scope=scope)

    async def _periodic_update_check(self) -> None:
        interval = max(300, int(os.getenv("BAAS_UPDATE_CHECK_INTERVAL_SECONDS", "1800")))
        while True:
            try:
                await self.runtime.check_for_update()
            except Exception:
                logging.getLogger(__name__).exception("Periodic update check failed")
            await asyncio.sleep(interval)
