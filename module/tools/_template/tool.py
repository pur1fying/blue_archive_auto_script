# -*- coding: utf-8 -*-
"""最小插件实现：复制 _template/ 目录后，改 3 处名字 + 你的业务逻辑。

1) 目录名：_template → 你的插件名（如 my_tool）
2) manifest.json：id / name / entry 里的目录名 / config_prefix
3) 本文件末尾 import：module.tools.my_tool.ui
"""
from module.tools.base import ToolPlugin


class Tool(ToolPlugin):
    """manifest.entry 指向它（默认 module.tools.<目录名>.tool:Tool）。

    框架已经替你做的：
    - 主页自动发「进入××」蓝色按钮（无需写 home 声明）
    - 工具大厅顶栏自动发「主页显示」开关与栏位选择
    - config_defaults 里声明的字段自动生成「插件设置」界面
    """

    def build_widget(self, parent=None, config=None):
        # 工具大厅打开时构建主页面。最省事：把 UI 交给 ui.py 的 Layout。
        from module.tools.my_tool.ui import Layout

        return Layout(parent=parent, config=config)

    # 可选：读自己的配置。键 = config_prefix + 字段名，值已由框架
    # 在 ConfigSet.load 时 setattr 到 config.config 上。
    def my_setting(self, config, key, default):
        try:
            return getattr(config.config, key, default)
        except Exception:
            return default
