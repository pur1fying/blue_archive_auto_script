import json
import threading
import time
from datetime import datetime
from hashlib import md5
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel)
from qfluentwidgets import SettingCardGroup

from core import EVENT_CONFIG_PATH, SWITCH_CONFIG_PATH
from gui.components import expand
from gui.components.template_card import TemplateSettingCard
from gui.util.config_set import ConfigSet

lock = threading.Lock()


class SwitchFragment(ScrollArea, ConfigSet):
    def __init__(self, parent=None, config_dir: str = 'config.json'):
        super().__init__(parent=parent)
        ConfigSet.__init__(self, config_dir)
        self.config_dir = config_dir
        # 创建一个QWidget实例作为滚动区域的内容部件
        self.scrollWidget = QWidget()
        # 创建一个ExpandLayout实例作为滚动区域的布局管理器
        self.expandLayout = ExpandLayout(self.scrollWidget)
        # 创建一个标题为“调度设置”的TitleLabel实例
        self.settingLabel = TitleLabel(self.tr(f"配置设置 {self.config['name']}"), self.scrollWidget)
        # 初始化basicGroup变量,_setting_cards列表
        self.basicGroup = None
        self._setting_cards = []
        self._event_config, self._switch_config = [], []  # 初始化_event_config和_switch_config列表
        self._read_config()  # 调用_read_config()方法读取配置文件并更新_event_config和_switch_config列表

        # 根据_switch_config和_event_config列表的元素创建SettingCard对象，并将其添加到_setting_cards列表中
        self._setting_cards = [
            self._create_card(
                name=item_event['name'],
                tip=item_event['tip'],
                # enabled=item_event['enabled'],
                # next_tick=item_event['next_tick'],
                setting_name=item_event['config']
            )
            for item_event in self._switch_config
            # for item_event in self._event_config
            # if item_event['event_name'] == item_switch['name']
        ]

        self.__initLayout()  # 调用__initLayout()方法初始化布局
        self.__initWidget()  # 调用__initWidget()方法初始化部件
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

    def _create_card(self, name: str, tip: str, setting_name: str) -> TemplateSettingCard:
        _switch_card = TemplateSettingCard(
            title=name,
            content=tip,
            parent=self.basicGroup,
            sub_view=expand.__dict__[setting_name] if setting_name else None,
            config_dir=self.config_dir
        )  # 创建TemplateSettingCard实例
        # _switch_card.status_switch.setChecked(enabled)  # 设置状态开关的选中状态
        # _switch_card.statusChanged.connect(lambda x: self._change_status(name, x))  # 连接状态开关的状态更改信号和_change_status()方法
        # _switch_card.timeChanged.connect(lambda x: self._change_time(name, x))  # 连接时间更改信号和_change_time()方法
        # _switch_card.timer_box.setText(
        #     datetime.fromtimestamp(float(next_tick)).strftime("%Y-%m-%d %H:%M:%S"))  # 设置计时器文本
        return _switch_card  # 返回创建的TemplateSettingCard实例

    def _commit_change(self):
        with lock:
            with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._event_config, f, ensure_ascii=False, indent=2)  # 将_event_config列表写入配置文件

    def _read_config(self):
        with lock:
            with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)  # 从配置文件中读取数据并更新_event_config列表
            with open(SWITCH_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self._switch_config = json.load(f)  # 从配置文件中读取数据并更新_switch_config列表

    def update_settings(self):
        if self.basicGroup is not None:
            self.basicGroup.deleteLater()  # 如果basicGroup已经存在，则删除它
        self.basicGroup = SettingCardGroup(self.tr("功能开关"), self.scrollWidget)  # 创建一个标题为"功能开关"的SettingCardGroup实例
        self.basicGroup.addSettingCards(self._setting_cards)  # 将_setting_cards列表中的SettingCard对象添加到basicGroup中
        self.expandLayout.addWidget(self.basicGroup)  # 将basicGroup添加到expandLayout布局中

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
