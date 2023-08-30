import threading

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap

from qfluentwidgets import (PrimaryPushSettingCard, SubtitleLabel, setFont, ExpandLayout)
from qfluentwidgets import FluentIcon as FIF

from main import Baas


class HomeFragment(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.expandLayout = ExpandLayout(self)
        self.vBoxLayout = QVBoxLayout(self)

        title = '蔚蓝档案自动脚本'
        self.label = SubtitleLabel(title, self)
        setFont(self.label, 24)
        self.banner = QLabel(self)
        self.banner.setFixedHeight(200)
        pixmap = QPixmap("../../assets/banner_home_bg.png").scaled(
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

        self.setObjectName(title.replace(' ', '-'))

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
        self.expandLayout.addWidget(self.banner)
        self.expandLayout.addWidget(self.label)
        self.expandLayout.addWidget(self.startupCard)
        self.startupCard.clicked.connect(lambda: threading.Thread(target=Baas().start_ba()).start())
