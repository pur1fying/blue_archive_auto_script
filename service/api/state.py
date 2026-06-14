from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REMEMBER_COOKIE_NAME = "baas_remember"
REMEMBER_COOKIE_MAX_AGE = int(os.getenv("BAAS_REMEMBER_TTL_SECONDS", str(60 * 60 * 24 * 180)))


class LazyServiceContext:
    """Delay runtime-heavy service imports until the app actually starts."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._context = None

    def _get_context(self):
        if self._context is None:
            from service.context import ServiceContext

            self._context = ServiceContext(self.project_root)
        return self._context

    def __getattr__(self, name: str):
        return getattr(self._get_context(), name)


context = LazyServiceContext(PROJECT_ROOT)
