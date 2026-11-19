import json
import os
import shutil
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from deploy.installer.toml_config import TOML_Config


def desktop_migration_enabled():
    return sys.platform in ("win32", "darwin", "linux") and not hasattr(sys, "getandroidapilevel")


@contextmanager
def _handoff_lock(home):
    # Match the exclusive file lock used by the Tauri installer.
    fd = os.open(home / ".baas.legacy.lock", os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "r+b") as lock:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            yield


def _ignore_links(directory, names):
    ignored = []
    for name in names:
        info = (Path(directory) / name).lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            ignored.append(name)
    return ignored


def sync_legacy_config(root, language, theme, home=None):
    """Publish one complete snapshot of the current legacy installation."""
    home = Path.home() if home is None else home
    root = root.resolve()
    bundle = home / ".baas.legacy"
    prefs = {"installPath": str(root), "language": language, "theme": theme}
    setup = root / "setup.toml"
    if setup.is_file():
        try:
            cdk = TOML_Config(setup).get("General.mirrorc_cdk", "")
            if isinstance(cdk, str) and cdk.strip():
                prefs["mirrorcCdk"] = cdk.strip()
        except (OSError, ValueError):
            # An unavailable setup.toml should not prevent backing up profiles.
            pass

    with _handoff_lock(home), tempfile.TemporaryDirectory(prefix=".baas.legacy-", dir=home) as work:
        if (home / ".baas.legacy.pending").is_dir():
            return False
        work = Path(work)
        snapshot = work / "snapshot"
        snapshot.mkdir(mode=0o700)
        shutil.copytree(root / "config", snapshot / "config", ignore=_ignore_links)
        preference_file = snapshot / "baas.preference.json"
        fd = os.open(preference_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(prefs, stream, ensure_ascii=False)
        hidden = (bundle / "no_notification").is_file()
        if hidden:
            (snapshot / "no_notification").touch()
        previous = work / "previous"
        if bundle.exists():
            bundle.rename(previous)
        try:
            snapshot.rename(bundle)
        except OSError:
            if previous.exists():
                previous.rename(bundle)
            raise
    return not hidden


def suppress_legacy_notice(home=None):
    home = Path.home() if home is None else home
    with _handoff_lock(home):
        bundle = home / ".baas.legacy"
        if bundle.is_dir() and not bundle.is_symlink():
            (bundle / "no_notification").touch()
