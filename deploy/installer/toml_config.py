import os
import tomli_w

DEFAULT_SETTINGS = {
    "General": {
        "mirrorc_cdk": "",
        "current_BAAS_version": "",
        "current_BAAS_Cpp_version": "",
        "get_remote_sha_method": "",
        "dev": False,
        "refresh": False,
        "launch": False,
        "force_launch": False,
        "internal_launch": False,
        "no_build": True,
        "debug": False,
        "use_dynamic_update": False,
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
        keys = key.split('.')
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set(self, key, value):
        keys = key.split('.')
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def contains(self, key):
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
