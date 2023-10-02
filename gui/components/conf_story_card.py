# coding:utf-8

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout)
from qfluentwidgets import ExpandSettingCard, ConfigItem, PushButton, qconfig, FlowLayout, CheckBox, ComboBox
from qfluentwidgets import FluentIcon as FIF


class StoryItem(QWidget):
    """ Folder item """

    removed = pyqtSignal(QWidget)

    def __init__(self, good: str, parent=None):
        super().__init__(parent=parent)
        self.folder = good
        self.hBoxLayout = QHBoxLayout(self)
        self.folderLabel = QLabel('请选择主线关卡', self)
        stops = [f'{i}-{j}' for i in range(5, 11) for j in range(1, 6)]
        self.combo = ComboBox(self)
        self.combo.addItems(stops)
        self.setFixedHeight(53)
        self.combo.setCurrentIndex(0)
        self.hBoxLayout.setContentsMargins(48, 0, 60, 0)
        self.hBoxLayout.addWidget(self.folderLabel, 17, Qt.AlignLeft)
        self.hBoxLayout.addWidget(self.combo, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)


class StorySettingCard(ExpandSettingCard):
    """ Folder list setting card """

    folderChanged = pyqtSignal(list)

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, stop=None, parent=None):
        """
        Parameters
        ----------
        configItem: RangeConfigItem
            configuration item operated by the card

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(FIF.FOLDER, title, content, parent)

        if stop is None:
            stop = '4-4'
        self.configItem = configItem
        self._dialogDirectory = stop
        self.file = qconfig.get(configItem)
        self.file = self.file  # type:str
        self.__initWidget()

    def __initWidget(self):
        # initialize layout
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.item = StoryItem(self.file, self.view)

        self.item.combo.currentIndexChanged.connect(self.__onStateChanged)

        self.viewLayout.addWidget(self.item)
        self.item.show()
        self._adjustViewSize()

    def __onStateChanged(self, _state):
        self.file = self.item.combo.currentText()
        qconfig.set(self.configItem, self.file)
