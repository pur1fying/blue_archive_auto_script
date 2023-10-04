import threading

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (PrimaryPushSettingCard, SubtitleLabel, setFont, ExpandLayout)

from gui.components.logger_box import LoggerBox
from main import Main

MAIN_BANNER = 'gui/assets/banner_home_bg.png'


class HomeFragment(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.expandLayout = ExpandLayout(self)
        self.vBoxLayout = QVBoxLayout(self)

        title = '蔚蓝档案自动脚本'
        self.once = True
        self.label = SubtitleLabel(title, self)
        setFont(self.label, 24)
        self.banner = QLabel(self)
        self.banner.setFixedHeight(200)
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)

        self.startupCard = PrimaryPushSettingCard(
            self.tr('启动'),
            FIF.CARE_RIGHT_SOLID,
            self.tr('档案，启动'),
            '开始你的档案之旅',
            self
        )
        self.__initLayout()
        self.setObjectName("0x00000003")

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
        self.expandLayout.addWidget(self.banner)
        self.expandLayout.addWidget(self.label)
        self.expandLayout.addWidget(self.startupCard)
        self.logger = LoggerBox(self.expandLayout, self)
        self._main_thread = Main(logger_box=self.logger)
        self.startupCard.clicked.connect(self.__init_starter)

    def __init_starter(self):
        threading.Thread(target=self.__worker).start()

    def __worker(self):
        if self._main_thread.flag_run:
            self._main_thread.flag_run = False
            self.startupCard.button.setText("启动")
            self._main_thread.send('stop')
        else:
            self._main_thread.flag_run = True
            self.startupCard.button.setText("停止")
            self._main_thread.send('start')
