from __future__ import annotations

import time
import os
import pygit2
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from typing import Callable, Union, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Optional

import requests

from deploy.installer.const import GetShaMethod, get_remote_sha_methods_for_channel, normalize_update_channel
from deploy.installer.mirrorc_update.const import MirrorCErrorCode
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater

from deploy.installer.git_backend import remote_branch_sha, rollback_repository
from service.update.repository import update_repo_to_latest
from service.update.setup_io import read_setup_toml, write_setup_toml
from service.update.setup_schema import migrate_to_current_schema, setup_channel

RepositoryResult = Dict[str, Any]

class GitOperationHandler:
    """Read and roll back repositories exclusively through pygit2."""

    def __init__(self, repo_path: Union[str, Path] = "."):
        self.repo_path = Path(repo_path)

    def get_remote_latest_sha(self, url: str, branch: str, timeout: Optional[float] = None) -> str:
        try:
            return remote_branch_sha(url, branch, timeout=timeout)
        except Exception as exc:
            raise ValueError(f"Unable to read remote branch '{branch}' at {url}: {exc}") from exc

    def get_local_head_info(self) -> Tuple[str, str]:
        repo = pygit2.Repository(str(self.repo_path))
        try:
            return str(repo.head.target), "HEAD" if repo.head_is_detached else repo.head.shorthand
        finally:
            repo.free()

    def rollback(self, target_sha: str):
        repo = pygit2.Repository(str(self.repo_path))
        try:
            rollback_repository(repo, target_sha)
        finally:
            repo.free()


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


def _git_wrapper_get_latest_sha(config: Dict[str, Any], timeout: Optional[float] = None) -> Tuple[bool, str]:
    """Read a remote SHA with the shared pygit2 backend."""
    url = config["url"]
    branch = config["branch"]

    git_ops = GitOperationHandler(Path.cwd())

    try:
        sha = git_ops.get_remote_latest_sha(url, branch, timeout=timeout)
        return True, sha
    except Exception as exc:
        return False, str(exc)


def _github_repo_from_url(url: str) -> Optional[Tuple[str, str]]:
    lower_url = url.lower()
    marker = "github.com/"
    marker_index = lower_url.find(marker)
    if marker_index >= 0:
        tail = url[marker_index + len(marker):]
    else:
        parsed = urlparse(url)
        if parsed.netloc.lower() != "githubfast.com":
            return None
        tail = parsed.path.lstrip("/")

    tail = tail.split("?", 1)[0].split("#", 1)[0].strip("/")
    parts = [part for part in tail.split("/") if part]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _github_archive_url_for_config(config: Dict[str, Any]) -> Optional[str]:
    source_url = str(config.get("url") or "")
    repo_parts = _github_repo_from_url(source_url)
    if not repo_parts:
        owner = config.get("owner")
        repo = config.get("repo")
        if not owner or not repo:
            return None
        repo_parts = (str(owner), str(repo))

    owner, repo = repo_parts
    branch = str(config.get("branch") or "master")
    github_archive_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    parsed = urlparse(source_url)
    host = parsed.netloc.lower()
    scheme = parsed.scheme or "https"

    if host in {"v4.gh-proxy.org", "v6.gh-proxy.org", "cdn.gh-proxy.org", "gh-proxy.org", "gh.sevencdn.com"}:
        return f"{scheme}://{host}/{github_archive_url}"
    if host == "githubfast.com":
        return f"{scheme}://{host}/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    if host == "baas-cdn.kiramei.workers.dev":
        return f"{scheme}://{host}/{github_archive_url}"
    return f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"


def _probe_android_archive_url(archive_url: str, timeout: float) -> Tuple[bool, str]:
    connect_timeout = min(max(float(timeout), 1.0), 8.0)
    read_timeout = max(float(timeout), connect_timeout)
    headers = {
        "User-Agent": "BAAS-Android",
        "Range": "bytes=0-0",
    }
    try:
        with requests.get(
            archive_url,
            stream=True,
            timeout=(connect_timeout, read_timeout),
            headers=headers,
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=1):
                if chunk:
                    break
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _android_http_get_latest_sha(config: Dict[str, Any], timeout: float) -> Tuple[bool, str]:
    repo_parts = _github_repo_from_url(str(config.get("url") or ""))
    archive_url = _github_archive_url_for_config(config)
    if not repo_parts or not archive_url:
        return _git_wrapper_get_latest_sha(config, timeout)

    ok, error = _probe_android_archive_url(archive_url, timeout)
    if not ok:
        return False, error

    owner, repo = repo_parts
    github_config = {
        "owner": owner,
        "repo": repo,
        "branch": str(config.get("branch") or "master"),
    }
    success, sha = _github_api_get_latest_sha(github_config, timeout)
    if not success:
        return False, f"Archive source reachable, but GitHub API SHA lookup failed: {sha}"
    return True, sha


