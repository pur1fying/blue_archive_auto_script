from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QFrame
from qfluentwidgets import LineEdit

from gui.util.translator import baasTranslator as bt
from gui.components.shop_goods import ShopGoodCard, ShopGoodsGrid


_PAD_Y = 16
_PAD_X = 16


class Layout(QWidget):
    """Common shop goods editor with a width-responsive goods grid."""

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.default_goods = self.config.static_config.common_shop_price_list[self.config.server_mode]
        self.goods = self.config.get(key='CommonShopList')
        self._n = len(self.goods)

        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        root = QVBoxLayout(self)
        root.setContentsMargins(_PAD_X, _PAD_Y, _PAD_X, _PAD_Y)
        root.setSpacing(8)
        root.setAlignment(Qt.AlignTop)

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
        self.label.setWordWrap(True)
        self.input = LineEdit(refresh_box)
        self.input.setFixedWidth(72)
        self.input.setValidator(QIntValidator(0, 5))
        self.input.setText(str(self.config.get('CommonShopRefreshTime')))
        self.input.editingFinished.connect(self._commit_refresh)
        refresh_row.addWidget(self.label, 1, Qt.AlignVCenter)
        refresh_row.addWidget(self.input, 0, Qt.AlignVCenter)
        refresh_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        root.addWidget(refresh_box)

        goods_host = ShopGoodsGrid(self)

        self.setStyleSheet('Demo{background: white}')
        self.boxes = []
        for i in range(self._n):
            name = bt.tr('ConfigTranslation', self.default_goods[i][0])
            price_text = str(self.default_goods[i][1])
            if self.default_goods[i][2] == 'creditpoints':
                price_text += self.tr('信用点')
            else:
                price_text += self.tr('青辉石')
            wrapper_widget = ShopGoodCard(
                name,
                price_text,
                checked=self.goods[i] == 1,
                price_first=False,
                parent=goods_host,
            )
            t_cbx = wrapper_widget.check_box
            goods_host.addWidget(wrapper_widget)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.boxes.append(t_cbx)

        root.addWidget(goods_host, 0, Qt.AlignTop)
        self._goods_host = goods_host

    def alter_status(self, index):
        self.config.set(
            key='CommonShopList',
            value=[1 if self.boxes[i].isChecked() else 0 for i in range(len(self.boxes))],
        )

    def _commit_refresh(self):
        self.config.set('CommonShopRefreshTime', int(self.input.text() or 0))
