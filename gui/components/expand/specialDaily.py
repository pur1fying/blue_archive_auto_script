from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qfluentwidgets import LineEdit

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QVBoxLayout(self)

        self.lay1 = QHBoxLayout(self)
        self.lay2 = QHBoxLayout(self)

        self.label = QLabel('三个悬赏委托分别打的难度 0 1 2 3 ... 分别表示 A B C D 难度，与主线输入类似，1-1代表B难度打一次，列表中三个元素：', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)

        _set_main = self.get('specialPriority')

        self.setFixedHeight(120)

        self.input.setText(_set_main)

        self.input.setFixedWidth(700)

        self.lay1.setContentsMargins(10, 0, 0, 10)
        self.lay2.setContentsMargins(10, 0, 0, 10)

        self.accept.clicked.connect(self.__accept_main)

        self.lay1.addWidget(self.label, 0, Qt.AlignLeft)
        self.lay2.addWidget(self.input, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.accept, 0, Qt.AlignLeft)

        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)
        self.lay2.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay2)

    def __accept_main(self):
        input_content = self.input.text()
        self.set('specialPriority', input_content)
