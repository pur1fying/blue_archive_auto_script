from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from qfluentwidgets import LineEdit

from gui.util import notification


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.__check_version()
        self.hBoxLayout = QHBoxLayout(self)
        self.label = QLabel('输入你的每个区域日程的次数（国服6个区域，国际服9个区域）（如"111111"）', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)
        _set_ = self.config.get('lesson_times')
        self.priority_list = [int(x) for x in (_set_ if _set_ else [1, 1, 1, 1, 1])]
        validate = QDoubleValidator()
        self.input.setText(''.join([str(x) for x in self.priority_list]))
        self.input.setValidator(validate)
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
        pre_list = [int(x) for x in self.input.text()]
        info_widget = self.parent().parent().parent().parent().parent().parent().parent()
        if self.config.server_mode in [1, 2] and pre_list.__len__() != 9:
            return notification.error('日程次数', '国际服模式下，输入的区域次数不满足9个', info_widget)
        elif self.config.server_mode == 0 and pre_list.__len__() != 6:
            return notification.error('日程次数', '国服模式下，输入的区域次数不满足6个', info_widget)
        self.priority_list = pre_list
        self.config.set('lesson_times', self.priority_list)
        return notification.success('日程次数', f'日程次数设置成功为:{self.priority_list}', info_widget)

    def __check_version(self):
        conf = self.config.get('lesson_times')
        if self.config.server_mode == 1 and conf.__len__() != 9:
            self.config.set('lesson_times', [1, 1, 1, 1, 1, 1, 1, 1, 1])
        elif self.config.server_mode == 0 and conf.__len__() != 6:
            self.config.set('lesson_times', [1, 1, 1, 1, 1, 1])
