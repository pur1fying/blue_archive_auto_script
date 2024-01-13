from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qfluentwidgets import LineEdit, InfoBar, InfoBarIcon, InfoBarPosition

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QVBoxLayout(self)

        self.lay1 = QHBoxLayout(self)
        self.lay2 = QHBoxLayout(self)

        self.label = QLabel('用">"分割物品，排在前面的会优先选择', self)
        self.input1 = LineEdit(self)
        self.input2 = LineEdit(self)
        self.accept = QPushButton('确定', self)

        priority = self.get('createPriority')
        time = self.get('createTime')

        self.setFixedHeight(120)
        self.input1.setText(priority)
        self.input1.setFixedWidth(600)
        self.input2.setText(time)

        self.lay1.setContentsMargins(10, 0, 0, 10)
        self.lay2.setContentsMargins(10, 0, 0, 10)

        self.accept.clicked.connect(self.__accept_main)

        self.lay1.addWidget(self.label, 0, Qt.AlignLeft)
        self.lay2.addWidget(self.input1, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.input2, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.accept, 0, Qt.AlignLeft)

        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)
        self.lay2.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay2)

    def __accept_main(self):
        input1_content = self.input1.text()
        input2_content = self.input2.text()

        self.set('createPriority', input1_content)
        self.set('createTime', input2_content)

        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'制造次数：{input2_content}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.parent().parent().parent().parent()
        )
        w.show()
