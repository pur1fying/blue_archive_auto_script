from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import ComboBox

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QVBoxLayout(self)

        self.lay1 = QHBoxLayout(self)

        self.option_1 = QHBoxLayout(self)
        self.option_2 = QHBoxLayout(self)
        self.option_3 = QHBoxLayout(self)

        self.label_1_0 = QLabel('高架公路', self)
        self.label_2_0 = QLabel('沙漠铁路', self)
        self.label_3_0 = QLabel('讲堂', self)

        self.input_1_2 = ComboBox(self)
        self.input_2_2 = ComboBox(self)
        self.input_3_2 = ComboBox(self)

        self.input_1_2.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.input_2_2.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.input_3_2.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])

        self.option_1.addWidget(self.label_1_0, 0, Qt.AlignLeft)
        self.option_1.addStretch(1)
        self.option_1.addWidget(self.input_1_2, 0, Qt.AlignRight)

        self.option_2.addWidget(self.label_2_0, 0, Qt.AlignLeft)
        self.option_2.addStretch(1)
        self.option_2.addWidget(self.input_2_2, 0, Qt.AlignRight)

        self.option_3.addWidget(self.label_3_0, 0, Qt.AlignLeft)
        self.option_3.addStretch(1)
        self.option_3.addWidget(self.input_3_2, 0, Qt.AlignRight)

        self.label = QLabel('请在下拉框中选择相应悬赏委托的难度和次数：', self)

        _set_main = self.get('rewarded_task_times')
        self.count = [int(x) for x in _set_main.split(',')]

        self.input_1_2.setCurrentIndex(self.count[0] - 1)
        self.input_2_2.setCurrentIndex(self.count[1] - 1)
        self.input_3_2.setCurrentIndex(self.count[2] - 1)

        self.input_1_2.currentIndexChanged.connect(self._commit)
        self.input_2_2.currentIndexChanged.connect(self._commit)
        self.input_3_2.currentIndexChanged.connect(self._commit)

        self.setFixedHeight(200)

        self.lay1.setContentsMargins(10, 0, 0, 10)
        self.option_1.setContentsMargins(10, 0, 0, 10)
        self.option_2.setContentsMargins(10, 0, 0, 10)
        self.option_3.setContentsMargins(10, 0, 0, 10)

        self.lay1.addWidget(self.label, 0, Qt.AlignLeft)

        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.option_1)
        self.hBoxLayout.addLayout(self.option_2)
        self.hBoxLayout.addLayout(self.option_3)

    def _commit(self):
        self.count[0] = self.input_1_2.currentIndex() + 1
        self.count[1] = self.input_2_2.currentIndex() + 1
        self.count[2] = self.input_3_2.currentIndex() + 1
        _formatted = ','.join([str(self.count[i]) for i in range(0, 3)])
        self.set('specialPriority', _formatted)
