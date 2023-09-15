# coding:utf-8

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QFileDialog, QWidget, QLabel,
                             QHBoxLayout)
from qfluentwidgets import ExpandSettingCard, ConfigItem, PushButton, qconfig
from qfluentwidgets import FluentIcon as FIF


class FolderItem(QWidget):
    """ Folder item """

    removed = pyqtSignal(QWidget)

    def __init__(self, file: str, parent=None):
        super().__init__(parent=parent)
        self.folder = file
        self.hBoxLayout = QHBoxLayout(self)
        self.folderLabel = QLabel(file, self)

        self.setFixedHeight(53)
        self.hBoxLayout.setContentsMargins(48, 0, 60, 0)
        self.hBoxLayout.addWidget(self.folderLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)


class FileSelectSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    folderChanged = pyqtSignal(str)

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, filePath="", parent=None):
        """
        Parameters
        ----------
        configItem: RangeConfigItem
            configuration item operated by the card

        title: str
            the title of card

        content: str
            the content of card

        filePath: str
            working directory of file dialog

        parent: QWidget
            parent widget
        """
        super().__init__(FIF.FOLDER, title, content, parent)
        self.configItem = configItem
        self._dialogDirectory = filePath
        self.addFolderButton = PushButton(self.tr('设置目录'), self, FIF.FOLDER_ADD)

        self.file = qconfig.get(configItem)  # type:str
        self.__initWidget()

    def __initWidget(self):
        self.addWidget(self.addFolderButton)

        # initialize layout
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.item = FolderItem(self.file, self.view)
        self.viewLayout.addWidget(self.item)
        self.item.show()
        self._adjustViewSize()

        self.addFolderButton.clicked.connect(self.__showFolderDialog)

    def __showFolderDialog(self):
        """ show folder dialog """
        folder = QFileDialog.getOpenFileName(
            self, self.tr("选择模拟器路径"), self._dialogDirectory, '*.exe')[0]
        if folder == "":
            return
        self.__setFileItem(folder)
        qconfig.set(self.configItem, self.file)

    def __setFileItem(self, file: str):
        """ add folder item """
        self.file = file
        self.__removeFolder()
        self.item = FolderItem(self.file, self.view)
        self.viewLayout.addWidget(self.item)
        self.item.show()
        self._adjustViewSize()

    def __removeFolder(self):
        """ remove folder """
        self.viewLayout.removeWidget(self.item)
        self.item.deleteLater()
        self._adjustViewSize()
