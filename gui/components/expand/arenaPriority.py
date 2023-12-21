from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtGui import QIntValidator
from qfluentwidgets import LineEdit, InfoBar, InfoBarIcon, InfoBarPosition

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(120)
        self.info_widget = self.parent()
        self.hBoxLayout = QVBoxLayout(self)
        self.lay_1 = QHBoxLayout(self)
        self.lay_2 = QHBoxLayout(self)
        self.label_1 = QLabel('输入你需要对手比你低几级，高几级则填负数：', self)
        self.label_2 = QLabel('输入你最多需要刷新几次：', self)
        self.input_1 = LineEdit(self)
        self.input_2 = LineEdit(self)
        self.accept_1 = QPushButton('确定', self)
        self.accept_2 = QPushButton('确定', self)

        self.level_diff = self.get('ArenaLevelDiff')
        validator_1 = QIntValidator(-50, 50)
        self.input_1.setText(str(self.level_diff))
        self.input_1.setValidator(validator_1)
        self.hBoxLayout.setContentsMargins(24, 0, 24, 0)

        self.refresh_times = self.get('maxArenaRefreshTimes')
        validator_2 = QIntValidator(0, 50)
        self.input_2.setText(str(self.refresh_times))
        self.input_2.setValidator(validator_2)

        self.accept_1.clicked.connect(self.__accept_1)
        self.accept_2.clicked.connect(self.__accept_2)

        self.lay_1.addWidget(self.label_1, 20, Qt.AlignLeft)
        self.lay_1.addWidget(self.input_1, 0, Qt.AlignRight)
        self.lay_1.addWidget(self.accept_1, 0, Qt.AlignCenter)

        self.lay_2.addWidget(self.label_2, 20, Qt.AlignLeft)
        self.lay_2.addWidget(self.input_2, 0, Qt.AlignRight)
        self.lay_2.addWidget(self.accept_2, 0, Qt.AlignCenter)

        self.hBoxLayout.setContentsMargins(24, 0, 24, 0)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay_1)
        self.hBoxLayout.addLayout(self.lay_2)

    def __accept_1(self, changed_text=None):
        self.level_diff = int(self.input_1.text())
        self.set('ArenaLevelDiff', self.level_diff)
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你需要对手比你低{self.level_diff}级',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()

    def __accept_2(self, changed_text=None):
        self.refresh_times = int(self.input_2.text())
        self.set('maxArenaRefreshTimes', self.refresh_times)
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你最大刷新次数设置为：{self.refresh_times}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()
