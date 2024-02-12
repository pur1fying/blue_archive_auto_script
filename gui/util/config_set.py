import json
from core.notification import notify


class ConfigSet:
    def __init__(self, config_dir):
        print(config_dir)
        self.config = None
        # Config Server Mode 0: CN, 1: EN, 2: JP
        self.server_mode = 0
        self.static_config = None
        self.config_dir = config_dir
        self._init_config()

    def _init_config(self):
        with open(f'./config/{self.config_dir}/config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        with open("config/static.json", 'r', encoding='utf-8') as f:
            self.static_config = json.load(f)
        if self.config['server'] == '国服' or self.config['server'] == 'B服':
            self.server_mode = 0
        elif self.config['server'] == '国际服':
            self.server_mode = 1
        elif self.config['server'] == '日服':
            self.server_mode = 2

    def get(self, key):
        self._init_config()
        return self.config.get(key)

    def set(self, key, value):
        self._init_config()
        self.config[key] = value
        with open(f'./config/{self.config_dir}/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        if not self.check(key, value):
            notify('', '修改配置失败,请重新设置')
            print(f'failed to set config {key}')

    def __getitem__(self, item: str):
        return self.config[item]

    def check(self, key, value):
        with open(f'./config/{self.config_dir}/config.json', 'r', encoding='utf-8') as f:
            new_config = json.load(f)
        return new_config.get(key) == value
