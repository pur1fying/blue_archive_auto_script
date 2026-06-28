from __future__ import annotations

import time
import os
import pygit2
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Union, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Optional
from pygit2.enums import ResetMode

import requests

from deploy.installer.const import GetShaMethod, get_remote_sha_methods_for_channel, normalize_update_channel
from deploy.installer.mirrorc_update.const import MirrorCErrorCode
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater

from service.update.repository import update_repo_to_latest
from service.update.setup_io import read_setup_toml, write_setup_toml
from service.update.setup_schema import migrate_to_current_schema, setup_channel

RepositoryResult = Dict[str, Any]


class GitOperationHandler:
    """
    Encapsulates Git operations.
    Priority:
    1. If system 'git' executable exists, use it for read operations (ls-remote, rev-parse).
    2. If not, fall back to 'pygit2'.
    3. For critical state changes like rollback, 'pygit2' is preferred/enforced.
    """

    def __init__(self, repo_path: Union[str, Path] = "."):
        self.repo_path = Path(repo_path)
        self.git_executable = None and shutil.which("git")

    def _run_git_cmd(self, args: List[str]) -> str:
        """Helper to run system git commands."""
        if not self.git_executable:
            raise FileNotFoundError("Git executable not found.")

        # Ensure we run in the correct directory
        result = subprocess.run(
            [self.git_executable, *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def get_remote_latest_sha(self, url: str, branch: str) -> str:
        """
        Get the SHA of a remote branch.
        Uses `git ls-remote` if available, otherwise uses pygit2 anonymous remote.
        """
        if self.git_executable:
            try:
                # Command: git ls-remote <url> refs/heads/<branch>
                # Output format: <SHA>\trefs/heads/<branch>
                ref = f"refs/heads/{branch}"
                output = self._run_git_cmd(["ls-remote", url, ref])
                if output:
                    return output.split()[0]
                raise ValueError(f"Branch '{branch}' not found at {url} (System Git)")
            except (subprocess.CalledProcessError, IndexError, ValueError) as e:
                # If system git fails, try fallback or just raise
                raise RuntimeError(f"System git failed: {e}")

        # Fallback to pygit2
        repo = pygit2.Repository(self.repo_path)
        # Create anonymous remote to avoid modifying config
        remote = repo.remotes.create_anonymous(url)
        target_ref = f"refs/heads/{branch}"
        for head in remote.ls_remotes():
            if head.get("name") == target_ref:
                return str(head.get("oid"))
        raise ValueError(f"Branch '{branch}' not found at {url} (pygit2)")

    def get_local_head_info(self) -> Tuple[str, str]:
        """
        Get the current local SHA and branch name.
        Returns: (sha, branch_name)
        """
        if self.git_executable:
            try:
                # Get SHA: git rev-parse HEAD
                sha = self._run_git_cmd(["rev-parse", "HEAD"])

                # Get Branch: git rev-parse --abbrev-ref HEAD
                # Note: Returns "HEAD" if detached
                branch = self._run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
                return sha, branch
            except subprocess.CalledProcessError:
                # Likely empty repo or error
                raise RuntimeError("Failed to retrieve local git info via system git.")

        # Fallback to pygit2
        repo = pygit2.Repository(self.repo_path)
        sha = str(repo.revparse_single("HEAD").id)
        branch = repo.head.shorthand
        return sha, branch

    def rollback(self, target_sha: str):
        """
        Rollback the repository to a specific SHA.
        Per requirements, this strictly uses pygit2.
        """
        repo = pygit2.Repository(self.repo_path)
        # Logic for rollback using pygit2 (e.g., reset --hard)
        # This is a placeholder for where the rollback logic would go.
        commit = repo.revparse_single(target_sha)
        repo.reset(commit.id, ResetMode.HARD)


@dataclass
class VersionInfo:
    """Normalized version data loaded from setup.toml."""

    version: Optional[str]
    source: str
    path: Path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "path": str(self.path),
        }


def _github_api_get_latest_sha(config: Dict[str, Any], timeout: float) -> Tuple[bool, str]:
    owner = config["owner"]
    repo = config["repo"]
    branch = config["branch"]
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        response_json = response.json()
        sha_value = response_json.get("commit", {}).get("sha")
        if not sha_value:
            return False, "Commit SHA not found in GitHub response"
        return True, sha_value
    except requests.RequestException as exc:  # pragma: no cover - network errors
        return False, str(exc)


def _mirrorc_api_get_latest_sha(timeout: float, channel: str = "stable") -> Tuple[bool, str]:
    mirrorc_inst = MirrorC_Updater(app="BAAS_repo", current_version="", channel=channel)
    try:
        ret = mirrorc_inst.get_latest_version(cdk="", timeout=timeout)
        if ret.has_data and ret.latest_version_name:
            return True, ret.latest_version_name
        return False, ret.message
    except Exception as exc:  # pragma: no cover - external dependency
        return False, str(exc)


def _git_wrapper_get_latest_sha(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Replaces the direct pygit2 call.
    Uses GitOperationHandler to determine whether to use system git or pygit2.
    """
    url = config["url"]
    branch = config["branch"]

    git_ops = GitOperationHandler(Path.cwd())

    try:
        sha = git_ops.get_remote_latest_sha(url, branch)
        return True, sha
    except Exception as exc:
        return False, str(exc)


def repo_sha_test_configs(channel: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return normalized repository SHA test configs for a channel."""
    channel = normalize_update_channel(channel or _setup_channel()[0])
    return [{**config, "channel": channel} for config in get_remote_sha_methods_for_channel(channel)]


def test_all_repo_sha(timeout: float = 3.0, channel: Optional[str] = None) -> List[RepositoryResult]:
    """Test every configured repository and return timing + SHA details."""
    results: List[RepositoryResult] = []
    for config in repo_sha_test_configs(channel):
        result = test_repo_sha(config, timeout)
        results.append(result)
    return results


def test_repo_sha(config: dict[str, Union[str, GetShaMethod]], timeout: float) -> dict[str, Any]:
    method = config["method"]
    start = time.perf_counter()
    if method == GetShaMethod.GITHUB_API:
        success, value = _github_api_get_latest_sha(config, timeout)
    elif method == GetShaMethod.MIRRORC_API:
        success, value = _mirrorc_api_get_latest_sha(timeout, str(config.get("channel") or _setup_channel()[0]))
    else:
        # Renamed to indicate it uses the wrapper logic
        success, value = _git_wrapper_get_latest_sha(config)
    elapsed = time.perf_counter() - start
    result: RepositoryResult = {
        "name": config.get("name"),
        "method": method.name,
        "duration": elapsed,
        "success": success,
        "value": value if success else None,
        "error": None if success else value,
    }
    return result


def _format_expired_time(timestamp_value: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
    if not timestamp_value:
        return None, None
    dt = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
    return timestamp_value, dt.isoformat()


def _setup_channel(setup_path: Optional[Path] = None) -> Tuple[str, Dict[str, Any], Path]:
    data, path = read_setup_toml(setup_path)
    channel = setup_channel(data)
    return channel, data, path


def validate_cdk(cdk: str, timeout: float = 3.0, channel: Optional[str] = None) -> Dict[str, Any]:
    """Validate a MirrorC CDK and return structured status information."""
    channel = normalize_update_channel(channel or _setup_channel()[0])
    if cdk != "":
        updater = MirrorC_Updater(app="BAAS_repo", current_version="", channel=channel)
        try:
            ret = updater.get_latest_version(cdk=cdk, timeout=timeout)
        except requests.RequestException as exc:
            data, path_setup_toml = read_setup_toml()
            data = migrate_to_current_schema(data)
            data["general"]["mirrorc_cdk"] = ""
            write_setup_toml(data, path_setup_toml)
            return {
                "success": False,
                "code": None,
                "message": str(exc),
                "latest_version": None,
                "expires_at": None,
                "expires_at_iso": None,
                "mirrorc_message": None,
            }
        except Exception as exc:  # pragma: no cover - unexpected error
            data, path_setup_toml = read_setup_toml()
            data = migrate_to_current_schema(data)
            data["general"]["mirrorc_cdk"] = ""
            write_setup_toml(data, path_setup_toml)
            return {
                "success": False,
                "code": None,
                "message": str(exc),
                "latest_version": None,
                "expires_at": None,
                "expires_at_iso": None,
                "mirrorc_message": None,
            }
    else:
        ret = SimpleNamespace(
            code=MirrorCErrorCode.KEY_INVALID.value,
            message="CDK invalid.",
            latest_version_name=None
        )

    code = ret.code
    expires_ts = getattr(ret, "cdk_expired_time", None)
    expires_ts, expires_iso = _format_expired_time(expires_ts)

    base_messages = {
        MirrorCErrorCode.SUCCESS.value: (
            "CDK valid. Expires at {}" if expires_iso else "CDK valid."
        ),
        MirrorCErrorCode.KEY_EXPIRED.value: "CDK expired.",
        MirrorCErrorCode.KEY_INVALID.value: "CDK invalid.",
        MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value: "CDK quota exhausted for today.",
        MirrorCErrorCode.KEY_MISMATCHED.value: "CDK mismatched for requested resource.",
        MirrorCErrorCode.KEY_BLOCKED.value: "CDK blocked.",
    }
    message = base_messages.get(code, f"MirrorC returned code {code}.")

    data, path_setup_toml = read_setup_toml()
    data = migrate_to_current_schema(data)
    data["general"]["mirrorc_cdk"] = cdk if code == MirrorCErrorCode.SUCCESS.value else ""
    data["general"]["channel"] = channel
    write_setup_toml(data, path_setup_toml)

    return {
        "success": code == MirrorCErrorCode.SUCCESS.value,
        "code": code,
        "message": message,
        "mirrorc_message": getattr(ret, "message", None),
        "latest_version": getattr(ret, "latest_version_name", None),
        "expires_at": expires_ts,
        "expires_at_iso": expires_iso,
    }


def get_local_version(setup_path: Optional[Path] = None) -> Tuple["VersionInfo", Dict[str, Any], str]:
    data, path = read_setup_toml(setup_path)

    # Use GitOperationHandler to abstract system git vs pygit2
    git_ops = GitOperationHandler(Path.cwd())

    try:
        version_value, _branch = git_ops.get_local_head_info()
        data = migrate_to_current_schema(data)
        data["general"]["current_baas_sha"] = version_value
        write_setup_toml(data, path)
    except Exception:
        data = migrate_to_current_schema(data)
        version_value = data["general"].get("current_baas_sha", "")
        _branch = "master"

    return VersionInfo(version=version_value, source="setup.toml", path=path), data, _branch


def _select_remote_record(
    local_version: Optional[str],
    results: List[RepositoryResult],
) -> Optional[RepositoryResult]:
    for record in results:
        value = record.get("value")
        if not record.get("success") or not value:
            continue
        if not local_version:
            return record
        if len(value) == len(local_version):
            return record
    return next((record for record in results if record.get("success") and record.get("value")), None)


def check_for_update(timeout: float = 3.0) -> Dict[str, Any]:
    """
    Detect whether a newer version is available.

    The function compares the version retrieved from setup.toml with the first
    successful remote value (preferring matching formats) and returns a
    structured response that can be consumed by service endpoints.
    """
    try:
        if _is_android_runtime():
            setup_toml, path = read_setup_toml()
            setup_toml = migrate_to_current_schema(setup_toml)
            local_version = setup_toml["general"].get("current_baas_sha", "")
            if setup_toml["general"].get("no_update", False):
                return {
                    "local": local_version,
                    "remote": local_version,
                    "update_available": False,
                    "skipped": True,
                    "reason": "no_update",
                    "channel": setup_channel(setup_toml),
                    "method": "github",
                }
            channel = setup_channel(setup_toml)
            source = _github_archive_config(channel)
            success, remote_version = _github_api_get_latest_sha(source, timeout)
            if not success:
                remote_version = None
            return {
                "local": local_version,
                "remote": remote_version,
                "update_available": bool(local_version and remote_version and local_version != remote_version),
                "channel": channel,
                "method": "github",
                "setup_path": str(path),
            }

        local_info, setup_toml, _branch = get_local_version()
        setup_toml = migrate_to_current_schema(setup_toml)
        if setup_toml["general"].get("no_update", False):
            return {
                "local": local_info.version,
                "remote": local_info.version,
                "update_available": False,
                "skipped": True,
                "reason": "no_update",
                "channel": setup_channel(setup_toml),
                "method": setup_toml["general"].get("get_remote_sha_method"),
            }
        channel = setup_channel(setup_toml)
        setup_toml["general"]["channel"] = channel
        repo_methods = get_remote_sha_methods_for_channel(channel)
        method_name = setup_toml["general"].get("get_remote_sha_method", None)
        method_names = {method.get("name") for method in repo_methods}
        if method_name and method_name not in method_names:
            method_name = "github"
            setup_toml["general"]["get_remote_sha_method"] = method_name
            write_setup_toml(setup_toml, local_info.path)
        if not method_name:
            repo_results = test_all_repo_sha(timeout=timeout, channel=channel)
            selected = _select_remote_record(local_info.version, repo_results)
            method_name = selected.get("name") if selected else "github"
            setup_toml["general"]["get_remote_sha_method"] = method_name
            write_setup_toml(setup_toml, local_info.path)

        for ind, x in enumerate(repo_methods):
            x["channel"] = channel
            if "branch" in x:
                repo_methods[ind]["branch"] = _branch

        method_config = next((x for x in repo_methods if x.get('name') == method_name), repo_methods[0])
        repo_result = test_repo_sha(method_config, timeout=timeout)
        remote_version = repo_result.get("value") if repo_result else None

        update_available = (
            bool(local_info.version)
            and bool(remote_version)
            and local_info.version != remote_version
        )

        return {
            "local": local_info.version,
            "remote": remote_version,
            "update_available": update_available,
            "channel": channel,
            "method": method_config.get("name"),
        }

    except:
        import traceback
        traceback.print_exc()
        return {}


def _is_android_runtime() -> bool:
    return os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}


def _github_archive_config(channel: str) -> Dict[str, Any]:
    methods = get_remote_sha_methods_for_channel(channel)
    for method in methods:
        if method.get("method") == GetShaMethod.GITHUB_API:
            return method
    raise RuntimeError(f"No GitHub API update source configured for channel: {channel}")


def _copy_android_update_tree(source_root: Path, target_root: Path) -> None:
    keep_names = {
        "config",
        "log",
        "tmp",
        ".git",
        ".venv",
        ".env",
        "__pycache__",
        ".pytest_cache",
    }
    for item in source_root.iterdir():
        if item.name in keep_names:
            continue
        target = target_root / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        elif item.is_file() and item.name != "setup.toml":
            shutil.copy2(item, target)


def _android_update_to_latest(setup_path: Union[Path, None] = None) -> Dict[str, Any]:
    data, path = read_setup_toml(setup_path)
    data = migrate_to_current_schema(data)
    if data["general"].get("no_update", False):
        return {"status": "skipped", "reason": "no_update"}

    channel = setup_channel(data)
    source = _github_archive_config(channel)
    owner = source["owner"]
    repo = source["repo"]
    branch = source["branch"]
    ok, remote_sha = _github_api_get_latest_sha(source, 10.0)
    if not ok or not remote_sha:
        raise RuntimeError(f"Failed to fetch Android update SHA: {remote_sha}")

    archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
    target_root = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="baas-android-update-") as tmp_dir:
        tmp = Path(tmp_dir)
        archive_path = tmp / "repo.zip"
        response = requests.get(archive_url, stream=True, timeout=60)
        response.raise_for_status()
        with archive_path.open("wb") as fp:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    fp.write(chunk)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(tmp)
        roots = [child for child in tmp.iterdir() if child.is_dir()]
        if not roots:
            raise RuntimeError("Downloaded Android update archive is empty")
        _copy_android_update_tree(roots[0], target_root)

    data["general"]["current_baas_sha"] = remote_sha
    data["general"]["channel"] = channel
    data["paths"]["baas_root_path"] = "."
    write_setup_toml(data, path)
    return {
        "status": "updated",
        "current": remote_sha,
        "restart_required": True,
        "method": "github-archive",
        "channel": channel,
    }


def update_to_latest(setup_path: Union[Path, None] = None):
    if _is_android_runtime():
        return _android_update_to_latest(setup_path)
    data, path = read_setup_toml(setup_path)
    data = migrate_to_current_schema(data)
    if data["general"].get("no_update", False):
        return {"status": "skipped", "reason": "no_update"}
    update_repo_to_latest(data, path)
