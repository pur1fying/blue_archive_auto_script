from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict

from deploy.installer.const import method_for_repo_url, normalize_update_channel, repo_url_for_method
from deploy.installer.toml_config import DEFAULT_SETTINGS as LEGACY_DEFAULT_SETTINGS

CURRENT_SCHEMA_VERSION = 1

CURRENT_DEFAULT_SETTINGS: Dict[str, Any] = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "general": {
        "mirrorc_cdk": "",
        "channel": "stable",
        "current_baas_sha": "",
        "current_baas_cpp_sha": "",
        "get_remote_sha_method": "",
        "launch": False,
        "force_launch": False,
        "debug": False,
        "no_update": False,
        "git_backend": "auto",
        "source_list": LEGACY_DEFAULT_SETTINGS["General"]["source_list"],
    },
    "paths": {
        "baas_root_path": "",
        "tmp_path": "tmp",
        "toolkit_path": "toolkit",
    },
    "python": {
        "runtime_path": "default",
        "python_version": "3.9.0",
    },
    "repositories": {
        "main_sources": [],
        "cpp_sources": [],
    },
}


def _table(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _first_string(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return ""


def _first_bool(default: bool, *values: Any) -> bool:
    for value in values:
        if isinstance(value, bool):
            return value
    return default


def setup_channel(data: Dict[str, Any]) -> str:
    general = _table(data, "general")
    legacy_general = _table(data, "General")
    return normalize_update_channel(
        general.get("channel")
        or legacy_general.get("channel")
        or ("dev" if legacy_general.get("dev") else "stable")
    )


def migrate_to_current_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    current = copy.deepcopy(CURRENT_DEFAULT_SETTINGS)
    general = _table(data, "general")
    paths = _table(data, "paths")
    python = _table(data, "python")
    repositories = _table(data, "repositories")
    legacy_general = _table(data, "General")
    legacy_paths = _table(data, "Paths")
    legacy_urls = _table(data, "URLs")

    current["schema_version"] = int(data.get("schema_version") or data.get("schemaVersion") or CURRENT_SCHEMA_VERSION)

    current_general = current["general"]
    current_general.update({key: value for key, value in general.items() if key in current_general})
    current_general["mirrorc_cdk"] = _first_string(
        general.get("mirrorc_cdk"),
        general.get("mirrorcCdk"),
        legacy_general.get("mirrorc_cdk"),
    )
    current_general["channel"] = setup_channel(data)
    current_general["current_baas_sha"] = _first_string(
        general.get("current_baas_sha"),
        general.get("currentBaasSha"),
        legacy_general.get("current_baas_sha"),
        legacy_general.get("current_baas_version"),
        legacy_general.get("current_BAAS_version"),
    )
    current_general["current_baas_cpp_sha"] = _first_string(
        general.get("current_baas_cpp_sha"),
        general.get("currentBaasCppSha"),
        legacy_general.get("current_baas_cpp_sha"),
        legacy_general.get("current_baas_cpp_version"),
        legacy_general.get("current_BAAS_Cpp_version"),
    )
    current_general["get_remote_sha_method"] = _first_string(
        general.get("get_remote_sha_method"),
        general.get("getRemoteShaMethod"),
        legacy_general.get("get_remote_sha_method"),
        method_for_repo_url(legacy_urls.get("REPO_URL_HTTP")),
    )
    current_general["launch"] = _first_bool(current_general["launch"], general.get("launch"), legacy_general.get("launch"))
    current_general["force_launch"] = _first_bool(
        current_general["force_launch"],
        general.get("force_launch"),
        general.get("forceLaunch"),
        legacy_general.get("force_launch"),
    )
    current_general["debug"] = _first_bool(current_general["debug"], general.get("debug"), legacy_general.get("debug"))
    current_general["no_update"] = _first_bool(
        current_general["no_update"],
        general.get("no_update"),
        general.get("noUpdate"),
        legacy_general.get("no_update"),
    )
    current_general["git_backend"] = (
        _first_string(general.get("git_backend"), general.get("gitBackend"))
        or current_general["git_backend"]
    )
    source_list = general.get("source_list") or general.get("sourceList") or legacy_general.get("source_list")
    if isinstance(source_list, list) and source_list:
        current_general["source_list"] = [str(item) for item in source_list]

    current_paths = current["paths"]
    current_paths.update({key: value for key, value in paths.items() if key in current_paths})
    current_paths["baas_root_path"] = _first_string(
        paths.get("baas_root_path"),
        paths.get("baasRootPath"),
        legacy_paths.get("BAAS_ROOT_PATH"),
    )
    current_paths["tmp_path"] = (
        _first_string(paths.get("tmp_path"), paths.get("tmpPath"), legacy_paths.get("TMP_PATH"))
        or current_paths["tmp_path"]
    )
    current_paths["toolkit_path"] = (
        _first_string(paths.get("toolkit_path"), paths.get("toolkitPath"), legacy_paths.get("TOOL_KIT_PATH"))
        or current_paths["toolkit_path"]
    )

    current_python = current["python"]
    current_python.update({key: value for key, value in python.items() if key in current_python})
    current_python["runtime_path"] = _first_string(
        python.get("runtime_path"),
        python.get("runtimePath"),
        legacy_general.get("runtime_path"),
    ) or current_python["runtime_path"]
    current_python["python_version"] = (
        _first_string(python.get("python_version"), python.get("pythonVersion"))
        or current_python["python_version"]
    )

    current_repositories = current["repositories"]
    current_repositories.update(
        {key: value for key, value in repositories.items() if key in current_repositories}
    )
    if isinstance(repositories.get("mainSources"), list):
        current_repositories["main_sources"] = repositories["mainSources"]
    if isinstance(repositories.get("cppSources"), list):
        current_repositories["cpp_sources"] = repositories["cppSources"]
    return current


def legacy_repo_url(data: Dict[str, Any]) -> str:
    current = migrate_to_current_schema(data)
    method = current["general"].get("get_remote_sha_method") or "github"
    return repo_url_for_method(method, current["general"].get("channel")) or ""


def legacy_runtime_view(data: Dict[str, Any]) -> Dict[str, Any]:
    current = migrate_to_current_schema(data)
    general = current["general"]
    paths = current["paths"]
    python = current["python"]
    repo_url = legacy_repo_url(current)
    return {
        "General": {
            "mirrorc_cdk": general["mirrorc_cdk"],
            "current_BAAS_version": general["current_baas_sha"],
            "current_BAAS_Cpp_version": general["current_baas_cpp_sha"],
            "get_remote_sha_method": general["get_remote_sha_method"],
            "channel": general["channel"],
            "dev": general["channel"] == "dev",
            "refresh": False,
            "launch": general["launch"],
            "force_launch": general["force_launch"],
            "internal_launch": False,
            "no_build": True,
            "debug": general["debug"],
            "use_dynamic_update": False,
            "no_update": general["no_update"],
            "git_backend": general["git_backend"],
            "source_list": general["source_list"],
            "package_manager": "pip",
            "runtime_path": python["runtime_path"],
            "linux_pwd": "",
        },
        "URLs": {
            **LEGACY_DEFAULT_SETTINGS["URLs"],
            "REPO_URL_HTTP": repo_url,
        },
        "Paths": {
            "BAAS_ROOT_PATH": paths["baas_root_path"] or str(Path.cwd()),
            "TMP_PATH": paths["tmp_path"],
            "TOOL_KIT_PATH": paths["toolkit_path"],
        },
    }


def set_general(data: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    current = migrate_to_current_schema(data)
    current["general"][key] = value
    if key == "channel":
        current["general"]["channel"] = normalize_update_channel(value)
    return current


def set_path(data: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    current = migrate_to_current_schema(data)
    current["paths"][key] = value
    return current
