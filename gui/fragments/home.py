import datetime
import threading
import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap

from qfluentwidgets import (PrimaryPushSettingCard, SubtitleLabel, setFont, ExpandLayout)
from qfluentwidgets import FluentIcon as FIF

from gui.components.logger_box import LoggerBox
from main import Main

MAIN_BANNER = '../assets/banner_home_bg.png'


class HomeFragment(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.expandLayout = ExpandLayout(self)
        self.vBoxLayout = QVBoxLayout(self)

        title = '蔚蓝档案自动脚本'
        self.started = False
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
        if self.started:
            self._main_thread.send('stop')
            self.started = False
            self.startupCard.setText('启动')
            self.startupCard.setSubText('档案，启动')
            self.startupCard.setIcon(FIF.CARE_RIGHT_SOLID)
            self.logger.d('已停止')
