from __future__ import annotations

from pathlib import Path
from typing import Any, Union

import tomli_w

try:  # Python 3.11+
    import tomllib  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[import]

from .setup_schema import CURRENT_DEFAULT_SETTINGS, migrate_to_current_schema


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
            tomli_w.dump(CURRENT_DEFAULT_SETTINGS, file)

    with path.open("rb") as fp:
        data = migrate_to_current_schema(tomllib.load(fp))
    with path.open("wb") as file:
        tomli_w.dump(data, file)
    return data, path


def write_setup_toml(content: dict, setup_path: Union[Path, None] = None) -> None:
    """Persist setup configuration to TOML.

    Args:
        content: TOML-serializable setup configuration.
        setup_path: Optional explicit TOML path. Defaults to `Path.cwd() / "setup.toml"`.
    """
    path = setup_path or (Path.cwd() / "setup.toml")
    if not path.exists():
        with path.open("wb") as file:
            tomli_w.dump(CURRENT_DEFAULT_SETTINGS, file)

    with path.open("wb") as fp:
        tomli_w.dump(migrate_to_current_schema(content), fp)
