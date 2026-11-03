# -*- coding: utf-8 -*-
from __future__ import annotations

from module.tools.base import ToolPlugin, resolve_dotted, _cfg_bool


class EquipFarmTool(ToolPlugin):
    def register_config(self) -> None:
        from module.tools.config_registry import register_config_defaults

        register_config_defaults({
            "tool_equip_farm_inputs_json": "",
            "tool_equip_farm_home_entry": True,
        })

    def build_widget(self, parent=None, config=None):
        ui = self.manifest.ui or "module.tools.equip_farm.ui:Layout"
        Layout = resolve_dotted(ui)
        try:
            return Layout(parent, config)
        except TypeError:
            return Layout(config=config)

    def build_home_widget(self, parent=None, config=None):
        if not self.home_visible(config):
            return None
        from module.tools.equip_farm.home_widget import EquipFarmHomeWidget

        return EquipFarmHomeWidget(parent=parent, config=config)

    def home_visible(self, config) -> bool:
        # 主页显示开关（默认开）
        return _cfg_bool(config, "tool_equip_farm_home_entry", True)
