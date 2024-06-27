from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from qfluentwidgets import FlowLayout, CheckBox, LineEdit

from gui.util.translator import baasTranslator as bt


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.default_goods = self.config.static_config['common_shop_price_list'][self.config.server_mode]
        print(len(self.default_goods))
        self.__check_server()
        self.goods = self.config.get(key='CommonShopList')

        layout = FlowLayout(self, needAni=True)

        layout.setContentsMargins(30, 0, 30, 0)
        layout.setVerticalSpacing(0)
        # layout.setHorizontalSpacing(10)

        self.setFixedHeight(700)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')
        self.label = QLabel(self.tr('刷新次数'), self)
        self.label.setFixedWidth(160)
        self.input = LineEdit(self)
        self.input.setValidator(QIntValidator(0, 5))
        print(self.config.get('CommonShopRefreshTime'))
        self.input.setText(str(self.config.get('CommonShopRefreshTime')))
        self.accept = QPushButton(self.tr('确定'), self)
        self.boxes = []
        for i in range(len(self.goods)):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.goods[i] == 1)
            ccs = QLabel(bt.tr('ConfigTranslation', self.default_goods[i][0]), self)
            ccs.setFixedWidth(150)
            price_text = str(self.default_goods[i][1])
            if self.default_goods[i][2] == 'creditpoints':
                price_text += self.tr('信用点')
            else:
                price_text += self.tr('青辉石')
            price_label = QLabel(price_text, self)
            price_label.setFixedWidth(150)
            wrapper_widget = QWidget()
            VLayout = QVBoxLayout(self)
            VLayout.addWidget(ccs)
            VLayout.addWidget(price_label)
            wrapper = QHBoxLayout()
            wrapper.addLayout(VLayout)
            wrapper.addWidget(t_cbx)
            wrapper_widget.setLayout(wrapper)
            layout.addWidget(wrapper_widget)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.boxes.append(t_cbx)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.accept)
        self.accept.clicked.connect(self.__accept)

    def alter_status(self, index):
        self.boxes[index].setChecked(self.boxes[index].isChecked())
        self.config.set(key='CommonShopList', value=[1 if self.boxes[i].isChecked() else 0 for i in range(len(self.boxes))])

    def __accept(self, input_content=None):
        self.config.set('CommonShopRefreshTime', self.input.text())

    def __check_server(self):
        if len(self.config.get('CommonShopList')) != len(self.default_goods):
            self.config.set('CommonShopList', len(self.default_goods) * [0])
