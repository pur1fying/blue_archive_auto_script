from PyQt5.QtWidgets import QWidget, QLabel
from qfluentwidgets import FlowLayout, CheckBox

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(120)

        self.goods = self.get(key='ArenaShopList')

        layout = FlowLayout(self, needAni=True)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setVerticalSpacing(20)
        layout.setHorizontalSpacing(10)

        self.setFixedSize(720, 200)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')

        self.boxes = []
        for i in range(13):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.goods[i] == 1)
            ccs = QLabel(f"商品{i + 1}", self)
            ccs.setFixedWidth(80)
            layout.addWidget(ccs)
            layout.addWidget(t_cbx)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.boxes.append(t_cbx)

    def alter_status(self, index):
        self.boxes[index].setChecked(self.boxes[index].isChecked())
        self.set(key='ArenaShopList', value=[1 if self.boxes[i].isChecked() else 0 for i in range(13)])

