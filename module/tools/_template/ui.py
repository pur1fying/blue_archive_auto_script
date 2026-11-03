# -*- coding: utf-8 -*-
"""最简工具页：标题 + 一行说明。复杂了再参考 schale_inventory/ui.py。

主题红线（详见 docs/THEME_BORDER.md）：
- 业务代码只用 themed_*() 取色，不要硬编码颜色
- 插件内部边框 1px；2px 只属于框架基层设置栏
- paintEvent 里禁止对 painter 字体 setPointSize/setFont（像素字体会静默掉画）
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    from gui.components.expand.tool_style import themed_text
except Exception:  # pragma: no cover
    themed_text = lambda: "#333333"


class Layout(QWidget):
    """工具页主控件。框架只要求：是 QWidget、构造不炸。"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self._config = config
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(8)
        title = QLabel("我的工具", self)
        root.addWidget(title)
        hint = QLabel("在这里搭你自己的界面。config_defaults 已自动生成设置页。", self)
        hint.setStyleSheet("color:%s;" % themed_text())
        root.addWidget(hint)
