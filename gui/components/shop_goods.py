# -*- coding: utf-8 -*-
"""商店通用积木：商品卡皮肤 + 固定四列响应式网格。"""
from __future__ import annotations

from math import ceil
from typing import List, Sequence

from PyQt5.QtCore import QEvent, Qt, QSize, QPointF, pyqtSignal
from PyQt5.QtGui import QFontMetrics, QTextLayout, QTextOption
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

GRID_COLUMNS = 4
GRID_H_SPACING = 8
GRID_V_SPACING = 8
SIDE_MARGIN = 12
DEFAULT_VIEW_WIDTH = 800
SHOP_PREFERRED_WIDTH = DEFAULT_VIEW_WIDTH
SHOP_MAX_WIDTH = 1000
SHOP_VIEWPORT_HEIGHT = 440
CARD_PAD_X = 10
CARD_PAD_Y = 8
CARD_BORDER = 2
CARD_RADIUS = 8
# 四列始终保留。只有视口窄到每列不足该宽度时，商品区才出现横向滚动，
# 而不是压扁或裁掉文字。
MIN_COL_W = 96

GREEN = "#6FBF63"
GREEN_DIM = "#8FCF84"
GREEN_CHECK = "#3D9A45"

CAT_BG = {
    "exp_book": "rgb(242, 240, 240)",
    "exp_bead": "rgb(154, 240, 248)",
    "artifact": "rgb(255, 255, 255)",
    "secret_stone": "rgb(248, 224, 247)",
    "ap": "rgb(225, 246, 198)",
    "credit": "rgb(255, 249, 200)",
    "default": "rgb(250, 250, 250)",
}


def get_category_colors() -> dict:
    """商品分类底色表。

    预留接口：未来在设置页提供「更改商店商品显示颜色」时，
    由本函数返回用户自定义的分类底色映射。本 PR 保持默认色，
    不接入配置读写。
    """
    return dict(CAT_BG)


def classify_goods(raw_name: str) -> str:
    n = str(raw_name or "")
    nl = n.lower()
    if "经验书" in n:
        return "exp_book"
    if "强化珠" in n or "经验珠" in n:
        return "exp_bead"
    if "神秘古物" in n or "古物" in n:
        return "artifact"
    if "神明文字" in n or "神名文字" in n:
        return "secret_stone"
    if "体力" in n or "AP" in n or nl in ("ap", "30ap", "60ap") or n.endswith("AP"):
        return "ap"
    if "信用点" in n:
        return "credit"
    return "default"


def _wrapped_text_height(text: str, font, width: int) -> int:
    """按 Qt 的真实换行规则计算完整文本高度。"""
    layout = QTextLayout(str(text or ""), font)
    option = QTextOption()
    option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
    layout.setTextOption(option)
    line_width = max(1, int(width))
    height = 0.0
    layout.beginLayout()
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(line_width)
        line.setPosition(QPointF(0.0, height))
        height += line.height()
    layout.endLayout()
    if height <= 0:
        height = QFontMetrics(font).height()
    return int(ceil(height))


