from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from qfluentwidgets import ComboBox, LineEdit, CheckBox


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.hBoxLayout = QVBoxLayout(self)
        self.lay1 = QHBoxLayout(self)
        self.lay2 = QHBoxLayout(self)
        self.lay2_ = QHBoxLayout(self)
        self.lay3 = QHBoxLayout(self)
        self.lay3_ = QHBoxLayout(self)
        self.lay4 = QHBoxLayout(self)
        self.lay5 = QHBoxLayout(self)
        self.lay6 = QHBoxLayout(self)

        self.label_1 = QLabel('是否要领取奖励:', self)
        self.income_switch = CheckBox(self)
        self.income_switch.setChecked(self.config.get('cafe_reward_collect_hour_reward'))
        self.income_switch.stateChanged.connect(lambda: self.config.set('cafe_reward_collect_hour_reward',
                                                                        self.income_switch.isChecked()))
        self.lay4.addWidget(self.label_1, 20, Qt.AlignLeft)
        self.lay4.addWidget(self.income_switch, 0, Qt.AlignRight)

        self.label_2 = QLabel('是否使用邀请券:', self)
        self.invite_switch = CheckBox(self)
        self.invite_switch.setChecked(self.config.get('cafe_reward_use_invitation_ticket'))
        self.invite_switch.stateChanged.connect(lambda: self.config.set('cafe_reward_use_invitation_ticket',
                                                                        self.invite_switch.isChecked()))
        self.lay5.addWidget(self.label_2, 20, Qt.AlignLeft)
        self.lay5.addWidget(self.invite_switch, 0, Qt.AlignRight)

        if self.config.server_mode == 'JP':
            self.label_3 = QLabel('是否有二号咖啡厅:', self)
            self.second_switch = CheckBox(self)
            self.second_switch.setChecked(self.config.get('cafe_reward_has_no2_cafe'))
            self.second_switch.stateChanged.connect(lambda: self.config.set('cafe_reward_has_no2_cafe',
                                                                            self.invite_switch.isChecked()))
            self.lay6.addWidget(self.label_3, 20, Qt.AlignLeft)
            self.lay6.addWidget(self.second_switch, 0, Qt.AlignRight)

        self.pat_styles = ['普通', '地毯', '拖动礼物']
        self.student_name = []

        self.label1 = QLabel('列表选择你要添加邀请的学生，修改后请点击确定：', self)
        for i in range(0, len(self.config.static_config['student_names'])):
            if self.config.static_config['student_names'][i][self.config.server_mode + '_implementation']:
                self.student_name.append(
                    self.config.static_config['student_names'][i][self.config.server_mode + '_name'])
        self.input1 = ComboBox(self)
        self.input = LineEdit(self)
        self.input.setFixedWidth(650)
        self.ac_btn = QPushButton('确定', self)

        self.favor_student1 = self.config.get('favorStudent1')
        self.input1.addItems(self.student_name)
        # self.input1.setText(','.join(self.favor_student))
        self.favor_student1 = self.check_valid_student_names()
        self.config.set('favorStudent1', self.favor_student1)
        self.input.setText(','.join(self.favor_student1))

        if self.config.server_mode == 'JP':
            self.student_name_ = []
            self.label4 = QLabel('如果有第二咖啡厅，选择你需要邀请的学生', self)
            for i in range(0, len(self.config.static_config['student_names'])):
                if self.config.static_config['student_names'][i][self.config.server_mode + '_implementation']:
                    self.student_name_.append(
                        self.config.static_config['student_names'][i][self.config.server_mode + '_name'])
            self.input4 = ComboBox(self)
            self.input_ = LineEdit(self)
            self.input_.setFixedWidth(650)
            self.ac_btn_ = QPushButton('确定', self)

            self.favor_student2 = self.config.get('favorStudent2')
            self.input4.addItems(self.student_name)
            self.favor_student2 = self.check_valid_student_names_()
            self.config.set('favorStudent2', self.favor_student2)
            self.input_.setText(','.join(self.favor_student2))

        self.label2 = QLabel('选择摸头方式：', self)
        self.input2 = ComboBox(self)
        self.pat_style = self.config.get('patStyle') or '普通'
        self.input2.addItems(self.pat_styles)
        self.input2.setText(self.pat_style)
        self.input2.setCurrentIndex(self.pat_styles.index(self.pat_style))

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

        self.lay4.setContentsMargins(10, 0, 0, 0)
        self.lay4.addSpacing(16)
        self.lay4.addStretch(1)
        self.lay4.setAlignment(Qt.AlignCenter)

        self.lay5.setContentsMargins(10, 0, 0, 0)
        self.lay5.addSpacing(16)
        self.lay5.addStretch(1)
        self.lay5.setAlignment(Qt.AlignCenter)

        if self.config.server_mode == 'JP':
            self.lay6.setContentsMargins(10, 0, 0, 0)
            self.lay6.addSpacing(16)
            self.lay6.addStretch(1)
            self.lay6.setAlignment(Qt.AlignCenter)

            self.lay2_.setContentsMargins(10, 0, 0, 0)
            self.lay2_.addWidget(self.label4, 20, Qt.AlignLeft)
            self.lay2_.addWidget(self.input4, 0, Qt.AlignRight)
            self.lay2_.addSpacing(16)
            self.lay2_.addStretch(1)
            self.lay2_.setAlignment(Qt.AlignCenter)

            self.lay3_.setContentsMargins(10, 0, 0, 0)
            self.lay3_.addWidget(self.input_, 0, Qt.AlignLeft)
            self.lay3_.addWidget(self.ac_btn_, 20, Qt.AlignRight)
            self.lay3_.addSpacing(16)
            self.lay3_.addStretch(1)
            self.lay3_.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay4)
        self.hBoxLayout.addLayout(self.lay5)
        if self.config.server_mode == 'JP':
            self.hBoxLayout.addLayout(self.lay6)
        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay3)
        if self.config.server_mode == 'JP':
            self.hBoxLayout.addLayout(self.lay2_)
            self.hBoxLayout.addLayout(self.lay3_)
        self.hBoxLayout.addLayout(self.lay2)
        self.__init_Signals_and_Slots()

    def __add_student_name_in_the_last(self):
        self.favor_student1.append(self.input1.currentText())
        self.favor_student1 = self.check_valid_student_names()
        self.config.set('favorStudent1', self.favor_student1)
        self.input.setText(','.join(self.favor_student1))

    def __add_student_name_in_the_last_second(self):
        self.favor_student2.append(self.input4.currentText())
        self.favor_student2 = self.check_valid_student_names_()
        self.config.set('favorStudent2', self.favor_student2)
        self.input_.setText(','.join(self.favor_student2))

    def __accept_pat_style(self):
        self.pat_style = self.input2.text()
        self.config.set('patStyle', self.pat_style)

    def __student_name_change_by_keyboard_input(self):
        text = self.input.text()
        self.favor_student1 = text.split(',')
        self.config.set('favorStudent1', self.favor_student1)
        print(self.favor_student1)

    def __student_name_change_by_keyboard_input_(self):
        text = self.input_.text()
        self.favor_student2 = text.split(',')
        self.config.set('favorStudent2', self.favor_student2)

    def __init_Signals_and_Slots(self):
        self.input2.currentTextChanged.connect(self.__accept_pat_style)
        self.input1.currentTextChanged.connect(self.__add_student_name_in_the_last)
        self.ac_btn.clicked.connect(self.__student_name_change_by_keyboard_input)
        if self.config.server_mode == 'JP':
            self.input4.currentTextChanged.connect(self.__add_student_name_in_the_last_second)
            self.ac_btn_.clicked.connect(self.__student_name_change_by_keyboard_input_)

    def check_valid_student_names(self):
        temp = []
        appeared_names = []
        for fav in self.favor_student1:
            if fav in self.student_name and (fav not in appeared_names):
                temp.append(fav)
                appeared_names.append(fav)
        return temp

    def check_valid_student_names_(self):
        temp = []
        appeared_names = []
        for fav in self.favor_student2:
            if fav in self.student_name and (fav not in appeared_names):
                temp.append(fav)
                appeared_names.append(fav)
        return temp
