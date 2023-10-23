from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel, SettingCardGroup)

from gui.components.conf_exe_card import ServerSettingCard
from gui.components.conf_file_card import FileSelectSettingCard
from gui.components.conf_goods_card import ItemSelectSettingCard
from gui.components.conf_story_card import StorySettingCard
from gui.util.config import conf_global


class SettingsFragment(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.tr("设置"), self.scrollWidget)

        self.basicGroup = SettingCardGroup(
            self.tr("基本"), self.scrollWidget)

        self.folderOption = FileSelectSettingCard(
            conf_global.emulatorPath,
            title=self.tr('模拟器目录'),
            filePath=QStandardPaths.writableLocation(QStandardPaths.MusicLocation),
            parent=self.basicGroup
        )

        self.serverOption = ServerSettingCard(
            configServer=conf_global.server,
            configPort=conf_global.port,
            title=self.tr('应用相关设置'),
            stop='官服',
            parent=self.basicGroup
        )

        self.shopOption = ItemSelectSettingCard(
            conf_global.shopList,
            title=self.tr('商店商品选择'),
            goodsList=[0] * 16,
            parent=self.basicGroup
        )

        self.storyOption = StorySettingCard(
            conf_global.mainStop,
            title=self.tr('主线任务选择'),
            stop='4-4',
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
        self.basicGroup.addSettingCard(self.folderOption)
        self.basicGroup.addSettingCard(self.shopOption)
        self.basicGroup.addSettingCard(self.storyOption)
        self.basicGroup.addSettingCard(self.serverOption)
        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)

        self.setWidget(self.scrollWidget)
