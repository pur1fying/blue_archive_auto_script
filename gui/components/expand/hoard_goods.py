# -*- coding: utf-8 -*-
"""小勾选框：与 baas-ui-pr2 商店 GoodsCard 同款绿框。

选中：白底 + 左右 4px 绿 / 上下 2px 绿（无勾选方块）
未选：同样 4/2 厚度的淡灰边（盒模型恒定，点选文字绝不跳动）
未选 hover 不加绿。
"""

from __future__ import annotations

from typing import List, Sequence

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyle,
    QWidget,
)

from gui.components.expand.tool_style import GreenFrameOption

GREEN_CHECK = "#3D9A45"  # 勾选标记色（指示器内部，非主题边框）


class CheckGoods(GreenFrameOption):
    """绿框选项（主题引擎统一组件 GreenFrameOption 的囤体/装备侧名字）。"""

    def __init__(self, key: str, title: str, parent=None, *, min_w=0, pad=(12, 8)):
        super().__init__(key=str(key), text=title, parent=parent, min_w=min_w, pad=pad)


class MultiCheckRow(QWidget):
    changed = pyqtSignal(list)

    def __init__(self, items: Sequence[tuple], parent=None, *, card_min_w: int = 0):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.cards = {}
        for key, title in items:
            c = CheckGoods(str(key), title, self, min_w=card_min_w)
            c.toggled.connect(lambda *_: self.changed.emit(self.selected_keys()))
            lay.addWidget(c)
            self.cards[str(key)] = c
        lay.addStretch(1)

    def selected_keys(self) -> List[str]:
        return [k for k, c in self.cards.items() if c.is_checked()]

    def set_selected(self, keys: Sequence[str]):
        want = set(str(x) for x in (keys or []))
        for k, c in self.cards.items():
            c.set_checked(k in want, emit=False)


class ExclusiveCheckRow(QWidget):
    changed = pyqtSignal(str)

    def __init__(self, items: Sequence[tuple], parent=None, *, allow_empty: bool = False,
                 card_min_w: int = 0):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.cards = {}
        self._cur = ""
        self._allow_empty = bool(allow_empty)
        for key, title in items:
            c = CheckGoods(str(key), title, self, min_w=card_min_w)
            c.toggled.connect(self._on)
            lay.addWidget(c)
            self.cards[str(key)] = c
        lay.addStretch(1)

    def _on(self, key: str, checked: bool):
        if checked:
            for k, c in self.cards.items():
                if k != key:
                    c.set_checked(False, emit=False)
            self._cur = key
        else:
            if key == self._cur:
                if self._allow_empty:
                    self._cur = ""
                elif "0" in self.cards:
                    self.cards["0"].set_checked(True, emit=False)
                    self._cur = "0"
                else:
                    self.cards[key].set_checked(True, emit=False)
                    self._cur = key
                    return
        self.changed.emit(self._cur)

    def selected_key(self) -> str:
        return self._cur

    def set_selected(self, key: str):
        key = str(key or "")
        if key and key not in self.cards:
            key = "0" if "0" in self.cards else (next(iter(self.cards), "") if self.cards else "")
        for k, c in self.cards.items():
            c.set_checked(k == key and bool(key), emit=False)
        self._cur = key
