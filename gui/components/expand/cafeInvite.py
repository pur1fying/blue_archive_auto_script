from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from qfluentwidgets import ComboBox, LineEdit, CheckBox


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.setFixedHeight(425)
        self.config = config
        self.hBoxLayout = QVBoxLayout(self)
        self.lay1 = QHBoxLayout(self)       # ComboBox 选择第一咖啡厅学生名字
        self.lay2 = QHBoxLayout(self)       # 摸头方式
        self.lay2_ = QHBoxLayout(self)      # ComboBox 选择第二咖啡厅学生名字
        self.lay3 = QHBoxLayout(self)       # 第一咖啡厅邀请学生名字
        self.lay3_ = QHBoxLayout(self)      # 第二咖啡厅邀请学生名字
        self.lay6 = QHBoxLayout(self)       # 是否有二号咖啡厅

        self.layCollectReward = self.labeledCheckBoxTemplate('是否领取奖励:', 'cafe_reward_collect_hour_reward')
        self.layUseInvitationTicket = self.labeledCheckBoxTemplate('是否使用邀请券:', 'cafe_reward_use_invitation_ticket')
        self.layInviteLowestAffection = self.labeledCheckBoxTemplate('优先邀请券好感等级低的学生:', 'cafe_reward_lowest_affection_first')
        self.layEnableExchangeStudent = self.labeledCheckBoxTemplate('是否允许学生更换服饰:', 'cafe_reward_allow_exchange_student')


        if self.config.server_mode == 'JP' or self.config.server_mode == 'Global':

            self.label_3 = QLabel('是否有二号咖啡厅:', self)
            self.second_switch = CheckBox(self)
            self.second_switch.setChecked(self.config.get('cafe_reward_has_no2_cafe'))

            self.lay6.addWidget(self.label_3, 1, Qt.AlignLeft)
            self.lay6.addWidget(self.second_switch, 0, Qt.AlignRight)
            self.layEnableDuplicateInvite = self.labeledCheckBoxTemplate('是否允许重复邀请:', 'cafe_reward_allow_duplicate_invite')

        self.pat_styles = ['拖动礼物']
        self.student_name = []

        self.label1 = QLabel('列表选择你要添加邀请的学生，修改后请点击确定：', self)
        for i in range(0, len(self.config.static_config['student_names'])):
            if self.config.static_config['student_names'][i][self.config.server_mode + '_implementation']:
                self.student_name.append(
                    self.config.static_config['student_names'][i][self.config.server_mode + '_name'])
        self.input1 = ComboBox(self)
        self.input1.addItem("添加学生")
        self.input = LineEdit(self)
        self.input.setFixedWidth(650)
        self.ac_btn = QPushButton('确定', self)

        self.favor_student1 = self.config.get('favorStudent1')
        self.input1.addItems(self.student_name)
        self.favor_student1 = self.check_valid_student_names()
        self.config.set('favorStudent1', self.favor_student1)
        self.input.setText(','.join(self.favor_student1))

        self.label2 = QLabel('选择摸头方式：', self)
        self.input2 = ComboBox(self)

        self.pat_style = self.config.get('patStyle') or '普通'
        self.input2.addItems(self.pat_styles)
        self.input2.setText(self.pat_style)
        self.input2.setCurrentIndex(self.pat_styles.index(self.pat_style))

        self.lay1.addWidget(self.label1, 1, Qt.AlignLeft)
        self.lay1.addWidget(self.input1, 0, Qt.AlignRight)

        self.lay2.addWidget(self.label2, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.input2, 0, Qt.AlignRight)

        self.lay3.addWidget(self.input, 1, Qt.AlignLeft)
        self.lay3.addWidget(self.ac_btn, 0, Qt.AlignRight)

        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addLayout(self.layCollectReward)
        self.hBoxLayout.addLayout(self.layUseInvitationTicket)
        self.hBoxLayout.addLayout(self.layInviteLowestAffection)
        self.hBoxLayout.addLayout(self.layEnableExchangeStudent)
        if self.config.server_mode == 'JP' or self.config.server_mode == 'Global':
            self.hBoxLayout.addLayout(self.layEnableDuplicateInvite)
        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay3)
        self.hBoxLayout.addLayout(self.lay2)
        self.hBoxLayout.setContentsMargins(20, 0, 20, 10)
        if self.config.server_mode == 'JP' or self.config.server_mode == 'Global':
            self.hBoxLayout.addLayout(self.lay6)
            if self.config.get('cafe_reward_has_no2_cafe'):
                self.set_buttons_for_no2_cafe()

        self.__init_Signals_and_Slots()

    def __add_student_name_in_the_last(self):
        if self.input1.currentText() == '添加学生':
            return
        self.favor_student1.append(self.input1.currentText())
        self.favor_student1 = self.check_valid_student_names()
        self.config.set('favorStudent1', self.favor_student1)
        self.input.setText(','.join(self.favor_student1))

    def __add_student_name_in_the_last_second(self):
        if self.input4.currentText() == '添加学生':
            return
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

    def __student_name_change_by_keyboard_input_(self):
        text = self.input_.text()
        self.favor_student2 = text.split(',')
        self.config.set('favorStudent2', self.favor_student2)

    def __init_Signals_and_Slots(self):
        self.input2.currentTextChanged.connect(self.__accept_pat_style)
        self.input1.currentTextChanged.connect(self.__add_student_name_in_the_last)
        self.ac_btn.clicked.connect(self.__student_name_change_by_keyboard_input)
        if self.config.server_mode == 'JP' or self.config.server_mode == 'Global':
            self.second_switch.stateChanged.connect(self.Slot_for_no_2_cafe_Checkbox)

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

    def Slot_for_no_2_cafe_Checkbox(self, state):
        self.config.set('cafe_reward_has_no2_cafe', state == Qt.Checked)
        if state == Qt.Checked:
            self.set_buttons_for_no2_cafe()
        else:
            sub_layout = self.hBoxLayout.itemAt(10)
            self.hBoxLayout.removeItem(sub_layout)
            while sub_layout.count():
                item = sub_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout.removeItem(item)
            sub_layout = self.hBoxLayout.itemAt(10)
            self.hBoxLayout.removeItem(sub_layout)
            while sub_layout.count():
                item = sub_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout.removeItem(item)

    def set_buttons_for_no2_cafe(self):
        self.label4 = QLabel('选择第二咖啡厅邀请的学生', self)
        self.input4 = ComboBox(self)
        self.input4.addItem("添加学生")
        self.input_ = LineEdit(self)
        self.input_.setFixedWidth(650)
        self.ac_btn_ = QPushButton('确定', self)
        self.favor_student2 = self.config.get('favorStudent2')
        self.input4.addItems(self.student_name)
        self.favor_student2 = self.check_valid_student_names_()
        self.config.set('favorStudent2', self.favor_student2)
        self.input_.setText(','.join(self.favor_student2))
        self.lay2_.addWidget(self.label4, 1, Qt.AlignLeft)
        self.lay2_.addWidget(self.input4, 0, Qt.AlignRight)

        self.lay3_.addWidget(self.input_, 1, Qt.AlignLeft)
        self.lay3_.addWidget(self.ac_btn_, 0, Qt.AlignRight)

        self.hBoxLayout.addLayout(self.lay2_)
        self.hBoxLayout.addLayout(self.lay3_)

        self.input4.currentTextChanged.connect(self.__add_student_name_in_the_last_second)
        self.ac_btn_.clicked.connect(self.__student_name_change_by_keyboard_input_)

    def labeledCheckBoxTemplate(self, label, config_name):
        lay = QHBoxLayout(self)
        label = QLabel(label, self)
        checkBox = CheckBox(self)
        checkBox.setChecked(self.config.get(config_name))
        lay.addWidget(label, 20, Qt.AlignLeft)
        lay.addWidget(checkBox, 0, Qt.AlignRight)
        checkBox.stateChanged.connect(lambda: self.config.set(config_name, checkBox.isChecked()))
        return lay