class WrappingLabel(QLabel):
    """完整显示中英日文本，并向父布局报告随宽度变化的高度。"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._height_cache = None
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def event(self, event):
        if event.type() in (
            QEvent.FontChange,
            QEvent.StyleChange,
            QEvent.ContentsRectChange,
        ):
            self._height_cache = None
        return super().event(event)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        margins = self.contentsMargins()
        inner = max(
            1,
            int(width)
            - margins.left()
            - margins.right()
            - self.margin() * 2,
        )
        cache_key = (inner, self.text())
        if self._height_cache is None or self._height_cache[0] != cache_key:
            self._height_cache = (
                cache_key,
                _wrapped_text_height(self.text(), self.font(), inner),
            )
        return (
            self._height_cache[1]
            + margins.top()
            + margins.bottom()
            + self.margin() * 2
        )

    def minimumSizeHint(self) -> QSize:
        return QSize(1, QFontMetrics(self.font()).height())

    def sizeHint(self) -> QSize:
        width = max(1, self.width())
        return QSize(width, self.heightForWidth(width))


class GoodsCard(QFrame):
    """一张商品卡：整卡切换选中，名称随卡片宽度完整换行。"""

    toggled = pyqtSignal(int, bool)

    def __init__(
        self,
        index: int,
        name: str,
        price_text: str,
        checked: bool = False,
        category: str = "default",
        parent=None,
    ):
        super().__init__(parent)
        self._index = int(index)
        self._checked = bool(checked)
        self._category = category if category in CAT_BG else "default"
        self.setObjectName("baGoodsCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumWidth(0)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(False)

        self._selection_frame = QFrame(self)
        self._selection_frame.setObjectName("goodsSelectionFrame")
        self._selection_frame.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._selection_frame.setAttribute(Qt.WA_StyledBackground, True)
        self._selection_frame.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(CARD_PAD_X, CARD_PAD_Y, CARD_PAD_X, CARD_PAD_Y)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(7)
        side = max(QFontMetrics(self.font()).height(), 16)
        self.mark = QLabel(self)
        self.mark.setFixedSize(side, side)
        self.mark.setAlignment(Qt.AlignCenter)
        self.mark.setStyleSheet(
            "QLabel{"
            f"color:{GREEN_CHECK};font-weight:700;"
            "border:1px solid rgba(70,70,70,150);"
            "border-radius:0;background:#FFFFFF;}"
        )
        top.addWidget(self.mark, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.price_lbl = QLabel(str(price_text or ""), self)
        self.price_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.price_lbl.setStyleSheet("color:#333;background:transparent;")
        self.price_lbl.setToolTip(self.price_lbl.text())
        top.addWidget(self.price_lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
        top.addStretch(1)
        root.addLayout(top)

        self.name_lbl = WrappingLabel(str(name or ""), self)
        self.name_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.name_lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        self.name_lbl.setStyleSheet("color:#222;background:transparent;")
        self.name_lbl.setToolTip(self.name_lbl.text())
        root.addWidget(self.name_lbl)
        self._apply_chrome()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._selection_frame.setGeometry(self.rect())
        self._selection_frame.raise_()

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool, *, emit: bool = True):
        checked = bool(checked)
        if self._checked == checked:
            return
        self._checked = checked
        self._apply_chrome()
        if emit:
            self.toggled.emit(self._index, self._checked)

    def set_category(self, category: str):
        self._category = category if category in CAT_BG else "default"
        self._apply_chrome()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_checked(not self._checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def _fill_bg(self) -> str:
        colors = get_category_colors()
        return colors.get(self._category, colors.get("default", CAT_BG["default"]))

    def _apply_chrome(self):
        bg = self._fill_bg()
        self.mark.setText("✓" if self._checked else "")
        self.setStyleSheet(
            "QFrame#baGoodsCard{"
            f"background-color:{bg};"
            "border:2px solid #B8B8B8;"
            f"border-radius:{CARD_RADIUS}px;}}"
        )
        if self._checked:
            self._selection_frame.setStyleSheet(
                "QFrame#goodsSelectionFrame{"
                "background:transparent;"
                f"border-top:1px solid {GREEN_DIM};"
                f"border-bottom:1px solid {GREEN_DIM};"
                f"border-left:3px solid {GREEN};"
                f"border-right:3px solid {GREEN};"
                f"border-radius:{CARD_RADIUS}px;}}"
            )
            self._selection_frame.show()
            self._selection_frame.raise_()
        else:
            self._selection_frame.hide()
        self.update()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        layout = self.layout()
        margins = layout.contentsMargins()
        name_width = max(
            1,
            int(width)
            - margins.left()
            - margins.right()
            - CARD_BORDER * 2,
        )
        top_height = max(
            self.mark.height(),
            self.price_lbl.sizeHint().height(),
        )
        return (
            margins.top()
            + margins.bottom()
            + top_height
            + layout.spacing()
            + self.name_lbl.heightForWidth(name_width)
            + CARD_BORDER * 2
        )

    def sizeHint(self) -> QSize:
        width = max(MIN_COL_W, self.width())
        return QSize(width, self.heightForWidth(width))

    def minimumSizeHint(self) -> QSize:
        return QSize(MIN_COL_W, self.heightForWidth(MIN_COL_W))


class ShopGoodsGrid(QWidget):
    """始终固定四列，列宽随可用宽度等分，行高随完整名称增长。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._cards: List[GoodsCard] = []
        self._synced_height = -1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(GRID_H_SPACING)
        self._grid.setVerticalSpacing(GRID_V_SPACING)
        self._grid.setAlignment(Qt.AlignTop)
        for column in range(GRID_COLUMNS):
            self._grid.setColumnStretch(column, 1)
            self._grid.setColumnMinimumWidth(column, MIN_COL_W)

    def clear(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self._cards.clear()

    def set_cards(self, cards: Sequence[GoodsCard]):
        self.clear()
        self._cards = list(cards)
        for index, card in enumerate(self._cards):
            row, column = divmod(index, GRID_COLUMNS)
            self._grid.addWidget(card, row, column)
        self._sync_height(self.width() or DEFAULT_VIEW_WIDTH)

    def cards(self) -> List[GoodsCard]:
        return list(self._cards)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        if not self._cards:
            return 40
        margins = self._grid.contentsMargins()
        usable = max(
            GRID_COLUMNS * MIN_COL_W,
            int(width) - margins.left() - margins.right(),
        )
        column_width = max(
            MIN_COL_W,
            (usable - GRID_H_SPACING * (GRID_COLUMNS - 1)) // GRID_COLUMNS,
        )
        rows = (len(self._cards) + GRID_COLUMNS - 1) // GRID_COLUMNS
        height = margins.top() + margins.bottom()
        for row in range(rows):
            chunk = self._cards[row * GRID_COLUMNS : (row + 1) * GRID_COLUMNS]
            height += max(
                (card.heightForWidth(column_width) for card in chunk),
                default=40,
            )
            if row:
                height += GRID_V_SPACING
        return max(40, height)

    def _sync_height(self, width: int):
        height = self.heightForWidth(width)
        if height == self._synced_height:
            return
        self._synced_height = height
        self.setFixedHeight(height)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_height(event.size().width())

    def sizeHint(self) -> QSize:
        width = max(DEFAULT_VIEW_WIDTH, self.minimumSizeHint().width())
        return QSize(width, self.heightForWidth(width))

    def minimumSizeHint(self) -> QSize:
        width = GRID_COLUMNS * MIN_COL_W + GRID_H_SPACING * (GRID_COLUMNS - 1)
        return QSize(width, self.heightForWidth(width))


ShopGoodCard = GoodsCard
