# -*- coding: utf-8 -*-
"""商店页壳：固定顶栏 + 可滚商品区（积木在 shop_goods）。

顶栏（不滚，贴顶）：
  第1行：「请勾选购买物品」 | 货币图标+单位
  第2行：完整日耗公式（不换行） | 刷新次数

商品区：ShopGoodsGrid，始终 4 列绿框卡 + 勾选方块。
滚动：普通 QScrollArea，使用公开滚动条接口设置步长。
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Sequence, Tuple

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import LineEdit, ImageLabel

from gui.util.translator import baasTranslator as bt
from gui.components.shop_goods import (
    DEFAULT_VIEW_WIDTH,
    SIDE_MARGIN,
    GoodsCard,
    ShopGoodsGrid,
    classify_goods,
)


PAD_Y = 8

_ROUNDED_UI_FONTS = (
    "HarmonyOS Sans SC",
    "MiSans",
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "Yu Gothic UI",
    "Meiryo UI",
    "Malgun Gothic",
    "Segoe UI Variable Display",
    "Segoe UI",
)


@lru_cache(maxsize=1)
def _available_ui_fonts():
    try:
        return frozenset(QFontDatabase().families())
    except Exception:
        return frozenset()


def _readable_heading_font(widget: QWidget, pixel_size: int) -> QFont:
    """Choose a soft UI font without assuming optional fonts are installed."""
    font = widget.font()
    available = _available_ui_fonts()
    for family in _ROUNDED_UI_FONTS:
        if family in available:
            font.setFamily(family)
            break
    font.setPixelSize(pixel_size)
    font.setWeight(QFont.DemiBold)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font


def _safe_int(text, default=0) -> int:
    try:
        return int(str(text).strip())
    except (TypeError, ValueError):
        return default


def _price_of(item) -> int:
    try:
        return int(item[1])
    except (TypeError, ValueError, IndexError):
        return 0


def _raw_name(item) -> str:
    try:
        return str(item[0])
    except Exception:
        return ""


def _item_name(item) -> str:
    try:
        return bt.tr("ConfigTranslation", item[0])
    except Exception:
        return _raw_name(item)


def _price_text(item) -> str:
    return str(_price_of(item))


def _tune_scroll(scroll_area: QScrollArea) -> None:
    """Set predictable wheel increments through public scrollbar APIs."""
    bar = scroll_area.verticalScrollBar()
    bar.setSingleStep(48)
    bar.setPageStep(200)


class ShopPanel(QWidget):
    """固定顶栏 + 内部滚动的商品 4 列网格。"""

    def __init__(
        self,
        parent=None,
        config=None,
        *,
        goods_key: str,
        refresh_key: str,
        price_list: Sequence,
        currency_unit_label: str,
        refresh_max: int,
        estimate_fn=None,
        currency_icon: str = "",
        **_ignored,
    ):
        super().__init__(parent=parent)
        self.config = config
        self.goods_key = goods_key
        self.refresh_key = refresh_key
        self.price_list = list(price_list or [])
        self.estimate_fn = estimate_fn
        self._refresh_max = int(refresh_max)
        self._currency_icon = str(currency_icon or "")

        raw_goods = None
        try:
            raw_goods = self.config.get(key=goods_key)
        except Exception:
            try:
                raw_goods = self.config.get(goods_key)
            except Exception:
                raw_goods = None
        goods = list(raw_goods) if isinstance(raw_goods, (list, tuple)) else []
        n = max(len(goods), len(self.price_list))
        if len(goods) < n:
            goods = goods + [0] * (n - len(goods))
        if len(self.price_list) < n:
            n = min(len(goods), len(self.price_list))
            goods = goods[:n]
        self.goods = goods[:n]
        self.price_list = self.price_list[:n]
        self.goods_count = n

        self.setObjectName("shopPanel")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setProperty("shopInternalScroll", True)
        self.setProperty("hoardSingleScroll", True)

        root = QVBoxLayout(self)
        root.setContentsMargins(SIDE_MARGIN, PAD_Y, SIDE_MARGIN, PAD_Y)
        root.setSpacing(6)
        root.setAlignment(Qt.AlignTop)

        # ===== 固定顶栏 =====
        head = QFrame(self)
        head.setObjectName("shopStickyHead")
        head.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hv = QVBoxLayout(head)
        hv.setContentsMargins(0, 0, 0, 0)
        hv.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        self.guide_label = QLabel(self.tr("请勾选购买物品"), head)
        self.guide_label.setFont(_readable_heading_font(self.guide_label, 18))
        self.guide_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.guide_label.setWordWrap(False)
        self.guide_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        title_row.addWidget(self.guide_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self._unit_icon = None
        if self._currency_icon:
            try:
                icon = ImageLabel(self._currency_icon, head)
                icon.setFixedSize(28, 28)
                icon.setToolTip(currency_unit_label)
                self._unit_icon = icon
                title_row.addWidget(icon, 0, Qt.AlignVCenter)
            except Exception:
                self._unit_icon = None
        self.unit_label = QLabel(currency_unit_label, head)
        unit_font = self.unit_label.font()
        unit_font.setPixelSize(14)
        self.unit_label.setFont(unit_font)
        self.unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.unit_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        title_row.addWidget(self.unit_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        title_row.addStretch(1)
        hv.addLayout(title_row)

        self._head_details = QBoxLayout(QBoxLayout.LeftToRight)
        self._head_details.setContentsMargins(0, 0, 0, 0)
        self._head_details.setSpacing(10)

        self.estimate_label = QLabel("", head)
        self.estimate_label.setFont(
            _readable_heading_font(self.estimate_label, 14)
        )
        self.estimate_label.setWordWrap(False)
        self.estimate_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.estimate_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Fixed,
        )
        self._head_details.addWidget(
            self.estimate_label,
            1,
            Qt.AlignLeft | Qt.AlignVCenter,
        )

        refresh_box = QFrame(head)
        refresh_box.setObjectName("shopRefreshBox")
        rr = QHBoxLayout(refresh_box)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.setSpacing(8)
        self.refresh_label = QLabel(self.tr("购买刷新次数"), refresh_box)
        self.refresh_input = LineEdit(refresh_box)
        self.head = head
        self.refresh_box = refresh_box
        self.refresh_input.setMinimumWidth(56)
        self.refresh_input.setMaximumWidth(88)
        self.refresh_input.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed,
        )
        self.refresh_input.setPlaceholderText("0")
        try:
            self.refresh_input.setText(str(self.config.get(refresh_key)))
        except Exception:
            self.refresh_input.setText("0")
        self.refresh_input.editingFinished.connect(self._commit_refresh)
        self.refresh_input.textChanged.connect(self._on_refresh_text_changed)
        rr.addWidget(self.refresh_label, 0, Qt.AlignVCenter)
        rr.addWidget(self.refresh_input, 0, Qt.AlignVCenter)
        self._head_details.addWidget(
            refresh_box,
            0,
            Qt.AlignRight | Qt.AlignVCenter,
        )
        hv.addLayout(self._head_details)

        root.addWidget(head, 0)

        # ===== 可滚商品区 =====
        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("shopGoodsScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._scroll.setStyleSheet(
            "QScrollArea#shopGoodsScroll{background:transparent;border:none;}"
            "QScrollBar:vertical{width:10px;background:transparent;margin:2px;}"
            "QScrollBar::handle:vertical{"
            "background:rgba(100,140,180,130);border-radius:5px;min-height:28px;}"
            "QScrollBar::handle:vertical:hover{background:rgba(80,130,180,180);}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:transparent;}"
        )
        try:
            self._scroll.viewport().setStyleSheet("background:transparent;")
        except Exception:
            pass
        _tune_scroll(self._scroll)

        body = QWidget()
        body.setObjectName("shopGoodsBody")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("QWidget#shopGoodsBody{background:transparent;}")
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bv = QVBoxLayout(body)
        bv.setContentsMargins(0, 4, 0, 8)
        bv.setSpacing(0)
        bv.setAlignment(Qt.AlignTop)

        self.grid = ShopGoodsGrid(body)
        cards: List[GoodsCard] = []
        for i in range(self.goods_count):
            item = self.price_list[i]
            raw = _raw_name(item)
            cat = classify_goods(raw)
            card = GoodsCard(
                index=i,
                name=_item_name(item),
                price_text=_price_text(item),
                checked=bool(self.goods[i] == 1),
                category=cat,
                parent=self.grid,
            )
            card.toggled.connect(self._on_card_toggled)
            cards.append(card)
        self.grid.set_cards(cards)
        self.cards = cards
        bv.addWidget(self.grid, 0, Qt.AlignTop)
        bv.addStretch(1)

        self._scroll.setWidget(body)
        root.addWidget(self._scroll, 1)

        self._refresh_estimate()
        self._update_header_direction(self.width())
        self._allow_click_outside_to_commit()

    def _update_header_direction(self, width: int):
        required = (
            self.estimate_label.sizeHint().width()
            + self.refresh_box.sizeHint().width()
            + self._head_details.spacing()
            + SIDE_MARGIN * 2
        )
        direction = (
            QBoxLayout.TopToBottom
            if int(width or 0) < required
            else QBoxLayout.LeftToRight
        )
        if self._head_details.direction() != direction:
            self._head_details.setDirection(direction)
            self.updateGeometry()

    def _allow_click_outside_to_commit(self):
        """Commit the refresh input when clicking anywhere else.

        Qt-native: blank areas become click-focusable, so a click outside the
        input moves focus and triggers the native editingFinished signal.
        No application-wide event filtering is involved.
        """
        self.setFocusPolicy(Qt.ClickFocus)
        window = self.window()
        if window is not None and window is not self:
            if window.focusPolicy() == Qt.NoFocus:
                window.setFocusPolicy(Qt.ClickFocus)
        for widget in self.findChildren(QWidget):
            if widget is self.refresh_input:
                continue
            if self.refresh_input.isAncestorOf(widget):
                continue
            if widget.focusPolicy() == Qt.NoFocus:
                widget.setFocusPolicy(Qt.ClickFocus)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_header_direction(event.size().width())

    def sizeHint(self):
        return QSize(DEFAULT_VIEW_WIDTH, 440)

    def minimumSizeHint(self):
        return QSize(480, 280)

    def _on_card_toggled(self, index: int, checked: bool):
        self.goods[index] = 1 if checked else 0
        self.config.set(key=self.goods_key, value=list(self.goods))
        self._refresh_estimate()

    def _on_refresh_text_changed(self, text: str):
        cleaned = "".join(ch for ch in (text or "") if ch.isdigit())
        if cleaned != text:
            pos = self.refresh_input.cursorPosition()
            self.refresh_input.blockSignals(True)
            self.refresh_input.setText(cleaned)
            self.refresh_input.setCursorPosition(
                max(0, pos - (len(text) - len(cleaned)))
            )
            self.refresh_input.blockSignals(False)

    def _commit_refresh(self):
        raw = (self.refresh_input.text() or "").strip()
        val = 0 if raw == "" else _safe_int(raw, 0)
        val = max(0, min(val, self._refresh_max))
        self.refresh_input.blockSignals(True)
        self.refresh_input.setText(str(val))
        self.refresh_input.blockSignals(False)
        self.config.set(self.refresh_key, val)
        self._refresh_estimate()

    def _checked_mask(self) -> List[int]:
        return [1 if c.is_checked() else 0 for c in self.cards]

    def _refresh_estimate(self):
        if not self.estimate_fn:
            self.estimate_label.setText("")
            return
        refresh_n = _safe_int(self.refresh_input.text(), 0)
        title, detail = self.estimate_fn(
            self, self._checked_mask(), refresh_n, self.price_list
        )
        parts = [str(part).replace("\n", " ").strip() for part in (title, detail)]
        self.estimate_label.setText(" ".join(part for part in parts if part))
        self.estimate_label.updateGeometry()


def estimate_arena_daily(panel, checked: List[int], refresh_n: int, price_list: Sequence) -> Tuple[str, str]:
    refresh_n = max(0, min(int(refresh_n), 3))
    one_pass = 0
    for i, flag in enumerate(checked):
        if flag and i < len(price_list):
            one_pass += _price_of(price_list[i])
    total = one_pass + one_pass * refresh_n + refresh_n * 10
    title = panel.tr("每天消耗约 {0} 竞技币").replace("{0}", str(total))
    detail = panel.tr("({0}+{0}×{1}+{1}×10)").replace("{0}", str(one_pass)).replace(
        "{1}", str(refresh_n)
    )
    return title, detail


def estimate_common_shop_daily(panel, checked: List[int], refresh_n: int, price_list: Sequence) -> Tuple[str, str]:
    # 运行时只支持 3 次刷新（价格 40/60/80），估算必须与执行器一致。
    refresh_n = max(0, min(int(refresh_n), 3))
    one_pass_credit = 0
    one_pass_pyro = 0
    for i, flag in enumerate(checked):
        if not flag or i >= len(price_list):
            continue
        item = price_list[i]
        price = _price_of(item)
        currency = item[2] if len(item) > 2 else "creditpoints"
        if currency == "creditpoints":
            one_pass_credit += price
        else:
            one_pass_pyro += price
    rounds = refresh_n + 1
    credit_total = one_pass_credit * rounds
    pyro_refresh = 0
    costs = [40, 60, 80]
    for k in range(refresh_n):
        pyro_refresh += costs[k]
    pyro_total = one_pass_pyro * rounds + pyro_refresh
    if one_pass_pyro or pyro_refresh:
        title = panel.tr("每天约 {0} 信用点").replace("{0}", str(credit_total))
        detail = panel.tr("青辉石约 {0}（含刷新）").replace("{0}", str(pyro_total))
        return title, detail
    title = panel.tr("每天消耗约 {0} 信用点").replace("{0}", str(credit_total))
    return title, ""
