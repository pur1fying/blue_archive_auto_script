from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from qfluentwidgets import ComboBox, LineEdit,  PushButton, SwitchButton

from gui.util.translator import baasTranslator as bt


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.setFixedHeight(550)

        self.name_dict = {
            self.tr('邀请最低好感度学生'): "lowest_affection",
            self.tr('邀请最高好感度学生'): "highest_affection",
            self.tr('邀请收藏的学生'): "starred",
            self.tr('指定姓名邀请'): "name"
        }
        self.name_dict_rev = {v: k for k, v in self.name_dict.items()}

        self.mainLayout = QVBoxLayout(self)
        self._init_all_comps()

    def _init_all_comps(self):
        self.cafe_reward_invite1_criterion = self.config.get('cafe_reward_invite1_criterion')
        self.cafe_reward_invite2_criterion = self.config.get('cafe_reward_invite2_criterion')

        self.pat_styles = [bt.tr('ConfigTranslation', '拖动礼物')]
        self.student_name = []

        for student in self.config.static_config.student_names:
            if student[self.config.server_mode + '_implementation']:
                name = student[self.config.server_mode + '_name']
                self.student_name.append(name)

                # 非中文环境下，添加学生的翻译
                if not bt.isChinese():
                    cn_name = student['CN_name']
                    translated_name = name
                    bt.addStudent(cn_name, translated_name)

        self.create_cafe_mode_sel(1)

        # 初始化布局
        self.layPatStyle = QHBoxLayout()
        self.laySecondCafe = QHBoxLayout()

        # 创建复选框布局
        self.layCollectReward = self.labeled_switchBtn_template(
            self.tr('是否领取奖励:'), 'cafe_reward_collect_hour_reward')
        self.layUseInvitationTicket = self.labeled_switchBtn_template(
            self.tr('是否使用邀请券:'), 'cafe_reward_use_invitation_ticket')
        # self.layInviteLowestAffection = self.labeled_switchBtn_template(
        #     self.tr('优先邀请券好感等级低的学生:'), 'cafe_reward_lowest_affection_first')
        self.layEnableExchangeStudent = self.labeled_switchBtn_template(
            self.tr('是否允许学生更换服饰:'), 'cafe_reward_allow_exchange_student')

        self.labelSecondCafe = QLabel(self.tr('是否有二号咖啡厅:'))
        self.second_switch = SwitchButton()
        self.second_switch.setChecked(self.config.get('cafe_reward_has_no2_cafe'))
        self.laySecondCafe.addWidget(self.labelSecondCafe, 1, Qt.AlignLeft)
        self.laySecondCafe.addWidget(self.second_switch, 0, Qt.AlignRight)
        self.layEnableDuplicateInvite = self.labeled_switchBtn_template(
            self.tr('是否允许重复邀请:'), 'cafe_reward_allow_duplicate_invite')

        # 创建摸头方式选择
        self.labelPatStyle = QLabel(self.tr('选择摸头方式：'))
        self.inputPatStyle = ComboBox()
        self.pat_style = self.config.get('patStyle') or bt.tr('ConfigTranslation', '普通')
        self.inputPatStyle.addItems(self.pat_styles)
        self.inputPatStyle.setCurrentText(self.pat_style)
        self.layPatStyle.addWidget(self.labelPatStyle, 1, Qt.AlignLeft)
        self.layPatStyle.addWidget(self.inputPatStyle, 0, Qt.AlignRight)

        # 添加布局到主布局
        self.mainLayout.addSpacing(10)
        self.mainLayout.addLayout(self.layCollectReward)
        self.mainLayout.addLayout(self.layUseInvitationTicket)
        # self.mainLayout.addLayout(self.layInviteLowestAffection)
        self.mainLayout.addLayout(self.layEnableExchangeStudent)
        self.mainLayout.addLayout(self.layEnableDuplicateInvite)
        self.mainLayout.addLayout(self.layPatStyle)
        self.mainLayout.setContentsMargins(20, 0, 20, 10)
        self.mainLayout.addLayout(self.laySecondCafe)
        if self.config.get('cafe_reward_has_no2_cafe'):
            self.create_cafe_mode_sel(2)

        self.__init_Signals_and_Slots()

    def create_cafe_mode_sel(self, cafe_no):
        cur_mode = getattr(self, f"cafe_reward_invite{cafe_no}_criterion")
        mode_select_layout = QHBoxLayout()
        mode_select_label = QLabel(self.tr(f'咖啡厅 {cafe_no} 邀请券选择模式：'))
        mode_select = ComboBox()
        mode_select.addItems(self.name_dict.keys())
        mode_select.setCurrentText(self.name_dict_rev[cur_mode])
        mode_select_layout.addWidget(mode_select_label, 1, Qt.AlignLeft)
        mode_select_layout.addWidget(mode_select, 0, Qt.AlignRight)
        mode_select.currentTextChanged.connect(partial(self._alt_cafe_mode, cafe_no))
        self.mainLayout.addLayout(mode_select_layout)

        if cur_mode == 'starred':
            layout = self._init_student_com_(cafe_no)
            self.mainLayout.addLayout(layout)
        elif cur_mode == 'name':
            layouts = self._init_student_sel(cafe_no)
            for layout in layouts:
                self.mainLayout.addLayout(layout)

    def _init_student_sel(self, no):
        label = QLabel(self.tr('列表选择你要添加邀请的学生，修改后请点击确定：'))
        laySelect, layInput = QHBoxLayout(), QHBoxLayout()
        comboStudent = ComboBox()
        comboStudent.addItem(self.tr("添加学生"))
        lineEditStudent = LineEdit()
        lineEditStudent.setFixedWidth(650)
        btnConfirm = PushButton(self.tr('确定'))
        favor_student = self.config.get(f'favorStudent{no}')
        comboStudent.addItems(self.student_name)
        favor_student = self.check_valid_student_names(favor_student)
        self.config.set(f'favorStudent{no}', favor_student)
        lineEditStudent.setText(','.join(favor_student))
        laySelect.addWidget(label, 1, Qt.AlignLeft)
        laySelect.addWidget(comboStudent, 0, Qt.AlignRight)
        layInput.addWidget(lineEditStudent, 1, Qt.AlignLeft)
        layInput.addWidget(btnConfirm, 0, Qt.AlignRight)
        comboStudent.currentTextChanged.connect(
            partial(self.__add_student_name, no, lineEditStudent, comboStudent))
        btnConfirm.clicked.connect(partial(self.__student_name_changed, no, lineEditStudent))
        return [laySelect, layInput]

    def _init_student_com_(self, no):
        layout = QHBoxLayout()
        label = QLabel(self.tr('选择收藏学生的序号'))
        comboPosition = ComboBox()
        comboPosition.addItems(['1', '2', '3', '4', '5'])
        comboPosition.setCurrentText(str(self.config.get(f'cafe_reward_invite{no}_starred_student_position')))
        comboPosition.currentTextChanged.connect(
            lambda text: self.config.set(f'cafe_reward_invite{no}_starred_student_position', int(text)))
        layout.addWidget(label, 1, Qt.AlignLeft)
        layout.addWidget(comboPosition, 0, Qt.AlignRight)
        return layout

    def __add_student_name(self, no, lineEdit, comboStudent, text):
        if text == self.tr('添加学生'):
            return
        favor_student = self.config.get(f'favorStudent{no}')
        favor_student.append(text)
        favor_student = self.check_valid_student_names(favor_student)
        self.config.set(f'favorStudent{no}', favor_student)
        lineEdit.setText(','.join(favor_student))

    def __accept_pat_style(self, text):
        self.pat_style = text
        self.config.set('patStyle', self.pat_style)

    def __student_name_changed(self, no, lineEdit):
        text = lineEdit.text()
        favor_student = text.split(',')
        favor_student = self.check_valid_student_names(favor_student)
        self.config.set(f'favorStudent{no}', favor_student)
        lineEdit.setText(','.join(favor_student))

    def __init_Signals_and_Slots(self):
        self.inputPatStyle.currentTextChanged.connect(self.__accept_pat_style)
        self.second_switch.checkedChanged.connect(self.Slot_for_no_2_cafe_Checkbox)

    @staticmethod
    def check_valid_student_names(favor_student):
        temp = []
        appeared_names = set()
        for name in favor_student:
            name = name.strip()
            if name not in appeared_names:
                temp.append(name)
                appeared_names.add(name)
        return temp

    def Slot_for_no_2_cafe_Checkbox(self, state):
        self.config.set('cafe_reward_has_no2_cafe', state)
        self.reset_view()

    def labeled_switchBtn_template(self, label_text, config_name):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        switchBtn = SwitchButton()
        switchBtn.setChecked(self.config.get(config_name))
        layout.addWidget(label, 1, Qt.AlignLeft)
        layout.addWidget(switchBtn, 0, Qt.AlignRight)
        switchBtn.checkedChanged.connect(lambda state: self.config.set(config_name, state))
        return layout

    def _alt_cafe_mode(self, no, text):
        self.config.set(f'cafe_reward_invite{no}_criterion', self.name_dict[text])
        self.reset_view()

    def reset_view(self):
        self.delete_all_view()
        self._init_all_comps()

    def delete_all_view(self):
        while self.mainLayout.count():
            item = self.mainLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout is not None:
                    self.clear_layout(layout)
            del item

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self.clear_layout(sub_layout)
            del item
