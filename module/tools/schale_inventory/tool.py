# -*- coding: utf-8 -*-
from module.tools.base import ToolPlugin


class SchaleInventoryTool(ToolPlugin):
    """库存管理计算器插件入口。"""

    def build_widget(self, parent=None, config=None):
        from module.tools.schale_inventory.ui import Layout

        return Layout(parent=parent, config=config)
