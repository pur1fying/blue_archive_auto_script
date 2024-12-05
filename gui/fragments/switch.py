import json
import threading
import time
from datetime import datetime
from hashlib import md5
from random import random
from typing import Union

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel, FlowLayout)
from qfluentwidgets import SettingCardGroup

from gui.components import expand
from gui.components.template_card import TemplateSettingCard, TemplateSettingCardForClick
from gui.util.config_gui import configGui

lock = threading.Lock()


class SwitchFragment(ScrollArea):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.flowLayout = None
        self.config = config
        self._config_update()
        # 创建一个QWidget实例作为滚动区域的内容部件
        self.scrollWidget = QWidget()
        # 创建一个ExpandLayout实例作为滚动区域的布局管理器
        self.expandLayout = ExpandLayout(self.scrollWidget)
        # 创建一个标题为“调度设置”的TitleLabel实例
        self.settingLabel = TitleLabel(self.scrollWidget)
        config.inject(self.settingLabel, self.tr("配置设置") + " {name}")
        self.configLoadType = configGui.configLoadType.value
        # 初始化basicGroup变量,_setting_cards列表
        self.basicGroup = None
        self._setting_cards = []
        self._event_config, self._switch_config = [], []  # 初始化_event_config和_switch_config列表
        self._read_config()  # 调用_read_config()方法读取配置文件并更新_event_config和_switch_config列表
        # 创建一个定时器，500毫秒后调用_lazy_load()方法，延迟加载设置，避免卡顿
        QTimer.singleShot(500, self._lazy_load)
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(self.object_name)

    # def _change_status(self, event_name: str, event_enabled: str) -> None:
    #     self._read_config()  # 读取配置文件并更新_event_config列表
    #     # 更新_event_config列表中与给定事件名称相对应的元素的enabled属性值
    #     self._event_config = [
    #         {**item, 'enabled': event_enabled}
    #         if item['event_name'] == event_name else item
    #         for item in self._event_config
    #     ]
    #     self._commit_change()  # 调用_commit_change()方法提交更改

    # def update_status(self, event_name: str, event_enabled: str) -> None:
    #     self._read_config()  # 读取配置文件并更新_event_config和_switch_config列表
    #     # 根据_switch_config和_event_config列表的元素创建SettingCard对象，并将其添加到_setting_cards列表中
    #     self._setting_cards = [
    #         self._create_card(
    #             name=item_event['event_name'],
    #             tip=item_switch['tip'],
    #             # enabled=item_event['enabled'],
    #             # next_tick=item_event['next_tick'],
    #             setting_name=item_switch['config']
    #         )
    #         for item_event in self._event_config
    #         for item_switch in self._switch_config
    #         if item_event['event_name'] == item_switch['name']
    #     ]
    #     # 将_setting_cards列表中的SettingCard对象添加到basicGroup中
    #     self.basicGroup.addSettingCards(self._setting_cards)

    def _config_update(self):
        self._common_shop_config_update()
        self._tactical_challenge_shop_config_update()
        self._create_config_update()

    def _common_shop_config_update(self):
        default_goods = self.config.static_config['common_shop_price_list'][self.config.server_mode]
        if len(self.config.get('CommonShopList')) != len(default_goods):
            self.config.set('CommonShopList', len(default_goods) * [0])

    def _tactical_challenge_shop_config_update(self):
        default_goods = self.config.static_config['tactical_challenge_shop_price_list'][self.config.server_mode]
        if len(self.config.get('TacticalChallengeShopList')) != len(default_goods):
            self.config.set('TacticalChallengeShopList', len(default_goods) * [0])

    def _create_config_update(self):
        for phase in range(1, 4):
            cfg_key_name = 'createPriority_phase' + str(phase)
            current_priority = self.config.get(cfg_key_name)
            res = []
            default_priority = self.config.static_config['create_default_priority'][self.config.server_mode]["phase" + str(phase)]
            for i in range(0, len(current_priority)):
                if current_priority[i] in default_priority:
                    res.append(current_priority[i])
            for j in range(0, len(default_priority)):
                if default_priority[j] not in res:
                    res.append(default_priority[j])
            self.config.set(cfg_key_name, res)

    def _lazy_load(self):
        # 根据_switch_config和_event_config列表的元素创建SettingCard对象，并将其添加到_setting_cards列表中
        self._setting_cards = [
            self._create_card(
                name=item_event['name'],
                tip=item_event['tip'],
                setting_name=item_event['config']
            )
            for item_event in self._switch_config
        ]

        self.__initLayout()  # 调用__initLayout()方法初始化布局
        self.__initWidget()  # 调用__initWidget()方法初始化部件

    def _change_time(self, event_name: str, event_time: str) -> None:
        try:
            event_time = int(datetime.strptime(event_time, "%Y-%m-%d %H:%M:%S").timestamp())
        except ValueError:
            return
        self._read_config()  # 读取配置文件并更新_event_config列表
        # 更新_event_config列表中与给定事件名称相对应的元素的next_tick属性值
        self._event_config = [
            {**item, 'next_tick': event_time}
            if item['event_name'] == event_name else item
            for item in self._event_config
        ]
        self._commit_change()  # 调用_commit_change()方法提交更改

    def _create_card(self, name: str, tip: str, setting_name: str) -> Union[
        TemplateSettingCard, TemplateSettingCardForClick]:
        Component = TemplateSettingCardForClick if self.configLoadType == 'Card' else TemplateSettingCard
        _switch_card = Component(
            title=name,
            content=tip,
            parent=self.basicGroup,
            sub_view=expand.__dict__[setting_name] if setting_name else None,
            config=self.config,
            context='ConfigTranslation',
            setting_name=setting_name
        )  # 创建TemplateSettingCard实例
        return _switch_card  # 返回创建的TemplateSettingCard实例

    def _commit_change(self):
        with lock:
            with open(self.config.config_dir + '/event.json', 'w', encoding='utf-8') as f:
                json.dump(self._event_config, f, ensure_ascii=False, indent=2)  # 将_event_config列表写入配置文件

    def _read_config(self):
        with lock:
            with open(self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)  # 从配置文件中读取数据并更新_event_config列表
            with open(self.config.config_dir + '/switch.json', 'r', encoding='utf-8') as f:
                self._switch_config = json.load(f)  # 从配置文件中读取数据并更新_switch_config列表

    def update_settings(self):
        if self.configLoadType == 'List':
            if self.basicGroup is not None:
                self.basicGroup.deleteLater()  # 如果basicGroup已经存在，则删除它

            self.basicGroup = SettingCardGroup(self.tr("功能开关"),
                                               self.scrollWidget)  # 创建一个标题为"功能开关"的SettingCardGroup实例
            self.basicGroup.vBoxLayout.insertSpacing(1, -10)  # 设置basicGroup的垂直布局的间距为20
            self.basicGroup.titleLabel.deleteLater()
            self.basicGroup.addSettingCards(self._setting_cards)  # 将_setting_cards列表中的SettingCard对象添加到basicGroup中
            self.expandLayout.addWidget(self.basicGroup)  # 将basicGroup添加到expandLayout布局中
        else:
            wrapper_widget = QWidget(self.scrollWidget)
            self.flowLayout = FlowLayout(wrapper_widget, needAni=True)  # 创建一个FlowLayout实例作为滚动区域的布局管理器
            self.flowLayout.setSpacing(10)
            self.flowLayout.setAlignment(Qt.AlignTop)
            for card in self._setting_cards:
                self.flowLayout.addWidget(card)
            # Attention: 150 is the height of the card, 4 is the row count
            wrapper_widget.setFixedHeight(150 * 4 + 50)
            self.expandLayout.addWidget(wrapper_widget)

    def __initLayout(self):
        self.expandLayout.setSpacing(28)  # 设置expandLayout的间距为28
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 设置水平滚动条策略为始终关闭
        self.setWidgetResizable(True)  # 设置滚动区域的部件可调整大小
        self.settingLabel.setObjectName('settingLabel')  # 设置settingLabel的对象名称为'settingLabel'
        self.setStyleSheet('''
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        ''')  # 设置滚动区域的样式表
        self.viewport().setStyleSheet("background-color: transparent;")  # 设置滚动区域的背景颜色为透明
        self.expandLayout.addWidget(self.settingLabel)  # 将settingLabel添加到expandLayout布局中
        self.update_settings()  # 调用update_settings()方法更新设置

    def __initWidget(self):
        self.setWidget(self.scrollWidget)  # 设置滚动区域的部件为scrollWidget
