# -*- coding: utf-8 -*-
"""囤体工具插件：UI 复用 hoardApConfig.Layout，逻辑仍在 module.hoard_ap。"""
from __future__ import annotations

from module.tools.base import ToolPlugin, resolve_dotted, _cfg_bool
from module.tools.hoard_ap.defaults import HOARD_CONFIG_DEFAULTS


class HoardApTool(ToolPlugin):
    def register_config(self) -> None:
        from module.tools.config_registry import register_config_defaults

        register_config_defaults(HOARD_CONFIG_DEFAULTS)

    def build_widget(self, parent=None, config=None):
        ui_path = self.manifest.ui or "gui.components.expand.hoardApConfig:Layout"
        Layout = resolve_dotted(ui_path)
        try:
            return Layout(parent, config)
        except TypeError:
            return Layout(config=config)

    def build_home_widget(self, parent=None, config=None):
        """主页：入口显示 或 拦截显示 任一开就挂载（内部再分显隐）。"""
        if not self.home_visible(config):
            return None
        from module.tools.hoard_ap.home_widget import PreferClearHomeWidget

        return PreferClearHomeWidget(parent=parent, config=config)

    def home_visible(self, config) -> bool:
        entry = _cfg_bool(config, "hoard_ap_home_entry", True)
        intercept = _cfg_bool(config, "hoard_ap_home_intercept_visible", True)
        return bool(entry or intercept)

    def on_enable(self, config) -> None:
        try:
            if hasattr(config, "set"):
                config.set("hoard_ap_enabled", True)
        except Exception as e:
            # 开关状态没写进去=界面与真实启用态脱节，必须留痕
            print("[hoard_ap] 主页开关写入 hoard_ap_enabled=True 失败:", e)

    def on_disable(self, config) -> None:
        try:
            if hasattr(config, "set"):
                config.set("hoard_ap_enabled", False)
        except Exception as e:
            print("[hoard_ap] 主页开关写入 hoard_ap_enabled=False 失败:", e)
