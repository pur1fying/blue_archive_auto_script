from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import ComboBox

from gui.util import notification


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.info_widget = self.parent()
        self.hBoxLayout = QHBoxLayout(self)
        # self.label = QLabel('输入最高难度', self)
        self.label = QLabel('最高难度', self)
        self.input = ComboBox(self)
        self.difficulties = self.config.static_config['total_assault_difficulties'][self.config.server_mode]
        self.input.addItems(self.difficulties)
        if self.config.get('totalForceFightDifficulty') not in self.difficulties:
            self.config.set('totalForceFightDifficulty', self.difficulties[0])
        self.input.setText(self.config.get('totalForceFightDifficulty'))
        self.input.currentIndexChanged.connect(self.__accept)

        self.setFixedHeight(53)
        self.hBoxLayout.setContentsMargins(48, 0, 0, 0)

        self.hBoxLayout.addWidget(self.label, 20, Qt.AlignLeft)
        self.hBoxLayout.addWidget(self.input, 0, Qt.AlignRight)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

    def __accept(self):
        self.config.set('totalForceFightDifficulty', self.input.text())
        notification.success('设置成功', f'你的总力战最高难度已经被设置为：{self.input.text()}', self.config)
