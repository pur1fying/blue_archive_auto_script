from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel, SettingCardGroup)

from gui.components import expand
from gui.components.template_card import SimpleSettingCard
from gui.util.config_set import ConfigSet


class SettingsFragment(ScrollArea, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.tr("设置"), self.scrollWidget)

        self.basicGroup = SettingCardGroup(
            self.tr("基本"), self.scrollWidget)

        self.serverOption = SimpleSettingCard(
            title='应用相关设置',
            content='选择你的服务器平台，设置你的端口（不知道端口请设置为0）',
            sub_view=expand.__dict__['serverConfig'],
            parent=self.basicGroup
        )

        self.scriptOption=SimpleSettingCard(
            title='脚本相关设置',
            content='根据你的电脑配置，调整相应的参数。',
            sub_view=expand.__dict__['scriptConfig'],
            parent=self.basicGroup
        )

        self.__initLayout()
        self.setObjectName("0x00000004")

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
        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)

        self.setWidget(self.scrollWidget)
