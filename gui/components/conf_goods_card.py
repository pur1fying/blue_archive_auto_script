# coding:utf-8

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel)
from qfluentwidgets import ExpandSettingCard, ConfigItem, PushButton, qconfig, FlowLayout, CheckBox
from qfluentwidgets import FluentIcon as FIF


class GoodsItem(QWidget):
    """ Folder item """

    removed = pyqtSignal(QWidget)

    def __init__(self, good: list[int], parent=None):
        super().__init__(parent=parent)
        self.folder = good
        # self.hBoxLayout = QHBoxLayout(self)
        layout = FlowLayout(self, needAni=True)
        # self.setFixedHeight(90)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setVerticalSpacing(20)
        layout.setHorizontalSpacing(10)

        self.setFixedSize(720, 200)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')

        self.boxes = []
        for i in range(16):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(good[i] == 1)
            ccs = QLabel(f"商品{i + 1}", self)
            ccs.setFixedWidth(80)
            layout.addWidget(ccs)
            layout.addWidget(t_cbx)
            self.boxes.append(t_cbx)


class ItemSelectSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    folderChanged = pyqtSignal(list)

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, goodsList=None, parent=None):
        """
        Parameters
        ----------
        configItem: RangeConfigItem
            configuration item operated by the card

        title: str
            the title of card

        content: str
            the content of card

        goodsList: list[int]
            working directory of file dialog

        parent: QWidget
            parent widget
        """
        super().__init__(FIF.FOLDER, title, content, parent)
        if goodsList is None:
            goodsList = [0] * 16
        self.configItem = configItem
        self._dialogDirectory = goodsList

        self.file = qconfig.get(configItem)
        self.file = self.file.copy()  # type:list[int]
        self.__initWidget()

    def __initWidget(self):

        # initialize layout
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.item = GoodsItem(self.file, self.view)

        for box in self.item.boxes:
            box.stateChanged.connect(self.__onStateChanged)

        self.viewLayout.addWidget(self.item)
        self.item.show()
        self._adjustViewSize()

    def __onStateChanged(self, _state):
        for i, box in enumerate(self.item.boxes):
            if box.isChecked():
                self.file[i] = 1
            else:
                self.file[i] = 0
        qconfig.set(self.configItem, self.file.copy())
