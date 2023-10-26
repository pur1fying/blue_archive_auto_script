import json
import threading
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel)
from qfluentwidgets import SettingCardGroup

from core import EVENT_CONFIG_PATH, SWITCH_CONFIG_PATH
from gui.components import expand
from gui.components.template_card import TemplateSettingCard

lock = threading.Lock()


class SwitchFragment(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.tr("调度设置"), self.scrollWidget)

        self.basicGroup = None

        self._setting_cards = []
        self._event_config, self._switch_config = [], []
        self._read_config()

        self._setting_cards = [
            self._create_card(
                name=item_event['event_name'],
                tip=item_switch['tip'],
                enabled=item_event['enabled'],
                next_tick=item_event['next_tick'],
                setting_name=item_switch['config']
            )
            for item_event in self._event_config
            for item_switch in self._switch_config
            if item_event['event_name'] == item_switch['name']
        ]

        self.__initLayout()
        self.__initWidget()
        self.setObjectName("0x00000002")

    def _change_status(self, event_name: str, event_enabled: str) -> None:
        self._read_config()
        self._event_config = [
            {**item, 'enabled': event_enabled}
            if item['event_name'] == event_name else item
            for item in self._event_config
        ]
        self._commit_change()

    def update_status(self, event_name: str, event_enabled: str) -> None:
        self._read_config()
        self._setting_cards = [
            self._create_card(
                name=item_event['event_name'],
                tip=item_switch['tip'],
                enabled=item_event['enabled'],
                next_tick=item_event['next_tick'],
                setting_name=item_switch['config']
            )
            for item_event in self._event_config
            for item_switch in self._switch_config
            if item_event['event_name'] == item_switch['name']
        ]
        # self.basicGroup.cardLayout.wid
        self.basicGroup.addSettingCards(self._setting_cards)

    def _change_time(self, event_name: str, event_time: str) -> None:
        try:
            event_time = int(datetime.strptime(event_time, "%Y-%m-%d %H:%M:%S").timestamp())
        except ValueError as e:
            return
        self._read_config()
        self._event_config = [
            {**item, 'next_tick': event_time}
            if item['event_name'] == event_name else item
            for item in self._event_config
        ]
        self._commit_change()

    def _create_card(self, name: str, tip: str, setting_name: str, enabled: bool,
                     next_tick: str) -> TemplateSettingCard:
        _switch_card = TemplateSettingCard(
            title=name,
            content=tip,
            parent=self.basicGroup,
            sub_view=expand.__dict__[setting_name] if setting_name else None
        )
        _switch_card.status_switch.setChecked(enabled)
        _switch_card.statusChanged.connect(
            lambda x: self._change_status(name, x)
        )
        _switch_card.timeChanged.connect(
            lambda x: self._change_time(name, x)
        )
        _switch_card.timer_box.setText(datetime.fromtimestamp(float(next_tick)).strftime("%Y-%m-%d %H:%M:%S"))
        return _switch_card

    def _commit_change(self):
        with lock:
            with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._event_config, f, ensure_ascii=False, indent=2)

    def _read_config(self):
        with lock:
            with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)
            with open(SWITCH_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self._switch_config = json.load(f)

    def update_settings(self):
        if self.basicGroup is not None:
            self.basicGroup.deleteLater()
        self.basicGroup = SettingCardGroup(
            self.tr("功能开关"), self.scrollWidget)
        self.basicGroup.addSettingCards(self._setting_cards)
        self.expandLayout.addWidget(self.basicGroup)

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
        self.expandLayout.addWidget(self.settingLabel)
        self.update_settings()

    def __initWidget(self):
        self.setWidget(self.scrollWidget)
