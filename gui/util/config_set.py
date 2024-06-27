import json
from core.notification import notify
from gui.util.translator import baasTranslator as bt


class ConfigSet:
    def __init__(self, config_dir):
        print(config_dir)
        self.config = None
        self.server_mode = 'CN'
        self.main_thread = None
        self.static_config = None
        self.config_dir = config_dir
        self.signals = {}
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
        
    def get(self, key):
        self._init_config()
        value = self.config.get(key)
        return bt.tr('ConfigTranslation', value)

    def set(self, key, value):
        self._init_config()
        value = bt.undo(value)
        self.config[key] = value
        with open(f'./config/{self.config_dir}/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def update(self, key, value):
        self.set(key, value)

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

    def set_main_thread(self, thread):
        self.main_thread = thread

    def get_main_thread(self):
        return self.main_thread
