from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple, Union

import pygit2
import requests
import tomli_w

try:  # Python 3.11+
    import tomllib  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[import]

from deploy.installer.const import GetShaMethod, get_remote_sha_methods
from deploy.installer.mirrorc_update.const import MirrorCErrorCode
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater
from deploy.installer.toml_config import DEFAULT_SETTINGS

RepositoryResult = Dict[str, Any]


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


def _mirrorc_api_get_latest_sha(timeout: float) -> Tuple[bool, str]:
    mirrorc_inst = MirrorC_Updater(app="BAAS_repo", current_version="")
    try:
        ret = mirrorc_inst.get_latest_version(cdk="", timeout=timeout)
        if ret.has_data and ret.latest_version_name:
            return True, ret.latest_version_name
        return False, ret.message
    except Exception as exc:  # pragma: no cover - external dependency
        return False, str(exc)


def _pygit2_get_latest_sha(config: Dict[str, Any]) -> Tuple[bool, str]:
    url = config["url"]
    branch = config["branch"]
    target_ref = f"refs/heads/{branch}"
    try:
        git = pygit2.Repository(".")
        remote = git.remotes.create_anonymous(url)
        for head in remote.ls_remotes():
            if head.get("name") == target_ref:
                return True, str(head.get("oid"))
        return False, f"Branch '{branch}' not found at {url}"
    except Exception as exc:
        return False, str(exc)


def test_all_repo_sha(timeout: float = 3.0) -> List[RepositoryResult]:
    """Test every configured repository and return timing + SHA details."""
    results: List[RepositoryResult] = []
    for config in get_remote_sha_methods:
        result = test_repo_sha(config, timeout)
        results.append(result)
    return results


def test_repo_sha(config: dict[str, Union[str, GetShaMethod]], timeout: float) -> dict[str, Any]:
    method = config["method"]
    start = time.perf_counter()
    if method == GetShaMethod.GITHUB_API:
        success, value = _github_api_get_latest_sha(config, timeout)
    elif method == GetShaMethod.MIRRORC_API:
        success, value = _mirrorc_api_get_latest_sha(timeout)
    else:
        success, value = _pygit2_get_latest_sha(config)
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


def validate_cdk(cdk: str, timeout: float = 3.0) -> Dict[str, Any]:
    """Validate a MirrorC CDK and return structured status information."""
    if cdk != "":
        updater = MirrorC_Updater(app="BAAS_repo", current_version="")
        try:
            ret = updater.get_latest_version(cdk=cdk, timeout=timeout)
        except requests.RequestException as exc:
            data, path_setup_toml = read_setup_toml()
            data["General"]["mirrorc_cdk"] = ""
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
            data["General"]["mirrorc_cdk"] = ""
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
    data["General"]["mirrorc_cdk"] = cdk if code == MirrorCErrorCode.SUCCESS.value else ""
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
    general_section = data.get("General", {})
    version_value = general_section.get("current_BAAS_version")
    try:
        repo = pygit2.Repository(Path.cwd())
        _branch = repo.head.shorthand
        if not version_value:
            commit = repo.revparse_single("HEAD")
            version_value = str(commit.id)
            data.setdefault("General", {})["current_BAAS_version"] = version_value
            with path.open("wb") as file:
                tomli_w.dump(data, file)
    except Exception:
        version_value = ""
        _branch = "master"

    return VersionInfo(version=version_value, source="setup.toml", path=path), data, _branch


def read_setup_toml(setup_path: Union[Path, None] = None) -> tuple[dict[str, Any], Union[Path, None]]:
    path = setup_path or (Path.cwd() / "setup.toml")
    if not path.exists():
        with path.open("wb") as file:
            tomli_w.dump(DEFAULT_SETTINGS, file)

    with path.open("rb") as fp:
        data = tomllib.load(fp)
    return data, path


def write_setup_toml(content: dict, setup_path: Union[Path, None] = None) -> None:
    path = setup_path or (Path.cwd() / "setup.toml")
    if not path.exists():
        with path.open("wb") as file:
            tomli_w.dump(DEFAULT_SETTINGS, file)

    with path.open("wb") as fp:
        tomli_w.dump(content, fp)


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
        local_info, setup_toml, _branch = get_local_version()
        method_name = setup_toml.setdefault("General", {}).get("get_remote_sha_method", None)
        if not method_name:
            repo_results = test_all_repo_sha(timeout=timeout)
            method_name = _select_remote_record(local_info.version, repo_results).get("name")
            setup_toml.setdefault("General", {})["get_remote_sha_method"] = method_name
            with local_info.path.open("wb") as file:
                tomli_w.dump(setup_toml, file)

        for ind, x in enumerate(get_remote_sha_methods):
            if "branch" in x:
                get_remote_sha_methods[ind]["branch"] = _branch

        method_config = list(filter(lambda x: x.get('name') == method_name, get_remote_sha_methods))[0]
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
            "update_available": update_available
        }

    except:
        import traceback
        traceback.print_exc()
        return {}


__all__ = [
    "check_for_update",
    "test_all_repo_sha",
    "validate_cdk",
    "VersionInfo",
    "read_setup_toml",
    "write_setup_toml"
]
