# coding:utf-8
import json

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel)
from qfluentwidgets import ExpandSettingCard, ConfigItem, PushButton, qconfig, FlowLayout, CheckBox, SwitchButton, \
    IndicatorPosition, LineEdit
from qfluentwidgets import FluentIcon as FIF


class BasicSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    statusChanged = pyqtSignal(bool)
    timeChanged = pyqtSignal(str)

    def __init__(self, config_item: ConfigItem, title: str, content: str = None, parent=None):
        super().__init__(FIF.CHECKBOX, title, content, parent)

        # Constants Definition
        self.EXTEND_CONFIG_PATH = './gui/config/extend.json'
        self.DISPLAY_CONFIG_PATH = './gui/config/display.json'
        self.EVENT_CONFIG_PATH = './core/event.json'
        # Card Top Widgets
        self.status_switch = SwitchButton(self.tr('Off'), self, IndicatorPosition.RIGHT)
        self.timer_box = LineEdit(self)

        # self.hBoxLayout = FlowLayout(self, needAni=True)
        # self.setFixedSize(720, 200)
        #
        # self.config_name = config_name
        # self.configItem = configItem
        # self.switch_item = PushButton(self.tr('设置目录'),
        #                               self, FIF.FOLDER_ADD)
        # self.hBoxLayout.addWidget(self.status_switch, 0, Qt.AlignRight)
        # self.hBoxLayout.addSpacing(16)

        self.__initWidget()

    def __initWidget(self):
        # Add widgets to layout
        self.addWidget(self.status_switch)
        self.addWidget(self.timer_box)

        # Initialize layout
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        # self.item = GoodsItem(self.file, self.view)

        for box in self.item.boxes:
            box.stateChanged.connect(self.__onStateChanged)

        self.viewLayout.addWidget(self.item)
        self.item.show()
        self._adjustViewSize()
