from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QFrame
from qfluentwidgets import FlowLayout, CheckBox, LineEdit

from gui.util.translator import baasTranslator as bt


# Unified chrome: same width; dialog forces same viewport height for both shops.
SHOP_CONTENT_WIDTH = 800
_ITEM_W = 170
_ITEM_H = 58
_HEADER_H = 48
_PAD_Y = 16  # same top & bottom
_PAD_X = 16


class Layout(QWidget):
    """Arena shop goods editor. Height follows real rows; dialog scrolls at shared viewport height."""

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.default_goods = self.config.static_config.tactical_challenge_shop_price_list[self.config.server_mode]
        self.goods = self.config.get(key='TacticalChallengeShopList')
        self._n = len(self.goods)

        self.setMinimumWidth(SHOP_CONTENT_WIDTH)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        root = QVBoxLayout(self)
        root.setContentsMargins(_PAD_X, _PAD_Y, _PAD_X, _PAD_Y)
        root.setSpacing(8)
        root.setAlignment(Qt.AlignTop)

        header = QHBoxLayout()
        header.addStretch(1)

        # Bordered refresh cluster so it reads as a control, not plain text.
        refresh_box = QFrame(self)
        refresh_box.setObjectName('shopRefreshBox')
        refresh_box.setStyleSheet(
            'QFrame#shopRefreshBox {'
            '  border: 1px solid rgba(0, 0, 0, 55);'
            '  border-radius: 6px;'
            '  background: rgba(0, 0, 0, 4);'
            '}'
        )
        refresh_row = QHBoxLayout(refresh_box)
        refresh_row.setContentsMargins(10, 6, 10, 6)
        refresh_row.setSpacing(8)
        self.label = QLabel(self.tr('刷新次数'), refresh_box)
        self.input = LineEdit(refresh_box)
        self.input.setFixedWidth(72)
        self.input.setValidator(QIntValidator(0, 3))
        self.input.setText(str(self.config.get('TacticalChallengeShopRefreshTime')))
        self.input.editingFinished.connect(self._commit_refresh)
        refresh_row.addWidget(self.label, 0, Qt.AlignVCenter)
        refresh_row.addWidget(self.input, 0, Qt.AlignVCenter)
        header.addWidget(refresh_box, 0, Qt.AlignRight)
        root.addLayout(header)

        goods_host = QWidget(self)
        goods_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._flow = FlowLayout(goods_host, needAni=False)
        self._flow.setContentsMargins(0, 0, 0, 0)
        self._flow.setVerticalSpacing(0)
        self._flow.setHorizontalSpacing(8)

        self.setStyleSheet('Demo{background: white}')
        self.boxes = []
        for i in range(self._n):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.goods[i] == 1)
            ccs = QLabel(bt.tr('ConfigTranslation', self.default_goods[i][0]), self)
            ccs.setFixedWidth(110)
            price_text = str(self.default_goods[i][1])
            price_label = QLabel(price_text, self)
            price_label.setFixedWidth(110)
            VLayout = QVBoxLayout()
            VLayout.addWidget(price_label)
            VLayout.addWidget(ccs)
            wrapper_widget = QWidget()
            wrapper = QHBoxLayout()
            wrapper.addLayout(VLayout)
            wrapper.addWidget(t_cbx)
            wrapper_widget.setLayout(wrapper)
            self._flow.addWidget(wrapper_widget)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index, self._n))
            self.boxes.append(t_cbx)

        root.addWidget(goods_host, 0, Qt.AlignTop)
        self._goods_host = goods_host
        self._apply_content_height(SHOP_CONTENT_WIDTH)

    def _cols_for_width(self, width: int) -> int:
        inner = max(1, width - 2 * _PAD_X)
        return max(1, inner // _ITEM_W)

    def _content_height_for_width(self, width: int) -> int:
        cols = self._cols_for_width(width)
        rows = max(1, (self._n + cols - 1) // cols) if self._n else 1
        goods_h = rows * _ITEM_H
        return _PAD_Y + _HEADER_H + goods_h + _PAD_Y

    def _apply_content_height(self, width: int):
        """minimumHeight drives QScrollArea scrollbar; viewport height is shared in dialog."""
        h = self._content_height_for_width(width)
        self.setMinimumHeight(h)
        cols = self._cols_for_width(width)
        rows = max(1, (self._n + cols - 1) // cols) if self._n else 1
        self._goods_host.setMinimumHeight(rows * _ITEM_H)

    def sizeHint(self):
        return QSize(SHOP_CONTENT_WIDTH, self._content_height_for_width(SHOP_CONTENT_WIDTH))

    def minimumSizeHint(self):
        return self.sizeHint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_content_height(max(event.size().width(), SHOP_CONTENT_WIDTH))

    def alter_status(self, index, goods_count):
        self.config.set(
            key='TacticalChallengeShopList',
            value=[1 if self.boxes[i].isChecked() else 0 for i in range(0, goods_count)],
        )

    def _commit_refresh(self):
        self.config.set('TacticalChallengeShopRefreshTime', int(self.input.text() or 0))
