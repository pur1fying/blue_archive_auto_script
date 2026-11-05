from __future__ import annotations

from pathlib import Path
from typing import Any, Union

import tomli_w

try:  # Python 3.11+
    import tomllib  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[import]

from .setup_schema import CURRENT_DEFAULT_SETTINGS, legacy_runtime_view, migrate_to_current_schema


def _desktop_compatible_document(content: dict, previous: dict) -> dict:
    """Mirror desktop keys on disk without discarding installer-only options."""
    current = migrate_to_current_schema(content)
    legacy = legacy_runtime_view(current)
    # These settings have no equivalent in the service schema.
    old_general = previous.get("General", {})
    for key in (
        "refresh", "internal_launch", "no_build", "use_dynamic_update",
        "package_manager", "linux_pwd",
    ):
        if key in old_general:
            legacy["General"][key] = old_general[key]
    for table in ("General", "URLs", "Paths"):
        retained = dict(previous.get(table, {}))
        if table == "URLs":
            # Keep custom download/repository URLs until a known source is selected.
            selected_url = legacy[table]["REPO_URL_HTTP"]
            legacy[table].update(retained)
            if selected_url and current["general"].get("get_remote_sha_method"):
                legacy[table]["REPO_URL_HTTP"] = selected_url
        else:
            retained.update(legacy[table])
            legacy[table] = retained
    document = dict(previous)
    document.update(current)
    document.update(legacy)
    return document


def read_setup_toml(setup_path: Union[Path, None] = None) -> tuple[dict[str, Any], Union[Path, None]]:
    """Load `setup.toml`, creating it from defaults when missing.

    Args:
        setup_path: Optional explicit TOML path. Defaults to `Path.cwd() / "setup.toml"`.

    Returns:
        A tuple of parsed TOML content and the path that was read.
    """
    path = setup_path or (Path.cwd() / "setup.toml")
    if not path.exists():
        with path.open("wb") as file:
            tomli_w.dump(_desktop_compatible_document(CURRENT_DEFAULT_SETTINGS, {}), file)

    with path.open("rb") as fp:
        data = migrate_to_current_schema(tomllib.load(fp))
    # Loading service settings must not erase the existing desktop configuration.
    return data, path


def write_setup_toml(content: dict, setup_path: Union[Path, None] = None) -> None:
    """Persist setup configuration to TOML.

    Args:
        content: TOML-serializable setup configuration.
        setup_path: Optional explicit TOML path. Defaults to `Path.cwd() / "setup.toml"`.
    """
    path = setup_path or (Path.cwd() / "setup.toml")
    previous = {}
    if path.exists():
        with path.open("rb") as file:
            previous = tomllib.load(file)
    with path.open("wb") as fp:
        tomli_w.dump(_desktop_compatible_document(content, previous), fp)
