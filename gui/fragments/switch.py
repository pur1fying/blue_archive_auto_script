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
    """
    A class that manages switch-related settings in a scrollable interface.
    """

    CARD2COMP = {
        "Card": TemplateSettingCardForClick,
        "List": TemplateSettingCard
    }

    def __init__(self, parent=None, config=None):
        """
        Initializes the SwitchFragment.

        Args:
            parent: The parent widget.
            config: Configuration object for settings injection.
        """
        super().__init__(parent=parent)
        self.flowLayout = None
        self.config = config

        # Create a QWidget instance to serve as the content of the scroll area.
        self.scrollWidget = QWidget()

        # Create an ExpandLayout instance for managing the scroll area's layout.
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # Create a TitleLabel instance with the title "Scheduler Settings".
        self.settingLabel = TitleLabel(self.scrollWidget)
        config.inject(self.settingLabel, self.tr("Configuration Settings") + " {name}")
        self.configLoadType = configGui.configDisplayType.value

        # Initialize variables for the basic group and setting cards.
        self.basicGroup = None
        self._setting_cards = []
        self._event_config, self._switch_config = [], []

        # Read configuration files to populate the event and switch settings.
        self._read_config()

        # Use a timer to lazily load settings after 500ms to avoid UI lag.
        QTimer.singleShot(500, self._lazy_load)

        # Generate a unique object name for the instance.
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(self.object_name)

    def _lazy_load(self):
        """
        Lazily loads setting cards based on the switch and event configuration.
        """
        self._setting_cards = [
            self._create_card(
                name=item_event['name'],
                tip=item_event['tip'],
                setting_name=item_event['config']
            )
            for item_event in self._switch_config
        ]

        self.__initLayout()
        self.__initWidget()

    def _change_time(self, event_name: str, event_time: str) -> None:
        """
        Updates the next execution time for a specific event.

        Args:
            event_name: The name of the event to update.
            event_time: The new execution time in the format 'YYYY-MM-DD HH:MM:SS'.
        """
        try:
            event_time = int(datetime.strptime(event_time, "%Y-%m-%d %H:%M:%S").timestamp())
        except ValueError:
            return
        self._read_config()

        # Update the 'next_tick' value for the specified event.
        self._event_config = [
            {**item, 'next_tick': event_time}
            if item['event_name'] == event_name else item
            for item in self._event_config
        ]
        self._commit_change()

    def _create_card(self, name: str, tip: str, setting_name: str) -> Union[
        TemplateSettingCard, TemplateSettingCardForClick]:
        """
        Creates a setting card based on the provided parameters.

        Args:
            name: The title of the setting card.
            tip: A description or tooltip for the setting card.
            setting_name: The configuration name associated with the card.

        Returns:
            A TemplateSettingCard or TemplateSettingCardForClick instance.
        """
        Component = self.CARD2COMP[self.configLoadType]
        _switch_card = Component(
            title=name,
            content=tip,
            parent=self.basicGroup,
            sub_view=expand.__dict__[setting_name] if setting_name else None,
            config=self.config,
            context='ConfigTranslation',
            setting_name=setting_name
        )
        return _switch_card

    def _commit_change(self):
        """
        Commits changes to the event configuration by saving them to a file.
        """
        with lock:
            with open(self.config.config_dir + '/event.json', 'w', encoding='utf-8') as f:
                json.dump(self._event_config, f, ensure_ascii=False, indent=2)

    def _read_config(self):
        """
        Reads event and switch configurations from their respective files.
        """
        with lock:
            with open(self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)
            with open(self.config.config_dir + '/switch.json', 'r', encoding='utf-8') as f:
                self._switch_config = json.load(f)

    def update_settings(self):
        """
        Updates the displayed settings based on the current configuration type.
        """
        if self.configLoadType == 'List':
            if self.basicGroup is not None:
                self.basicGroup.deleteLater()

            self.basicGroup = SettingCardGroup(self.tr("Features"),
                                               self.scrollWidget)
            self.basicGroup.vBoxLayout.insertSpacing(1, -10)
            self.basicGroup.titleLabel.deleteLater()
            self.basicGroup.addSettingCards(self._setting_cards)
            self.expandLayout.addWidget(self.basicGroup)
        else:
            wrapper_widget = QWidget(self.scrollWidget)
            self.flowLayout = FlowLayout(wrapper_widget, needAni=True)
            self.flowLayout.setSpacing(10)
            self.flowLayout.setAlignment(Qt.AlignTop)
            for card in self._setting_cards:
                self.flowLayout.addWidget(card)

            wrapper_widget.setFixedHeight(150 * 4 + 50)
            self.expandLayout.addWidget(wrapper_widget)

    def __initLayout(self):
        """
        Initializes the layout for the scrollable content.
        """
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
        """
        Sets the scrollable widget for the scroll area.
        """
        self.setWidget(self.scrollWidget)
