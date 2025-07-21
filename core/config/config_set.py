import json
import os
import re
from core.config.generated_user_config import Config
from core.config.generated_static_config import StaticConfig
from gui.util.customed_ui import BoundComponent
from gui.util.translator import baasTranslator as bt
from dataclasses import asdict


class ConfigSet:
    static_config: StaticConfig = None

    def __init__(self, config_dir):
        # change happens in self.config ( dataclass )
        # save change : dataclass --> dict --> json_str
        super().__init__()
        if ConfigSet.static_config is None:
            ConfigSet._init_static_config()
        self.config: Config
        self.config_dir = None
        if os.path.exists(f'config/{config_dir}/config.json'):  # relative path
            self.config_dir = os.path.abspath(f'config/{config_dir}')
        elif os.path.exists(f'{config_dir}/config.json'):  # absolute path
            self.config_dir = config_dir
        else:
            raise FileNotFoundError(f'config/{config_dir}/config.json not found')
        self.server_mode = 'CN'
        self._init_config()
        self.inject_comp_list = []
        self.inject_config_list = []
        self.window = None
        self.main_thread = None
        self.signals = {}

    @staticmethod
    def _init_static_config():
        with open('config/static.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            ConfigSet.static_config = StaticConfig(**data)

    def _init_config(self):
        with open(os.path.join(self.config_dir, "config.json"), 'r', encoding='utf-8') as f:
            self.config = Config(**json.load(f))
        self.server_mode = self.get_server_mode(self.config.server)

    @staticmethod
    def get_server_mode(server):
        if server in ['官服', 'B服']:
            return 'CN'
        if server in ['国际服', '国际服青少年', '韩国ONE', 'Steam国际服']:
            return 'Global'
        if server in ['日服']:
            return 'JP'

    def get(self, key, default=None):
        self._init_config()
        value = getattr(self.config, key, default)
        return bt.tr('ConfigTranslation', value)

    def set(self, key, value):
        self._init_config()
        value = bt.undo(value)
        setattr(self.config, key, value)
        self.save()
        self.dynamic_update(key)

    def update(self, key, value):
        self.set(key, value)

    def save(self):
        data = asdict(self.config)
        with open(os.path.join(self.config_dir, "config.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def dynamic_update(self, key):
        if key not in self.inject_config_list: return
        for comp in self.inject_comp_list:
            comp.config_updated(key)

    def __getitem__(self, item: str):
        return self.get(item)

    def add_signal(self, key, signal):
        self.signals[key] = signal

    def get_signal(self, key):
        return self.signals.get(key)

    def get_signals(self):
        return self.signals

    def set_window(self, window):
        self.window = window

    def get_window(self):
        return self.window

    def set_main_thread(self, thread):
        self.main_thread = thread

    def get_main_thread(self):
        return self.main_thread

    def inject(self, component, string_rule, attribute="setText"):
        """
        Inject a component with a string rule
        :param component: Component to inject
        :param string_rule: String rule
        :param attribute: Attribute to inject (default is setText)
        :return: BoundComponent, which can be ignored
        """
        bounded = BoundComponent(component, string_rule, self, attribute)
        self.inject_config_list.extend(re.findall(r'{(.*?)}', string_rule))
        self.inject_comp_list.append(bounded)
        return bounded

    def update_create_quantity_entry(self):
        dft = self.static_config.create_item_order[self.server_mode]["basic"]
        dft_list = [item for sublist in dft.values() for item in sublist]
        pop_list = []
        for key in self.config.create_item_holding_quantity:
            if key not in dft_list:
                pop_list.append(key)
        for key in pop_list:
            self.config.create_item_holding_quantity.pop(key)

        for entry in dft_list:
            if entry not in self.config.create_item_holding_quantity:
                self.config.create_item_holding_quantity[entry] = -1
        self.save()
