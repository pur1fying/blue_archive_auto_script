from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from qfluentwidgets import FlowLayout, CheckBox, LineEdit

from gui.util.translator import baasTranslator as bt


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.default_goods = self.config.static_config['tactical_challenge_shop_price_list'][self.config.server_mode]
        self.__check_server()
        self.goods = self.config.get(key='TacticalChallengeShopList')
        goods_count = len(self.goods)
        layout = FlowLayout(self, needAni=True)
        layout.setContentsMargins(30, 0, 0, 30)
        layout.setVerticalSpacing(0)
        # layout.setHorizontalSpacing(0)

        self.setFixedHeight(400)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')
        self.label = QLabel(self.tr('刷新次数'), self)
        self.input = LineEdit(self)
        self.input.setValidator(QIntValidator(0, 3))
        self.input.setText(self.config.get('TacticalChallengeShopRefreshTime'))

        self.accept = QPushButton(self.tr('确定'), self)
        self.boxes = []
        for i in range(0, goods_count):
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
            layout.addWidget(wrapper_widget)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index, goods_count))
            self.boxes.append(t_cbx)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.accept)
        self.accept.clicked.connect(self.__accept)

    def alter_status(self, index, goods_count):
        self.boxes[index].setChecked(self.boxes[index].isChecked())
        self.config.set(key='TacticalChallengeShopList',
                        value=[1 if self.boxes[i].isChecked() else 0 for i in range(0, goods_count)])

    def __accept(self):
        self.config.set('TacticalChallengeShopRefreshTime', self.input.text())

    def __check_server(self):
        if len(self.config.get('TacticalChallengeShopList')) != len(self.default_goods):
            self.config.set('TacticalChallengeShopList', len(self.default_goods) * [0])
