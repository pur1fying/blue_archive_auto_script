import time
from hashlib import md5
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel, SettingCardGroup)

from gui.components import expand
from gui.components.template_card import SimpleSettingCard


class SettingsFragment(ScrollArea):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.tr(f"普通设置 {self.config['name']}"), self.scrollWidget)

        self.basicGroup = SettingCardGroup(
            self.tr("基本"), self.scrollWidget)

        self.serverOption = SimpleSettingCard(
            title='应用相关设置',
            content='选择你的服务器平台，设置你的端口（不知道端口请设置为0）',
            sub_view=expand.__dict__['serverConfig'],
            parent=self.basicGroup,
            config=self.config
        )

        self.scriptOption = SimpleSettingCard(
            title='脚本相关设置',
            content='根据你的电脑配置，调整相应的参数。',
            sub_view=expand.__dict__['scriptConfig'],
            parent=self.basicGroup,
            config=self.config
        )

        self.exploreGroup = SettingCardGroup(
            self.tr("相关设置"), self.scrollWidget)

        self.exploreOption = SimpleSettingCard(
            title='普通图推图设置',
            content='根据你的推图需求，调整相应的参数。',
            sub_view=expand.__dict__['exploreConfig'],
            parent=self.exploreGroup,
            config=self.config
        )

        self.hardOption = SimpleSettingCard(
            title='困难图推图设置',
            content='根据你所需困难图刷关，设置参数。',
            sub_view=expand.__dict__['hardTaskConfig'],
            parent=self.exploreGroup,
            config=self.config
        )

        self.otherOption = SimpleSettingCard(
            title='其他设置',
            content='其他的一些小功能与设置',
            sub_view=expand.__dict__['otherConfig'],
            parent=self.exploreGroup,
            config=self.config
        )

        self.__initLayout()
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(self.object_name)

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.settingLabel.setObjectName('settingLabel')
        self.setStyleSheet('''
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        ''')
        self.viewport().setStyleSheet("background-color: transparent;")
        self.basicGroup.addSettingCard(self.serverOption)
        self.basicGroup.addSettingCard(self.scriptOption)
        self.exploreGroup.addSettingCard(self.exploreOption)
        self.exploreGroup.addSettingCard(self.hardOption)
        self.exploreGroup.addSettingCard(self.otherOption)
        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)
        self.expandLayout.addWidget(self.exploreGroup)

        self.setWidget(self.scrollWidget)
