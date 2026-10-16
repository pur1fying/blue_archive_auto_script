import os
import tomli_w

# The service schema and the desktop UI share one setup.toml. Keep these
# aliases here so reading desktop settings never imports the service runtime.
_SETUP_KEY_ALIASES = {
    "General.mirrorc_cdk": "general.mirrorc_cdk",
    "General.current_BAAS_version": "general.current_baas_sha",
    "General.current_BAAS_Cpp_version": "general.current_baas_cpp_sha",
    "General.get_remote_sha_method": "general.get_remote_sha_method",
    "General.channel": "general.channel",
    "General.launch": "general.launch",
    "General.force_launch": "general.force_launch",
    "General.debug": "general.debug",
    "General.no_update": "general.no_update",
    "General.git_backend": "general.git_backend",
    "General.source_list": "general.source_list",
    "General.runtime_path": "python.runtime_path",
    "Paths.BAAS_ROOT_PATH": "paths.baas_root_path",
    "Paths.TMP_PATH": "paths.tmp_path",
    "Paths.TOOL_KIT_PATH": "paths.toolkit_path",
}

DEFAULT_SETTINGS = {
    "General": {
        "mirrorc_cdk": "",
        "current_BAAS_version": "",
        "current_BAAS_Cpp_version": "",
        "get_remote_sha_method": "",
        "channel": "stable",
        "dev": False,
        "refresh": False,
        "launch": False,
        "force_launch": False,
        "internal_launch": False,
        "no_build": True,
        "debug": False,
        "use_dynamic_update": False,
        "no_update": False,
        "source_list": [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.ustc.edu.cn/pypi/web/simple",
            "https://mirrors.aliyun.com/pypi/simple",
            "https://pypi.doubanio.com/simple",
            "https://mirrors.huaweicloud.com/repository/pypi/simple",
            "https://mirrors.cloud.tencent.com/pypi/simple",
            "https://mirrors.163.com/pypi/simple",
            "https://pypi.python.org/simple",
            "https://pypi.org/simple",
        ],
        "package_manager": "pip",
        "runtime_path": "default",
        "linux_pwd": "",
    },
    "URLs": {
        "REPO_URL_HTTP": "https://gitee.com/pur1fy/blue_archive_auto_script.git",
        "GET_PIP_URL": "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py",
        "GET_UPX_URL": "https://ghp.ci/https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip",
        "GET_ENV_PATCH_URL": "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/env_patch.zip",
        "GET_PYTHON_URL": "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip",
    },
    "Paths": {
        "BAAS_ROOT_PATH": "",
        "TMP_PATH": "tmp",
        "TOOL_KIT_PATH": "toolkit",
    },
}

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


class TOML_Config:
    def __init__(self, config_path):
        if os.path.exists(config_path):
            self.config_path = config_path
        else:
            raise FileNotFoundError(f"TOML File [ '{config_path}' ] does not exist.")
        self.config = None
        self._init_config()
        self.signals = None

    def _init_config(self):
        with open(self.config_path, 'rb') as f:
            self.config = tomllib.load(f)

    def get(self, key, default=None):
        if "general" in self.config:
            if key in ("General", "URLs", "Paths"):
                table = dict(DEFAULT_SETTINGS[key])
                table.update(self.config.get(key, {}))
                for legacy_key, alias in _SETUP_KEY_ALIASES.items():
                    if legacy_key.startswith(key + ".") and self.contains(alias):
                        table[legacy_key.split(".", 1)[1]] = self.get(alias)
                if key == "General":
                    table["dev"] = self.get("General.dev", table["dev"])
                elif key == "URLs":
                    table["REPO_URL_HTTP"] = self.get("URLs.REPO_URL_HTTP", table["REPO_URL_HTTP"])
                return table
            if key == "General.dev" and "channel" in self.config["general"]:
                return self.config["general"].get("channel", "stable") == "dev"
            if key == "URLs.REPO_URL_HTTP":
                try:
                    from .const import repo_url_for_method
                except ImportError:  # Standalone installer.py
                    from const import repo_url_for_method
                general = self.config["general"]
                url = repo_url_for_method(
                    general.get("get_remote_sha_method"), general.get("channel", "stable")
                )
                if url:
                    return url
            alias = _SETUP_KEY_ALIASES.get(key)
            if alias and self.contains(alias):
                return self.get(alias, default)
        keys = key.split('.')
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set(self, key, value):
        if "general" in self.config:
            alias = _SETUP_KEY_ALIASES.get(key)
            if alias:
                self.set(alias, value)
            elif key == "General.dev":
                self.set("general.channel", "dev" if value else "stable")
            elif key == "URLs.REPO_URL_HTTP":
                try:
                    from .const import CHANNEL_REPO_SHA_METHODS, method_for_repo_url
                except ImportError:  # Standalone installer.py
                    from const import CHANNEL_REPO_SHA_METHODS, method_for_repo_url
                self.set("general.get_remote_sha_method", method_for_repo_url(value) or "")
                for channel, sources in CHANNEL_REPO_SHA_METHODS.items():
                    if any(source.get("url") == value for source in sources):
                        self.set("general.channel", channel)
                        break
        keys = key.split('.')
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def contains(self, key):
        if "general" in self.config and key in _SETUP_KEY_ALIASES:
            return self.contains(_SETUP_KEY_ALIASES[key])
        keys = key.split('.')
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        return True

    def set_and_save(self, key, value):
        self.set(key, value)
        self.save()

    def delete(self, key):
        if "general" in self.config and key in _SETUP_KEY_ALIASES:
            self.delete(_SETUP_KEY_ALIASES[key])
        keys = key.split('.')
        current = self.config

        for key in keys[:-1]:
            if key in current:
                current = current[key]
            else:
                return False

        final_key = keys[-1]
        if final_key in current:
            del current[final_key]
        return True

    def save(self):
        with open(self.config_path, 'wb') as f:
            tomli_w.dump(self.config, f)

    def add_signal(self, key, signal):
        self.signals[key] = signal

    def get_signal(self, key):
        return self.signals.get(key)

    def get_signals(self):
        return self.signals

    def set_signals(self, signals):
        self.signals = signals
