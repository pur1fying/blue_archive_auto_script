from __future__ import annotations

import asyncio
import threading
from contextlib import suppress
from pathlib import Path
from typing import Optional

from .config_manager import ConfigManager
from .logging import LogManager
from .runtime import ServiceRuntime


class ServiceContext:
    """Aggregates long-lived service components."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.config_manager = ConfigManager(project_root)
        self.runtime = ServiceRuntime(project_root)
        self.log_manager = LogManager()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._fs_task: Optional[asyncio.Task] = None

    async def startup(self) -> None:
        loop = asyncio.get_running_loop()
        self._loop = loop
        self.config_manager.set_loop(loop)
        self.runtime.set_loop(loop)
        self.log_manager.set_loop(loop)

        await self.runtime.ensure_ready()  # ensures OCR server is ready
        main_queue = self.runtime.get_main_log_queue()
        self.log_manager.register_queue(main_queue, scope="global")
        await self.log_manager.start()

        self._fs_task = asyncio.create_task(self.config_manager.watch_filesystem(), name="config-fs-watch")
        threading.Thread(target=self.runtime.init_all_data).start()


    async def shutdown(self) -> None:
        if self._fs_task:
            self._fs_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._fs_task
            self._fs_task = None
        await self.log_manager.stop()

    def ensure_runtime_logger_attached(self) -> None:
        for queue, scope in self.runtime.get_log_sources():
            self.log_manager.register_queue(queue, scope=scope)
