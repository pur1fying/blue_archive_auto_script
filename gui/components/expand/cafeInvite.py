from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from qfluentwidgets import ComboBox, LineEdit


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.hBoxLayout = QVBoxLayout(self)
        self.lay1 = QHBoxLayout(self)
        self.lay2 = QHBoxLayout(self)
        self.lay3 = QHBoxLayout(self)
        self.pat_styles = ['普通', '地毯', '拖动礼物']
        self.student_name = []
        if self.config.server_mode == 0:
            for i in range(0, len(self.config.static_config['CN_student_name'])):
                self.student_name.append(self.config.static_config['CN_student_name'][i])
        if self.config.server_mode == 1:
            for i in range(0, len(self.config.static_config['Global_student_name'])):
                self.student_name.append(self.config.static_config['Global_student_name'][i])
        self.label1 = QLabel('选择你要添加邀请的学生：', self)
        self.input1 = ComboBox(self)
        self.input = LineEdit(self)
        self.input.setFixedWidth(650)
        self.ac_btn = QPushButton('确定', self)

        self.favor_student = self.config.get('favorStudent1')
        self.input1.addItems(self.student_name)
        # self.input1.setText(','.join(self.favor_student))
        student_list = []
        for fav in self.favor_student:
            if fav in self.student_name:
                student_list.append(fav)
        if len(student_list) == 0:
            self.input1.setCurrentIndex(0)
            student_list.append(self.student_name[0])
        self.config.set('favorStudent1', student_list)
        self.input.setText(','.join(student_list))
        self.input1.currentTextChanged.connect(self.__accept)
        self.input1.customContextMenuRequested.connect(
            self.__accept
        )

        self.label2 = QLabel('选择摸头方式：', self)
        self.input2 = ComboBox(self)
        self.pat_style = self.config.get('patStyle') or '普通'
        self.input2.addItems(self.pat_styles)
        self.input2.setText(self.pat_style)
        self.input2.setCurrentIndex(self.pat_styles.index(self.pat_style))
        self.input2.currentTextChanged.connect(self.__accept)

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

        self.lay3.setContentsMargins(10, 0, 0, 0)
        self.lay3.addWidget(self.input, 0, Qt.AlignLeft)
        self.lay3.addWidget(self.ac_btn, 20, Qt.AlignRight)
        self.lay3.addSpacing(16)
        self.lay3.addStretch(1)
        self.lay3.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay3)
        self.hBoxLayout.addLayout(self.lay2)

    def __accept(self):
        self.favor_student = self.input1.text()
        print(self.pat_style)
        self.pat_style = self.input2.text()
        self.config.set('favorStudent1', [self.favor_student])
        self.config.set('patStyle', self.pat_style)
        print(self.favor_student)
        print(self.pat_style)
