from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from qfluentwidgets import ComboBox

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None, config_dir: str = 'config.json'):
        super().__init__(parent=parent)
        ConfigSet.__init__(self, config_dir)
        self.hBoxLayout = QVBoxLayout(self)
        self.lay1 = QHBoxLayout(self)
        self.lay2 = QHBoxLayout(self)
        self.pat_styles = ['普通', '地毯', '拖动礼物']
        self.student_name = []
        for i in range(0,len(self.static_config['CN_student_name'])):
            self.student_name.append(self.static_config['CN_student_name'][i])
        for i in range(0,len(self.static_config['Global_student_name'])):
            self.student_name.append(self.static_config['Global_student_name'][i])
        self.label1 = QLabel('选择你要邀请的学生(国际服选英文)：', self)
        self.input1 = ComboBox(self)
        self.favor_student = self.get('favorStudent')
        self.input1.addItems(self.student_name)
        self.input1.setText(','.join(self.favor_student))
        self.input1.setCurrentIndex(self.student_name.index(self.favor_student[0]))
        self.input1.currentTextChanged.connect(self.__accept)

        self.label2 = QLabel('选择摸头方式：', self)
        self.input2 = ComboBox(self)
        self.pat_style = self.get('patStyle') or '普通'
        self.input2.addItems(self.pat_styles)
        self.input2.setText(self.pat_style)
        self.input2.setCurrentIndex(self.pat_styles.index(self.pat_style))
        self.input2.currentTextChanged.connect(self.__accept)

        self.setFixedHeight(106)
        self.lay1.setContentsMargins(10, 0, 0, 0)
        self.lay1.addWidget(self.label1, 20, Qt.AlignLeft)
        self.lay1.addWidget(self.input1, 0, Qt.AlignRight)
        self.lay1.addSpacing(16)
        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)

        self.lay2.setContentsMargins(10, 0, 0, 0)
        self.lay2.addWidget(self.label2, 20, Qt.AlignLeft)
        self.lay2.addWidget(self.input2, 0, Qt.AlignRight)
        self.lay2.addSpacing(16)
        self.lay2.addStretch(1)
        self.lay2.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay2)

    def __accept(self):
        self.favor_student = self.input1.text()
        self.pat_style = self.input2.text()
        self.set('favorStudent', [self.favor_student])
        self.set('patStyle', self.pat_style)
        print(self.favor_student)
        print(self.pat_style)
