import os
import tomli_w

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
