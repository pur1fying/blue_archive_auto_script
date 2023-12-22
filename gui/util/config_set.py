import json

from core.notification import notify


class ConfigSet:
    def __init__(self):
        self.config = None
        self._init_config()

    def _init_config(self):
        with open('./config/config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def get(self, key):
        self._init_config()
        return self.config.get(key)

    def set(self, key, value):
        self._init_config()
        self.config[key] = value
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        if not self.check(key, value):
            notify('', '修改配置失败,请重新设置')
            print(f'failed to set config {key}')

    @staticmethod
    def check(key, value):
        with open('./config/config.json', 'r', encoding='utf-8') as f:
            new_config = json.load(f)
        return new_config.get(key) == value
