import json
import re

from PyQt5.QtCore import QObject

from gui.util.translator import baasTranslator as bt


class BoundComponent(QObject):
    """
    BoundComponent is a class that binds a component to a string rule. The string rule is a string that contains
    placeholders that are keys in the config. When the config is updated, the component will be updated with the new
    value. The rule string is a definition of how the component should be updated. For example, if the rule is
    "Title: {title} - Subtitle: {subtitle}", the component will be updated with the new value of the title and subtitle
    keys in the config.

    :param component: Component to bind
    :param string_rule: String rule to bind
    :param config_manager: Config manager
    :param attribute: Attribute to bind (default is setText)
    """
    def __init__(self, component,  string_rule, config_manager, attribute="setText"):
        super().__init__()
        self.component = component
        self.attribute = attribute
        self.string_rule = string_rule
        self.config_manager = config_manager

        self.update_component()  # 初始化时更新组件

    def update_component(self):
        """ Update the component with the new value """
        # Replace the keys in the rule with the values in the config
        new_value = self.string_rule
        keys_in_rule = re.findall(r'{(.*?)}', self.string_rule)
        for key in keys_in_rule:
            new_value = new_value.replace(f'{{{key}}}', self.config_manager.config.get(key, ''))

        # Dynamic call the attribute function of the component
        getattr(self.component, self.attribute)(new_value)

    def config_updated(self, key):
        if f'{{{key}}}' in self.string_rule:
            self.update_component()


class ConfigSet:
    def __init__(self, config_dir):
        super().__init__()
        print(config_dir)
        self.config = None
        self.server_mode = 'CN'
        self.inject_comp_list = []
        self.inject_config_list = []
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
        elif self.config['server'] in ['国际服', '国际服青少年', '韩国ONE']:
            self.server_mode = 'Global'
        elif self.config['server'] == '日服':
            self.server_mode = 'JP'

    def get(self, key):
        self._init_config()
        value = self.config.get(key)
        return bt.tr('ConfigTranslation', value)

    def get_origin(self, key):
        self._init_config()
        return self.config.get(key)

    def set(self, key, value):
        self._init_config()
        value = bt.undo(value)
        self.config[key] = value
        with open(f'./config/{self.config_dir}/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        self.dynamic_update(key)

    def dynamic_update(self, key):
        if key not in self.inject_config_list: return
        for comp in self.inject_comp_list:
            comp.config_updated(key)

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
