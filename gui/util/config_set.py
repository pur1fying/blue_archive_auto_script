import json
from core.notification import notify
from gui.i18n.language import baasTranslator as bt
from gui.i18n.config_translation import ConfigTranslation


class ConfigSet:
    def __init__(self, config_dir):
        print(config_dir)
        self.config = None
        self.server_mode = 'CN'
        self.static_config = None
        self.config_dir = config_dir
        self.signals = {}
        self.translation = ConfigTranslation()
        self._init_config()

    def _init_config(self):
        with open(f'./config/{self.config_dir}/config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        with open("config/static.json", 'r', encoding='utf-8') as f:
            self.static_config = json.load(f)
        if self.config['server'] == '国服' or self.config['server'] == 'B服':
            self.server_mode = 'CN'
        elif self.config['server'] == '国际服':
            self.server_mode = 'Global'
        elif self.config['server'] == '日服':
            self.server_mode = 'JP'

    def serialize(self, value):
        # i18n to Chinese
        if isinstance(value, str):
            if self.translation.get(value):
                value = self.translation.get(value)
        return value

    def deserialize(self, value):
        # Chinese to i18n
        if isinstance(value, str):
            value = bt.tr('ConfigTranslation', value)
        return value
        
    def get(self, key):
        self._init_config()
        value = self.config.get(key)
        return self.deserialize(value)

    def set(self, key, value):
        self._init_config()
        value = self.serialize(value)
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

    def add_signal(self, key, signal):
        self.signals[key] = signal

    def get_signal(self, key):
        return self.signals.get(key)
