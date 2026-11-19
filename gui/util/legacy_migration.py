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


def _handoff_directory():
    from PyQt5.QtCore import QStandardPaths

    location = Path(QStandardPaths.writableLocation(QStandardPaths.GenericDataLocation))
    if not location.is_absolute():
        raise OSError("Cannot locate the user application data directory")
    # Match Tauri's data_local_dir on Windows, macOS and Linux.
    return location / "BAAS" / "legacy-ui-migration"


@contextmanager
def _handoff_lock(directory):
    # Match the exclusive file lock used by the Tauri installer.
    fd = os.open(directory / ".baas.legacy.lock", os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "r+b") as lock:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield


def _ignore_links(directory, names):
    ignored = []
    for name in names:
        info = (Path(directory) / name).lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            ignored.append(name)
    return ignored


def sync_legacy_config(root, language, theme):
    """Publish one complete snapshot of the current legacy installation."""
    directory = _handoff_directory()
    root = root.resolve()
    bundle = directory / ".baas.legacy"
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

    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with _handoff_lock(directory):
        if (directory / ".baas.legacy.pending").is_dir():
            return False
        work = Path(tempfile.mkdtemp(prefix=".baas.legacy-", dir=directory))
        previous = work / "previous"
        try:
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
            if bundle.exists() or bundle.is_symlink():
                bundle.rename(previous)
            snapshot.rename(bundle)
        except OSError:
            if previous.exists() or previous.is_symlink():
                previous.rename(bundle)
            shutil.rmtree(work, ignore_errors=True)
            raise
        shutil.rmtree(work, ignore_errors=True)
    return not hidden


def suppress_legacy_notice():
    directory = _handoff_directory()
    with _handoff_lock(directory):
        bundle = directory / ".baas.legacy"
        if bundle.is_dir() and not bundle.is_symlink():
            (bundle / "no_notification").touch()
