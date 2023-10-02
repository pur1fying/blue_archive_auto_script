# coding:utf-8

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout)
from qfluentwidgets import ExpandSettingCard, ConfigItem, qconfig, ComboBox, LineEdit
from qfluentwidgets import FluentIcon as FIF


class ServerItem(QWidget):
    """ Folder item """

    removed = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.folderLabel = QLabel('请选择您的服务器', self)
        self.serverLabel = QLabel('请填写您的adb端口号', self)
        stops = ['官服', 'B服']
        self.portBox = LineEdit(self)
        self.combo = ComboBox(self)
        self.combo.addItems(stops)
        self.setFixedHeight(120)
        self.combo.setCurrentIndex(0)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(48, 0, 60, 0)

        self.lay1 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay2 = QHBoxLayout(self.vBoxLayout.widget())

        self.lay1.addWidget(self.folderLabel, 17, Qt.AlignLeft)
        self.lay1.addWidget(self.combo, 0, Qt.AlignRight)
        self.lay1.setAlignment(Qt.AlignVCenter)

        self.lay2.addWidget(self.serverLabel, 17, Qt.AlignLeft)
        self.lay2.addWidget(self.portBox, 0, Qt.AlignRight)
        self.lay2.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addLayout(self.lay1)
        self.vBoxLayout.addLayout(self.lay2)


class ServerSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    folderChanged = pyqtSignal(list)

    def __init__(self, configServer: ConfigItem, configPort: ConfigItem, title: str, content: str = None, stop=None,
                 parent=None):
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
        self.stop = stop
        self.configServer = configServer
        self.configPort = configPort
        self.server = qconfig.get(configServer)  # type:str
        self.port = qconfig.get(configPort)
        self.__initWidget()

    def __initWidget(self):
        # initialize layout
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.item = ServerItem(self.view)

        self.item.combo.currentIndexChanged.connect(self.__onStateChanged)
        self.item.portBox.textChanged.connect(self.__onTextChanged)
        self.viewLayout.addWidget(self.item)
        self.item.show()
        self._adjustViewSize()

    def __onStateChanged(self, _state):
        self.server = self.item.combo.currentText()
        qconfig.set(self.configServer, self.server)

    def __onTextChanged(self):
        self.port = self.item.portBox.text()
        qconfig.set(self.configPort, self.port)
