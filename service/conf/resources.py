from __future__ import annotations

from pathlib import Path
from typing import Optional

from .paths import resolve_config_dir


ResourceKey = tuple[str, Optional[str]]


class ResourcePathResolver:
    def __init__(self, project_root: Path) -> None:
        self.root = project_root
        self.config_root = self.root / "config"

    def file_path(self, resource: str, resource_id: Optional[str]) -> Path:
        if resource in ("config", "event"):
            if not resource_id:
                raise ValueError(f"resource_id required for resource '{resource}'")
            return resolve_config_dir(self.config_root, resource_id) / f"{resource}.json"
        if resource == "gui":
            return self.config_root / "gui.json"
        if resource == "static":
            return self.config_root / "static.json"
        if resource == "setup_toml":
            return self.root / "setup.toml"
        raise ValueError(f"Unsupported resource '{resource}'")