def repo_sha_test_configs(channel: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return normalized repository SHA test configs for a channel."""
    channel = normalize_update_channel(channel or _setup_channel()[0])
    return [
        {**config, "channel": channel, "order": index}
        for index, config in enumerate(get_remote_sha_methods_for_channel(channel))
    ]


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
    elif _is_android_runtime():
        success, value = _android_http_get_latest_sha(config, timeout)
    else:
        success, value = _git_wrapper_get_latest_sha(config, timeout)
    elapsed = time.perf_counter() - start
    result: RepositoryResult = {
        "name": config.get("name"),
        "method": method.name,
        "duration": elapsed,
        "success": success,
        "value": value if success else None,
        "error": None if success else value,
        "order": int(config.get("order", 0)) if success else -1,
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
        if not repo_result.get("success"):
            fallback_results = []
            for candidate in repo_methods:
                if candidate.get("name") == method_config.get("name"):
                    continue
                candidate_result = test_repo_sha(candidate, timeout=timeout)
                fallback_results.append(candidate_result)
                if candidate_result.get("success") and candidate_result.get("value"):
                    method_config = candidate
                    repo_result = candidate_result
                    setup_toml["general"]["get_remote_sha_method"] = candidate.get("name")
                    write_setup_toml(setup_toml, local_info.path)
                    break
            else:
                selected = _select_remote_record(local_info.version, fallback_results)
                if selected:
                    selected_name = selected.get("name")
                    method_config = next(
                        (x for x in repo_methods if x.get("name") == selected_name),
                        method_config,
                    )
                    repo_result = selected
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


def _android_archive_config(data: Dict[str, Any], channel: str) -> Dict[str, Any]:
    methods = get_remote_sha_methods_for_channel(channel)
    method_name = data.get("general", {}).get("get_remote_sha_method")
    if method_name:
        selected = next((method for method in methods if method.get("name") == method_name), None)
        if selected and _github_archive_url_for_config(selected):
            return selected
    return _github_archive_config(channel)


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


def _android_update_to_latest(
    setup_path: Union[Path, None] = None,
    progress: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    def emit(stage: str, **payload: Any) -> None:
        if progress:
            progress(stage, payload)

    emit("read_setup")
    data, path = read_setup_toml(setup_path)
    data = migrate_to_current_schema(data)
    if data["general"].get("no_update", False):
        emit("skipped", reason="no_update")
        return {"status": "skipped", "reason": "no_update"}

    channel = setup_channel(data)
    github_source = _github_archive_config(channel)
    archive_source = _android_archive_config(data, channel)
    emit("fetch_sha", channel=channel, method=archive_source.get("name") or "github")
    ok, remote_sha = _github_api_get_latest_sha(github_source, 10.0)
    if not ok or not remote_sha:
        raise RuntimeError(f"Failed to fetch Android update SHA: {remote_sha}")
    emit("remote_sha", sha=remote_sha)

    archive_url = _github_archive_url_for_config(archive_source)
    if not archive_url:
        raise RuntimeError(f"Failed to resolve Android update archive URL for source: {archive_source.get('name')}")
    target_root = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="baas-android-update-") as tmp_dir:
        tmp = Path(tmp_dir)
        archive_path = tmp / "repo.zip"
        emit("download_start", url=archive_url)
        response = requests.get(archive_url, stream=True, timeout=60)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length") or 0)
        downloaded = 0
        last_reported = 0
        with archive_path.open("wb") as fp:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    fp.write(chunk)
                    downloaded += len(chunk)
                    if downloaded - last_reported >= 1024 * 1024:
                        last_reported = downloaded
                        emit("download_progress", downloaded=downloaded, total=total_size)
        emit("download_done", downloaded=downloaded, total=total_size)
        emit("extract_start")
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(tmp)
        roots = [child for child in tmp.iterdir() if child.is_dir()]
        if not roots:
            raise RuntimeError("Downloaded Android update archive is empty")
        emit("copy_start", source=str(roots[0]), target=str(target_root))
        _copy_android_update_tree(roots[0], target_root)
        emit("copy_done")

    data["general"]["current_baas_sha"] = remote_sha
    data["general"]["channel"] = channel
    data["paths"]["baas_root_path"] = "."
    emit("write_setup", path=str(path))
    write_setup_toml(data, path)
    emit("done", sha=remote_sha)
    return {
        "status": "updated",
        "current": remote_sha,
        "restart_required": True,
        "method": archive_source.get("name") or "github-archive",
        "channel": channel,
    }


def update_to_latest_with_progress(
    setup_path: Union[Path, None] = None,
    progress: Optional[Callable[[str, Dict[str, Any]], None]] = None,
):
    if _is_android_runtime():
        return _android_update_to_latest(setup_path, progress=progress)
    if progress:
        progress("update_start", {})
    data, path = read_setup_toml(setup_path)
    data = migrate_to_current_schema(data)
    if data["general"].get("no_update", False):
        if progress:
            progress("skipped", {"reason": "no_update"})
        return {"status": "skipped", "reason": "no_update"}
    update_repo_to_latest(data, path)
    if progress:
        progress("done", {})


def update_to_latest(setup_path: Union[Path, None] = None):
    return update_to_latest_with_progress(setup_path)
