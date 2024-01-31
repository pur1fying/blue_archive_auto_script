from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from qfluentwidgets import LineEdit


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.hBoxLayout = QHBoxLayout(self)
        self.label = QLabel('输入你的每个区域日程的次数（国服6个区域，国际服9个区域）（如"111111"）', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)
        _set_ = self.config.get('lesson_times')
        self.priority_list = [int(x) for x in (_set_ if _set_ else [1, 1, 1, 1, 1])]
        validator = QDoubleValidator(10000.0, 10000000000.0, 0, self)
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
        self.config.set('lesson_times', self.priority_list)
