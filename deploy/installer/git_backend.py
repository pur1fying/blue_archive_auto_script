"""Shared, noninteractive pygit2 operations for both launchers and UIs.

Keep this module independent of service/Qt so the standalone installer can also
import it. Git Credential Manager and external git executables are never used.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import stat
import threading
from typing import Optional
from urllib.request import getproxies, proxy_bypass
from urllib.parse import urlsplit
import tempfile

import pygit2
from pygit2.enums import ResetMode


class NonInteractiveCallbacks(pygit2.RemoteCallbacks):
    def credentials(self, url, username_from_url, allowed_types):
        raise pygit2.GitError("Git authentication failed: credentials are required (interactive prompts disabled)")


def git_proxy(url: str):
    """Honor system/environment proxies, including NO_PROXY, for HTTP remotes."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if proxy_bypass(parsed.hostname):
        return None
    proxies = getproxies()
    return proxies.get(parsed.scheme) or proxies.get("all") or True


# libgit2 timeout settings are process-wide. Serialize our network operations
# while applying an optional probe timeout, and always restore previous values.
_network_lock = threading.RLock()


@contextmanager
def _network_timeout(timeout: Optional[float] = None):
    with _network_lock:
        previous = {}
        try:
            if timeout is not None:
                milliseconds = max(1, int(float(timeout) * 1000))
                for option in ("server_connect_timeout", "server_timeout"):
                    # Older pygit2/libgit2 builds do not expose these options;
                    # their native transport timeout continues to apply.
                    if hasattr(pygit2.settings, option):
                        previous[option] = getattr(pygit2.settings, option)
                        setattr(pygit2.settings, option, milliseconds)
            yield
        finally:
            for option, value in previous.items():
                setattr(pygit2.settings, option, value)


def remote_branch_sha(url: str, branch: str, timeout: Optional[float] = None) -> str:
    """Read a branch without needing a local checkout or writing its config."""
    with _network_timeout(timeout), tempfile.TemporaryDirectory(prefix="baas-git-sha-") as temp_dir:
        repo = pygit2.init_repository(temp_dir, bare=True)
        try:
            remote = repo.remotes.create_anonymous(url)
            for head in remote.ls_remotes(callbacks=NonInteractiveCallbacks(), proxy=git_proxy(url)):
                if head["name"] == f"refs/heads/{branch}":
                    return str(head["oid"])
            raise ValueError(f"Branch '{branch}' not found at {url}")
        finally:
            repo.free()


def clone_repository(url: str, path, *, branch: Optional[str] = None, callbacks=None):
    """Clone through proxy-aware fetch, including on pygit2 1.17.

    pygit2 1.17's clone_repository does not expose proxy options. Build the
    checkout using public repository/remote APIs instead, so clone, fetch and
    probes use the same proxy and authentication policy on all supported builds.
    """
    path = Path(path)
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise pygit2.GitError(f"Clone destination is not an empty directory: {path}")
    callbacks = callbacks or NonInteractiveCallbacks()
    with _network_timeout():
        repo = pygit2.init_repository(str(path))
        try:
            remote = repo.remotes.create("origin", url)
            proxy = git_proxy(url)
            heads = remote.ls_remotes(callbacks=callbacks, proxy=proxy)
            remote_head = next((head for head in heads if head["name"] == "HEAD"), None)
            default_ref = remote_head.get("symref_target") if remote_head else None
            selected_ref = f"refs/heads/{branch}" if branch is not None else default_ref
            if selected_ref and not any(head["name"] == selected_ref for head in heads):
                raise ValueError(f"Branch '{selected_ref}' not found at {url}")
            # The configured refspec downloads all branches, as a normal full
            # clone does; fetch's proxy argument is available since pygit2 1.17.
            remote.fetch(callbacks=callbacks, proxy=proxy)
            if default_ref and default_ref.startswith("refs/heads/"):
                default_tracking = "refs/remotes/origin/" + default_ref[len("refs/heads/"):]
                repo.references.create("refs/remotes/origin/HEAD", default_tracking, force=True)
            if selected_ref:
                selected_branch = selected_ref[len("refs/heads/"):]
                tracking_ref = f"refs/remotes/origin/{selected_branch}"
                commit = repo.revparse_single(tracking_ref).peel(pygit2.Commit)
                repo.references.create(selected_ref, commit.id, force=True)
                repo.branches.local[selected_branch].upstream = repo.branches.remote[f"origin/{selected_branch}"]
                repo.set_head(selected_ref)
                repo.reset(commit.id, ResetMode.HARD)
            elif remote_head is not None:
                # A remote can advertise a detached HEAD with no branch name.
                # Fetch HEAD explicitly if normal branch fetch did not get it.
                head_oid = remote_head["oid"]
                if head_oid not in repo:
                    remote.fetch(["HEAD"], callbacks=callbacks, proxy=proxy)
                repo.set_head(head_oid)
                repo.reset(head_oid, ResetMode.HARD)
            # An empty remote intentionally leaves an unborn local HEAD.
            return repo
        except Exception:
            repo.free()
            raise


