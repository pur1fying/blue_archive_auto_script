# -*- coding: utf-8 -*-
"""主页：装备刷图入口按钮（排在囤体右边，按插件 order）。"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

try:
    from qfluentwidgets import PrimaryPushButton, PushButton
except Exception:  # pragma: no cover
    try:
        from PyQt5.QtWidgets import QPushButton as PrimaryPushButton, QPushButton as PushButton
    except Exception:
        PrimaryPushButton = None  # type: ignore
        PushButton = None  # type: ignore

try:
    from gui.components.expand.tool_style import (
        apply_theme_to_labels,
        connect_theme_refresh,
    )
except Exception:  # pragma: no cover
    apply_theme_to_labels = connect_theme_refresh = None

from module.tools.base import _cfg_bool


class EquipFarmHomeWidget(QFrame):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("equipFarmHomeBox")
        root = QHBoxLayout(self)
        root.setContentsMargins(2, 4, 2, 4)  # 盒间隔=2+槽位6+2=10，与盒内 10px 一致
        root.setSpacing(8)
        self.btn_enter = None
        if PrimaryPushButton is not None or PushButton is not None:
            Btn = PrimaryPushButton or PushButton
            self.btn_enter = Btn("进入装备刷图", self)
            try:
                self.btn_enter.setToolTip("打开工具里的装备刷图页")
            except Exception:
                pass
            self.btn_enter.clicked.connect(self._open)
            root.addWidget(self.btn_enter, 0, Qt.AlignLeft)
        try:
            self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        except Exception:
            pass
        self._apply_visibility()

        # 深色模式适配
        if apply_theme_to_labels is not None:
            apply_theme_to_labels(self)
            connect_theme_refresh(self)

    def _apply_visibility(self) -> None:
        on = _cfg_bool(self.config, "tool_equip_farm_home_entry", True)
        try:
            self.setVisible(bool(on))
        except Exception:
            pass

    def _open(self):
        try:
            w = self.parent()
            while w is not None and not hasattr(w, "open_tool"):
                try:
                    w = w.parent()
                except Exception:
                    w = None
            if w is not None and hasattr(w, "open_tool"):
                w.open_tool("equip_farm")
                return
            cfg = self.config
            win = cfg.get_window() if cfg is not None and hasattr(cfg, "get_window") else None
            if win is not None and hasattr(win, "open_tool_page"):
                win.open_tool_page("equip_farm", config=cfg)
        except Exception as e:
            print("[equip_farm home] open failed:", e)
