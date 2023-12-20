from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton
from qfluentwidgets import FlowLayout, CheckBox, LineEdit

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(120)

        self.goods = self.get(key='CommonShopList')

        layout = FlowLayout(self, needAni=True)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setVerticalSpacing(20)
        layout.setHorizontalSpacing(10)

        self.setFixedSize(720, 250)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')
        self.label = QLabel('刷新次数', self)
        self.label.setFixedWidth(160)
        self.input = LineEdit(self)
        self.input.setValidator(QIntValidator(0, 5))
        self.input.setText(self.get('ShopRefreshTime'))
        self.accept = QPushButton('确定', self)
        self.boxes = []
        for i in range(16):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.goods[i] == 1)
            ccs = QLabel(f"商品{i + 1}", self)
            ccs.setFixedWidth(80)
            layout.addWidget(ccs)
            layout.addWidget(t_cbx)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.boxes.append(t_cbx)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.accept)
        self.accept.clicked.connect(self.__accept)

    def alter_status(self, index):
        self.boxes[index].setChecked(self.boxes[index].isChecked())
        self.set(key='ShopList', value=[1 if self.boxes[i].isChecked() else 0 for i in range(16)])

    def __accept(self, input_content=None):
        self.set('ShopRefreshTime', self.input.text())
