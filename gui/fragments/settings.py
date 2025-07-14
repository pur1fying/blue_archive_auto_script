import time
from hashlib import md5
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ComboBoxSettingCard, ExpandLayout, FluentIcon as FIF, ScrollArea, TitleLabel,
                            SettingCardGroup,
                            SwitchSettingCard, OptionsSettingCard, CustomColorSettingCard, setTheme, setThemeColor)

import window
from gui.components import expand
from gui.components.template_card import SimpleSettingCard
from gui.util import notification
from gui.util.config_gui import configGui, isWin11
from gui.util.language import Language


class SettingsFragment(ScrollArea):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.scrollWidget)
        config.inject(self.settingLabel, self.tr(f"普通设置") + " {name}")

        self.basicGroup = SettingCardGroup(
            self.tr("基本"), self.scrollWidget)

        self.basicGroupItems = [
            SimpleSettingCard(
                title=self.tr('应用相关设置'),
                content=self.tr('选择你的服务器平台，设置你的端口（不知道端口请设置为0）'),
                sub_view=expand.__dict__['serverConfig'],
                parent=self.basicGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr('脚本相关设置'),
                content=self.tr('根据你的电脑配置，调整相应的参数。'),
                sub_view=expand.__dict__['scriptConfig'],
                parent=self.basicGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr("模拟器启动设置"),
                content=self.tr("设置启动模拟器的路径"),
                sub_view=expand.__dict__['emulatorConfig'],
                parent=self.basicGroup,
                config=self.config
            )
        ]

        self.exploreGroup = SettingCardGroup(
            self.tr("相关设置"), self.scrollWidget)

        self.exploreGroupItems = [
            SimpleSettingCard(
                title=self.tr('编队配置'),
                content=self.tr('根据你的实际情况，设置编队相关参数。'),
                sub_view=expand.__dict__['formationConfig'],
                parent=self.exploreGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr('推图设置'),
                content=self.tr('根据你所需推图关卡，设置参数。'),
                sub_view=expand.__dict__['exploreConfig'],
                parent=self.exploreGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr('推剧情'),
                content=self.tr('主线剧情，小组剧情，支线剧情'),
                sub_view=expand.__dict__['proceedPlot'],
                parent=self.exploreGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr('活动图设置'),
                content=self.tr('推故事，推任务，推挑战'),
                sub_view=expand.__dict__['eventMapConfig'],
                parent=self.exploreGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr('其他设置'),
                content=self.tr('其他的一些小功能与设置'),
                sub_view=expand.__dict__['otherConfig'],
                parent=self.exploreGroup,
                config=self.config
            ),

            SimpleSettingCard(
                title=self.tr('推送设置'),
                content=self.tr('推送信息'),
                sub_view=expand.__dict__['pushConfig'],
                parent=self.exploreGroup,
                config=self.config
            )]

        self.guiGroup = SettingCardGroup(
            self.tr('图形用户界面'), self.scrollWidget)

        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('云母效果'),
            self.tr('将半透明应用于窗口和表面'),
            configGui.micaEnabled,
            self.guiGroup
        )
        self.micaCard.setEnabled(isWin11())
        self.themeCard = OptionsSettingCard(
            configGui.themeMode,
            FIF.BRUSH,
            self.tr('应用主题'),
            self.tr("更改应用的外观"),
            texts=[
                self.tr('浅色'), self.tr('深色'),
                self.tr('使用系统设置')
            ],
            parent=self.guiGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            configGui.themeColor,
            FIF.PALETTE,
            self.tr('主题颜色'),
            self.tr('更改应用的主题颜色'),
            self.guiGroup
        )
        self.zoomCard = OptionsSettingCard(
            configGui.dpiScale,
            FIF.ZOOM,
            self.tr("界面缩放"),
            self.tr("更改小部件和字体的大小"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("使用系统设置")
            ],
            parent=self.guiGroup
        )

        self.languageCard = ComboBoxSettingCard(
            configGui.language,
            FIF.LANGUAGE,
            self.tr('语言'),
            self.tr('设置界面的首选语言'),
            texts=Language.combobox(),
            parent=self.guiGroup
        )

        self.modeCard = ComboBoxSettingCard(
            configGui.configDisplayType,
            FIF.LIBRARY,
            self.tr('配置界面模式'),
            self.tr('设置配置界面模式'),
            texts=["Card", "List"],
            parent=self.guiGroup
        )

        self.modeCardType = ComboBoxSettingCard(
            configGui.cardDisplayType,
            FIF.LIBRARY,
            self.tr('卡片显示模式'),
            self.tr('卡片是否显示精美图片'),
            texts=["withImage", "plainText"],
            parent=self.guiGroup
        )

        self.guiGroupItems = [
            self.languageCard, self.micaCard, self.themeCard, self.themeColorCard, self.zoomCard, self.modeCard,
            self.modeCardType
        ]

        self.__initLayout()
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f"{self.object_name}.SettingsFragment")
        self.__connectSignalToSlot()

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

        self.basicGroup.addSettingCards(self.basicGroupItems)
        self.exploreGroup.addSettingCards(self.exploreGroupItems)
        self.guiGroup.addSettingCards(self.guiGroupItems)

        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)
        self.expandLayout.addWidget(self.exploreGroup)
        self.expandLayout.addWidget(self.guiGroup)

        self.setWidget(self.scrollWidget)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        if time.time() - window.LAST_NOTICE_TIME < 0.1:
            return
        # Puzzling Error for config missing ...
        # Now that the bug concerning #274 can't be represented, this is a simple fix.
        if self.config is not None:
            notification.success(
                self.tr('更新成功'),
                self.tr('配置将在重新启动后生效'),
                self.config
            )
        window.LAST_NOTICE_TIME = time.time()

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        configGui.appRestartSig.connect(self.__showRestartTooltip)
        self.themeCard.optionChanged.connect(lambda ci: setTheme(configGui.get(ci)))
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(lambda x: configGui.micaEnableChanged.emit(x))
