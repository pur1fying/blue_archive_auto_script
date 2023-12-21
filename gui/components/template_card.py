# coding:utf-8

from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import ExpandSettingCard, SwitchButton, \
    IndicatorPosition, LineEdit
from qfluentwidgets import FluentIcon as FIF


class TemplateSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    # statusChanged = pyqtSignal(bool)
    # timeChanged = pyqtSignal(str)

    def __init__(self, title: str = '', content: str = None, parent=None, sub_view=None):
        super().__init__(FIF.CHECKBOX, title, content, parent)
        # Card Top Widgets
        # self.status_switch = SwitchButton(self.tr('Off'), self, IndicatorPosition.RIGHT)
        # self.timer_box = LineEdit(self)
        # self.timer_box.setFixedWidth(160)
        # 暂时关闭调度功能
        # self.timer_box.setVisible(False)
        if sub_view is not None:
            self.expand_view = sub_view.Layout(self)
        else:
            self.expand_view = None

        # self.status_switch.checkedChanged.connect(self.statusChanged.emit)
        # self.timer_box.textChanged.connect(self.timeChanged.emit)

        self._adjustViewSize()
        self.__initWidget()

    def __initWidget(self):
        # Add widgets to layout
        # self.addWidget(self.timer_box)
        # self.addWidget(self.status_switch)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        # Initialize layout
        if self.expand_view is not None:
            self.viewLayout.addWidget(self.expand_view)
            self.expand_view.show()
        else:
            self.setExpand(False)
            self.card.expandButton.hide()
            self.card.setContentsMargins(0, 0, 30, 0)
        self._adjustViewSize()

    def setChecked(self, isChecked: bool):
        self.setValue(isChecked)


class SimpleSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    def __init__(self, sub_view, title: str = '', content: str = None, parent=None):
        super().__init__(FIF.CHECKBOX, title, content, parent)
        self.expand_view = sub_view.Layout(self)
        self._adjustViewSize()
        self.__initWidget()

    def __initWidget(self):
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        # Initialize layout
        self.viewLayout.addWidget(self.expand_view)
        self.expand_view.show()
        self._adjustViewSize()