def install_staged_repository(staged_path, target_path):
    """Merge a successful clone into an install, preserving untracked data.

    Replacing metadata happens only after clone has completed. In particular,
    existing config/deploy directories must merge, never become config/config.
    """
    staged_path, target_path = Path(staged_path), Path(target_path)
    target_path.mkdir(parents=True, exist_ok=True)
    git_dir = target_path / ".git"
    if git_dir.is_dir():
        shutil.rmtree(git_dir, onerror=_remove_readonly)
    elif git_dir.exists():
        git_dir.unlink()
    shutil.copytree(staged_path, target_path, dirs_exist_ok=True)


def _remove_readonly(function, path, exc_info):
    """Git object files are read-only on Windows; retry only permission errors."""
    if not isinstance(exc_info[1], PermissionError):
        raise exc_info[1]
    os.chmod(path, stat.S_IWRITE)
    function(path)


def ensure_origin(repo, url: str, remote_name: str = "origin"):
    """Update the URL in place so fetch refspecs and branch tracking survive."""
    if remote_name not in repo.remotes.names():
        return repo.remotes.create(remote_name, url)
    if repo.remotes[remote_name].url != url:
        repo.remotes.set_url(remote_name, url)
    return repo.remotes[remote_name]


def fetch_and_reset_branch(repo, branch: str, *, remote_name: str = "origin", callbacks=None) -> str:
    """Fetch the exact branch, switch HEAD, and discard tracked local changes.

    Update the selected local branch only. In particular, switching channels
    must never reset the branch that happened to be checked out before fetch.
    Untracked configuration and user data are preserved.
    """
    remote = repo.remotes[remote_name]
    remote_ref = f"refs/remotes/{remote_name}/{branch}"
    refspec = f"+refs/heads/{branch}:{remote_ref}"
    with _network_timeout():
        # libgit2 can fetch a missing explicit ref without raising and leave a
        # previous remote-tracking ref intact. Never reset to that stale ref.
        advertised = remote.ls_remotes(callbacks=callbacks or NonInteractiveCallbacks(), proxy=git_proxy(remote.url))
        if not any(head["name"] == f"refs/heads/{branch}" for head in advertised):
            raise ValueError(f"Branch '{branch}' not found at {remote.url}")
        remote.fetch([refspec], callbacks=callbacks or NonInteractiveCallbacks(), proxy=git_proxy(remote.url))
    commit = repo.revparse_single(remote_ref).peel(pygit2.Commit)
    local_ref = f"refs/heads/{branch}"
    repo.references.create(local_ref, commit.id, force=True)
    repo.branches.local[branch].upstream = repo.branches.remote[f"{remote_name}/{branch}"]
    repo.set_head(local_ref)
    repo.reset(commit.id, ResetMode.HARD)
    return str(commit.id)


def rollback_repository(repo, target: str) -> str:
    commit = repo.revparse_single(target).peel(pygit2.Commit)
    repo.reset(commit.id, ResetMode.HARD)
    return str(commit.id)
