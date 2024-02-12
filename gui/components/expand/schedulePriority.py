from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qfluentwidgets import LineEdit

from gui.util import notification


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        ls_names = self.config.static_config['lesson_region_name']
        self.count = [ls_names["CN"].__len__(), ls_names["Global"].__len__(), ls_names["JP"].__len__()]
        self.__check_version()
        self.hBoxLayout = QVBoxLayout(self)
        self.h1 = QHBoxLayout(self)
        self.label = QLabel(
            f'输入你的每个区域日程的次数（国服、国际服、日服分别有{"、".join(list(map(lambda x: str(x), self.count)))}个区域）'
            f'（如"111111"）', self)
        self.input = LineEdit(self)
        self.accept = QPushButton('确定', self)
        _set_ = self.config.get('lesson_times')
        self.priority_list = [int(x) for x in (_set_ if _set_ else [1, 1, 1, 1, 1])]
        validate = QDoubleValidator()
        self.input.setText(''.join([str(x) for x in self.priority_list]))
        self.input.setFixedWidth(300)
        self.input.setValidator(validate)
        self.hBoxLayout.setContentsMargins(48, 0, 0, 0)

        self.accept.clicked.connect(self.__accept)

        self.hBoxLayout.addWidget(self.label, 20, Qt.AlignLeft)
        self.h1.addWidget(self.input, 0, Qt.AlignLeft)
        self.h1.addWidget(self.accept, 0, Qt.AlignRight)
        self.h1.setContentsMargins(0, 10, 0, 0)
        self.hBoxLayout.addLayout(self.h1)
        self.hBoxLayout.setContentsMargins(20, 10, 0, 0)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignLeft)

    def __accept(self):
        pre_list = [int(x) for x in self.input.text()]
        info_widget = self.parent().parent().parent().parent().parent().parent().parent()
        if self.config.server_mode == 'Global' and pre_list.__len__() != self.count[1]:
            return notification.error('日程次数', f'国际服模式下，输入的区域次数不满足{self.count[1]}个', info_widget)
        elif self.config.server_mode == 'CN' and pre_list.__len__() != self.count[0]:
            return notification.error('日程次数', f'国服模式下，输入的区域次数不满足{self.count[0]}个', info_widget)
        elif self.config.server_mode == 'JP' and pre_list.__len__() != self.count[2]:
            return notification.error('日程次数', f'日服模式下，输入的区域次数不满足{self.count[2]}个', info_widget)
        self.priority_list = pre_list
        self.config.set('lesson_times', self.priority_list)
        return notification.success('日程次数', f'日程次数设置成功为:{self.priority_list}', info_widget)

    def __check_version(self):
        conf = self.config.get('lesson_times')
        if self.config.server_mode == 'Global' and conf.__len__() != self.count[1]:
            self.config.set('lesson_times', [1] * self.count[1])
        elif self.config.server_mode == 'CN' and conf.__len__() != self.count[0]:
            self.config.set('lesson_times', [1] * self.count[0])
        elif self.config.server_mode == 'JP' and conf.__len__() != self.count[2]:
            self.config.set('lesson_times', [1] * self.count[2])
