import json
import os
from pathlib import Path


def _usable_setup(candidate):
    try:
        resolved = Path(candidate).expanduser().resolve()
        return resolved if resolved.name == "setup.toml" and resolved.is_file() else None
    except (OSError, RuntimeError):
        return None


def resolve_setup_toml(install_root=None):
    """Return the installer's single setup.toml without breaking legacy layouts."""
    root = Path.cwd() if install_root is None else Path(install_root).resolve()
    override = os.environ.get("BAAS_SETUP_TOML")
    if override:
        usable = _usable_setup(override)
        if usable is not None:
            return usable

    pointer = root / ".baas-installer" / "setup-location-v1.json"
    try:
        document = json.loads(pointer.read_text(encoding="utf-8"))
        if (document.get("schema_version") == 1 and
                document.get("managed_by") == "baas-installer" and
                document.get("base") in {"install_root", "absolute"} and
                isinstance(document.get("path"), str)):
            candidate = Path(document["path"])
            if document["base"] == "install_root":
                candidate = root / candidate
            usable = _usable_setup(candidate)
            if usable is not None:
                return usable
    except (OSError, ValueError, TypeError):
        pass

    return _usable_setup(root / "setup.toml")
