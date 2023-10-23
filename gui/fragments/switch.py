import json
import threading

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel)
from qfluentwidgets import FluentIcon as FIF, SettingCardGroup, SwitchSettingCard

EVENT_CONFIG_PATH = './config/event.json'
SWITCH_CONFIG_PATH = './config/switch.json'

lock = threading.Lock()

class SwitchFragment(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.tr("调度设置"), self.scrollWidget)

        self.basicGroup = SettingCardGroup(
            self.tr("功能开关"), self.scrollWidget)

        self._setting_cards = []
        self._event_config, self._switch_config = [], []
        self._read_config()

        self._setting_cards = [
            self._create_card(
                item_event['event_name'],
                item_switch['tip'],
                item_event['enabled']
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

    def _create_card(self, name: str, tip: str, enabled: bool) -> SwitchSettingCard:
        _switch_card = SwitchSettingCard(
            FIF.CHECKBOX, name, tip,
            parent=self.basicGroup
        )
        _switch_card.setChecked(enabled)
        _switch_card.checkedChanged.connect(
            lambda x: self._change_status(name, x)
        )
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

        self.basicGroup.addSettingCards(self._setting_cards)

        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)

    def __initWidget(self):
        self.setWidget(self.scrollWidget)
