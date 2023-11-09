from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, ComboBox

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.info_widget = self.parent()
        self.hBoxLayout = QHBoxLayout(self)
        # self.label = QLabel('输入最高难度', self)
        self.label = QLabel('输入最高难度(功能开发中,先别用)', self)
        self.input = ComboBox(self)

        self.input.addItems(['NORMAL', 'HARD', 'VERYHARD', 'HARDCORE', 'EXTREME'])
        self.input.currentIndexChanged.connect(self.__accept)

        self.setFixedHeight(53)
        self.hBoxLayout.setContentsMargins(48, 0, 0, 0)

        self.hBoxLayout.addWidget(self.label, 20, Qt.AlignLeft)
        self.hBoxLayout.addWidget(self.input, 0, Qt.AlignRight)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

    def __accept(self):
        self.set('totalForceFightDifficulty', self.input.text())
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的总力战最高难度已经被设置为：{self.input.text()}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()
