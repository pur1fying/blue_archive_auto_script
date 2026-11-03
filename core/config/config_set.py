# -*- coding: utf-8 -*-
"""ConfigSet 薄补丁：支持插件配置字段注册，不改 Config dataclass / DEFAULT_CONFIG。

相对上游改动：
- _init_config：json.load 后 merge 插件默认；Config(**filtered)；extras setattr
- save：asdict 后再并入插件键
- get：缺字段时回落插件默认 / getattr extras
- 关键：get/set 不再每次整表重读磁盘（否则内存里刚 setattr 的插件键会被冲掉，
  且连续 set 两个键时第二个 _init_config 可能读到旧盘）
"""
import json
import os
import re
from core.config.generated_user_config import Config
from core.config.generated_static_config import StaticConfig
from gui.util.customized_ui import BoundComponent
from gui.util.translator import baasTranslator as bt
from dataclasses import asdict, fields


def _ensure_tools_defaults_loaded():
    """触发工具注册表加载 → 各插件 register_config_defaults。"""
    try:
        from module.tools.registry import get_registry

        get_registry()
    except Exception:
        pass


def _config_field_names():
    try:
        return {f.name for f in fields(Config)}
    except Exception:
        return set()


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
        self._loaded = False
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

    def _init_config(self, force: bool = False):
        """从磁盘加载一次；force=True 才强制重读。"""
        if self._loaded and not force and getattr(self, "config", None) is not None:
            return
        _ensure_tools_defaults_loaded()
        with open(os.path.join(self.config_dir, "config.json"), 'r', encoding='utf-8') as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raw = {}
        try:
            from module.tools.config_registry import merge_plugin_defaults, apply_extras_to_config
            raw = merge_plugin_defaults(raw)
        except Exception:
            apply_extras_to_config = None  # type: ignore
        known = _config_field_names()
        if known:
            core = {k: v for k, v in raw.items() if k in known}
        else:
            core = dict(raw)
        try:
            self.config = Config(**core)
        except TypeError:
            # 兼容：丢弃未知键
            sig = set(getattr(Config, '__dataclass_fields__', {}) or {})
            core = {k: v for k, v in raw.items() if k in sig} if sig else core
            self.config = Config(**core)
            known = sig or known
        if apply_extras_to_config:
            try:
                apply_extras_to_config(self.config, raw, known or set())
            except Exception:
                pass
        # 再保险：插件键即使不在 raw 也挂上默认
        try:
            from module.tools.config_registry import registered_defaults
            for k, v in registered_defaults().items():
                if not hasattr(self.config, k):
                    try:
                        setattr(self.config, k, v)
                    except Exception:
                        pass
        except Exception:
            pass
        self.server_mode = self.get_server_mode(self.config.server)
        # 侧车：把 extras / 注册默认同步一份，后续 set/save 不丢
        try:
            side = {}
            from module.tools.config_registry import registered_defaults
            for k, v in registered_defaults().items():
                if hasattr(self.config, k):
                    side[k] = getattr(self.config, k)
                else:
                    side[k] = v
            for k in (
                "home_layout_order",
                "tool_assets_enabled",
                "tool_assets_home_edit",
                "tool_assets_home_edit_entry",
                "tool_assets_home_switch_entry",
                "assetsVisibility",
                "tool_equip_farm_home_entry",
                "tool_auto_push_home_entry",
            ):
                if hasattr(self.config, k):
                    side[k] = getattr(self.config, k)
            self._plugin_side = side
        except Exception:
            if not hasattr(self, "_plugin_side"):
                self._plugin_side = {}
        self._loaded = True

    def reload(self):
        """显式从磁盘重载（一般不用；切账号时调）。"""
        self._loaded = False
        self._init_config(force=True)

    @staticmethod
    def get_server_mode(server):
        if server in ['官服', 'B服']:
            return 'CN'
        if server in ['国际服', '国际服青少年', '韩国ONE', 'Steam国际服']:
            return 'Global'
        if server in ['日服', '日服PC端']:
            return 'JP'

    def get(self, key, default=None):
        # 不再每次重读磁盘
        if not self._loaded or getattr(self, "config", None) is None:
            self._init_config()
        value = None
        found = False
        if hasattr(self.config, key):
            try:
                value = getattr(self.config, key)
                found = True
            except Exception:
                found = False
        if not found:
            side = getattr(self, "_plugin_side", None)
            if isinstance(side, dict) and key in side:
                value = side[key]
                found = True
        if not found:
            try:
                from module.tools.config_registry import registered_defaults

                if key in registered_defaults():
                    value = registered_defaults().get(key, default)
                    found = True
                else:
                    value = default
            except Exception:
                value = default
        # 布尔/数字/list/dict 不走翻译，避免被翻译层改写
        if isinstance(value, (bool, int, float, list, dict, type(None))):
            return value
        try:
            return bt.tr('ConfigTranslation', value)
        except Exception:
            return value

    def has(self, key):
        if not self._loaded or getattr(self, "config", None) is None:
            self._init_config()
        if hasattr(self.config, key):
            return True
        try:
            from module.tools.config_registry import registered_keys

            return key in registered_keys()
        except Exception:
            return False

    def set(self, key, value):
        if not self._loaded or getattr(self, "config", None) is None:
            self._init_config()
        # 只对字符串做 undo 翻译；bool/list 原样写入
        if isinstance(value, str):
            try:
                value = bt.undo(value)
            except Exception:
                pass
        try:
            setattr(self.config, key, value)
        except Exception:
            # dataclass frozen 等极端情况
            try:
                object.__setattr__(self.config, key, value)
            except Exception:
                pass
        # 侧车：保证 save 一定能读到刚写入的插件/主页键
        try:
            if not hasattr(self, "_plugin_side") or self._plugin_side is None:
                self._plugin_side = {}
            self._plugin_side[key] = value
        except Exception:
            pass
        self.save()
        self.dynamic_update(key)

    def update(self, key, value):
        self.set(key, value)

    def save(self):
        if getattr(self, "config", None) is None:
            return
        data = asdict(self.config)
        # dataclass asdict 只含声明字段；插件键 / 主页键必须二次合并
        HOME_KEYS = (
            "home_layout_order",
            "tool_assets_enabled",
            "tool_assets_home_edit",
            "tool_assets_home_edit_entry",
            "tool_assets_home_switch_entry",
            "assetsVisibility",
            "tool_equip_farm_home_entry",
            "tool_auto_push_home_entry",
            "hoard_ap_home_entry",
            "hoard_ap_home_intercept_visible",
        )
        try:
            from module.tools.config_registry import collect_plugin_values, registered_defaults

            data.update(collect_plugin_values(self.config))
            extra_keys = set(registered_defaults().keys()) | set(HOME_KEYS)
        except Exception:
            extra_keys = set(HOME_KEYS)

        # 1) 侧车垫底（set 写入的缓存）
        side = getattr(self, "_plugin_side", None)
        if isinstance(side, dict):
            for k, v in side.items():
                data[k] = v
        # 2) 实例属性覆盖侧车（含仅 setattr 未走 set 的路径）
        for k in extra_keys:
            try:
                if hasattr(self.config, k):
                    data[k] = getattr(self.config, k)
            except Exception:
                pass
        # 3) __dict__ 再覆盖（最权威）
        try:
            d = getattr(self.config, "__dict__", None)
            if isinstance(d, dict):
                for k in extra_keys:
                    if k in d:
                        data[k] = d[k]
                # 也把 __dict__ 里其它已注册/主页相关键收进来
                for k, v in d.items():
                    if k in extra_keys or k in (side or {}):
                        data[k] = v
        except Exception:
            pass
        # 4) 用最终 data 回写侧车，保持一致
        try:
            if not isinstance(side, dict):
                self._plugin_side = {}
                side = self._plugin_side
            for k in list(extra_keys):
                if k in data:
                    side[k] = data[k]
        except Exception:
            pass

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
