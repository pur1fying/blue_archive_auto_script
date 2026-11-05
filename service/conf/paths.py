from __future__ import annotations

from pathlib import Path


class ConfigPathError(ValueError):
    """Raised when a config id would escape the configured config root."""


def ensure_safe_config_id(config_id: str) -> str:
    """Validate and normalize a config id.

    Args:
        config_id: User or API supplied config identifier.

    Returns:
        The stripped config id if it contains no path separators.

    Raises:
        ConfigPathError: If the id is empty or would address nested/parent paths.
    """
    value = str(config_id).strip()
    if not value:
        raise ConfigPathError("config id is required")
    if any(sep in value for sep in ("/", "\\")) or value in {".", ".."}:
        raise ConfigPathError(f"invalid config id: {config_id!r}")
    return value


def resolve_config_dir(config_root: Path, config_id: str) -> Path:
    """Resolve a config directory under `config_root` without allowing escape.

    Args:
        config_root: Directory that owns all config folders.
        config_id: Single config identifier.

    Returns:
        Absolute path to the config directory.

    Raises:
        ConfigPathError: If `config_id` is unsafe or resolves outside `config_root`.
    """
    safe_id = ensure_safe_config_id(config_id)
    root = config_root.resolve()
    target = (root / safe_id).resolve()
    if target != root / safe_id:
        raise ConfigPathError(f"invalid config path: {config_id!r}")
    return target
