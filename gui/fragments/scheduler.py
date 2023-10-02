from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel, ComboBoxSettingCard)
from qfluentwidgets import FluentIcon as FIF, SettingCardGroup, SwitchSettingCard

from gui.components.ex_multi_set import MultiSetSettingCard
from gui.util.config import conf


class SchedulerFragment(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.tr("调度设置"), self)

        self.basicGroup = SettingCardGroup(
            self.tr("基础功能"), self.scrollWidget)

        self.cafeOption = SwitchSettingCard(
            FIF.CHECKBOX,
            self.tr('咖啡厅'),
            self.tr('帮助你收集咖啡厅体力和信用点'),
            configItem=conf.cafe,
            parent=self.basicGroup
        )

        self.teamOption = SwitchSettingCard(
            FIF.CHECKBOX,
            self.tr('小组'),
            self.tr('帮助你收集小组体力'),
            configItem=conf.team,
            parent=self.basicGroup
        )

        self.collectOption = SwitchSettingCard(
            FIF.CHECKBOX,
            self.tr('日常收集体力'),
            self.tr('帮助你自动收集体力'),
            configItem=conf.dailyCollect,
            parent=self.basicGroup
        )
        #
        self.consumeOption = SwitchSettingCard(
            FIF.CALORIES,
            self.tr('日常消耗体力'),
            self.tr('帮助你自动打关消体力升级'),
            configItem=conf.dailyConsume,
            parent=self.basicGroup
        )

        # self.shopListOption = ComboBoxSettingCard(
        #     configItem=conf.shopList,
        #     icon=FIF.CHECKBOX,
        #     title=self.tr('商店购买'),
        #     content=self.tr('帮助你自动购买商店物品'),
        #     parent=self.basicGroup
        # )

        self.emailOption = SwitchSettingCard(
            FIF.MAIL,
            self.tr('查收邮箱'),
            self.tr('帮助你自动收集邮箱奖励'),
            configItem=conf.emailCheck,
            parent=self.basicGroup
        )

        self.hardModeCombatOption = SwitchSettingCard(
            FIF.CALORIES,
            self.tr('日常困难'),
            self.tr('帮助你自动打困难关'),
            configItem=conf.hardModeCombat,
            parent=self.basicGroup
        )

        self.__initLayout()
        self.__initWidget()
        self.setObjectName("0x00000002")

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

        self.basicGroup.addSettingCard(self.collectOption)
        self.basicGroup.addSettingCard(self.consumeOption)
        self.basicGroup.addSettingCard(self.emailOption)
        self.basicGroup.addSettingCard(self.hardModeCombatOption)
        self.basicGroup.addSettingCard(self.cafeOption)
        # self.basicGroup.addSettingCard(self.shopListOption)
        self.basicGroup.addSettingCard(self.teamOption)
        self.basicGroup.addSettingCard(self.teamOption)

        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)

    def __initWidget(self):
        self.setWidget(self.scrollWidget)
