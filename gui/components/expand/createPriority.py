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

        self.label = QLabel('用">"分割物品，排在前面的会优先选择', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)

        _set_main = self.get('createPriority')

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
        self.set('createPriority', input_content)
