import json
import os
import pathlib
import shutil
import sys
import tempfile


repository = pathlib.Path(__file__).parents[3]
sys.path.insert(0, str(repository))
from deploy.installer.setup_path import resolve_setup_toml


fixture = pathlib.Path(tempfile.mkdtemp(prefix="baas-setup-path-"))
old_cwd = pathlib.Path.cwd()
old_override = os.environ.pop("BAAS_SETUP_TOML", None)
try:
    root = fixture / "BAAS"
    launcher = fixture / "launcher"
    state = root / ".baas-installer"
    root.mkdir()
    launcher.mkdir()
    state.mkdir()
    local_setup = root / "setup.toml"
    local_setup.write_text("local", encoding="utf-8")
    launcher_setup = launcher / "setup.toml"
    launcher_setup.write_text("launcher", encoding="utf-8")
    os.chdir(root)

    assert resolve_setup_toml() == local_setup.resolve()

    pointer = state / "setup-location-v1.json"
    pointer.write_text(json.dumps({
        "schema_version": 1,
        "managed_by": "baas-installer",
        "base": "install_root",
        "path": "../launcher/setup.toml",
    }), encoding="utf-8")
    assert resolve_setup_toml() == launcher_setup.resolve()

    pointer.write_text(json.dumps({
        "schema_version": 1,
        "managed_by": "baas-installer",
        "base": "absolute",
        "path": str(launcher_setup.resolve()),
    }), encoding="utf-8")
    assert resolve_setup_toml() == launcher_setup.resolve()

    pointer.write_text("not-json", encoding="utf-8")
    assert resolve_setup_toml() == local_setup.resolve()

    pointer.write_text(json.dumps({
        "schema_version": 1,
        "managed_by": "somebody-else",
        "base": "absolute",
        "path": str(launcher_setup.resolve()),
    }), encoding="utf-8")
    assert resolve_setup_toml() == local_setup.resolve()

    os.environ["BAAS_SETUP_TOML"] = str(launcher_setup)
    assert resolve_setup_toml() == launcher_setup.resolve()
finally:
    os.chdir(old_cwd)
    if old_override is None:
        os.environ.pop("BAAS_SETUP_TOML", None)
    else:
        os.environ["BAAS_SETUP_TOML"] = old_override
    shutil.rmtree(fixture, ignore_errors=True)
