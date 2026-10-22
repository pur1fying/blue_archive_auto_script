# -*- coding: utf-8 -*-
from module.tools.base import ToolPlugin, _cfg_bool, resolve_dotted


class AutoPushTool(ToolPlugin):
    def register_config(self) -> None:
        from module.tools.config_registry import register_config_defaults

        register_config_defaults({"tool_auto_push_team_plan": None})
    def build_widget(self, parent=None, config=None):
        Layout = resolve_dotted(self.manifest.ui or "module.tools.auto_push.ui:Layout")
        return Layout(parent, config)

    def build_home_widget(self, parent=None, config=None):
        if not _cfg_bool(config, "tool_auto_push_home_entry", False):
            return None
        from module.tools.auto_push.home_widget import AutoPushHomeWidget

        return AutoPushHomeWidget(parent=parent, config=config)
