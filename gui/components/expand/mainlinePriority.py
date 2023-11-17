from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qfluentwidgets import LineEdit, InfoBar, InfoBarIcon, InfoBarPosition

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.info_widget = self.parent()
        self.hBoxLayout = QVBoxLayout(self)
        self.lay1 = QHBoxLayout(self)
        self.lay2 = QHBoxLayout(self)
        self.lay1_hard = QHBoxLayout(self)
        self.lay2_hard = QHBoxLayout(self)

        self.label = QLabel('普通关卡与次数（如"1-1-1,1-2-3"表示关卡1-1打一次，然后关卡1-2打三次）：', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)
        self.label_hard = QLabel('困难关卡设置同上，注意：次数最多为3），逗号均为英文逗号：', self)
        self.input_hard = LineEdit(self)
        self.accept_hard = QPushButton('确定', self)

        _set_main = self.get('mainlinePriority')
        self.main_priority = [tuple(x.split('-')) for x in _set_main.split(',')]

        _set_hard = self.get('hardPriority')
        self.hard_priority = [tuple(x.split('-')) for x in _set_hard.split(',')]

        self.setFixedHeight(200)

        self.input.setText(_set_main)
        self.input_hard.setText(_set_hard)

        self.input.setFixedWidth(700)
        self.input_hard.setFixedWidth(700)

        self.lay1.setContentsMargins(10, 0, 0, 10)
        self.lay2.setContentsMargins(10, 0, 0, 10)
        self.lay1_hard.setContentsMargins(10, 0, 0, 10)
        self.lay2_hard.setContentsMargins(10, 0, 0, 10)

        self.accept.clicked.connect(self.__accept_main)
        self.accept_hard.clicked.connect(self.__accept_hard)

        self.lay1.addWidget(self.label, 0, Qt.AlignLeft)
        self.lay2.addWidget(self.input, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.accept, 0, Qt.AlignLeft)
        self.lay1_hard.addWidget(self.label_hard, 0, Qt.AlignLeft)
        self.lay2_hard.addWidget(self.input_hard, 1, Qt.AlignLeft)
        self.lay2_hard.addWidget(self.accept_hard, 0, Qt.AlignLeft)

        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)
        self.lay2.setAlignment(Qt.AlignCenter)
        self.lay1_hard.addStretch(1)
        self.lay1_hard.setAlignment(Qt.AlignCenter)
        self.lay2_hard.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay2)

        self.hBoxLayout.addLayout(self.lay1_hard)
        self.hBoxLayout.addLayout(self.lay2_hard)

    def __accept_main(self):
        input_content = self.input.text()
        self.set('mainlinePriority', input_content)
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的普通关卡已经被设置为：{input_content}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()

    def __accept_hard(self):
        input_content = self.input_hard.text()
        self.set('hardPriority', input_content)
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的困难关卡已经被设置为：{input_content}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()
