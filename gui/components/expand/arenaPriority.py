from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIntValidator
from qfluentwidgets import LineEdit

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)

        self.label = QLabel('输入你的排序（如"1234"）', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)

        self.priority_list = [int(x) for x in self.get('arenaPriority')]
        validator = QIntValidator(1234, 4321)
        self.input.setText(''.join([str(x) for x in self.priority_list]))
        self.input.setValidator(validator)
        self.setFixedHeight(53)
        self.hBoxLayout.setContentsMargins(48, 0, 0, 0)

        self.accept.clicked.connect(self.__accept)

        self.hBoxLayout.addWidget(self.label, 20, Qt.AlignLeft)
        self.hBoxLayout.addWidget(self.input, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.accept, 0, Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

    def __accept(self):
        self.priority_list = [int(x) for x in self.input.text()]
        self.set('arenaPriority', self.priority_list)
        print(self.priority_list)