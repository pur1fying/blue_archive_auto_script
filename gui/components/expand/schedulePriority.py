from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QGridLayout
from qfluentwidgets import LineEdit, PushButton

from core.utils import delay
from gui.util import notification


class StateButton(PushButton):
    """一个可切换状态的小按钮，行为类似 CheckBox"""

    def __init__(self, parent=None, checked=False):
        super().__init__(parent=parent)  # 不传 text，避免触发递归
        self.setText("")  # 手动清空
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(24, 24)
        self.update_style()
        self.toggled.connect(self.update_style)

    def update_style(self):
        if self.isChecked():
            self.setText("✔")
            self.setStyleSheet("""
                PushButton {
                    background-color: #0078d7;
                    color: white;
                    border: 1px solid #005a9e;
                    border-radius: 4px;
                }
            """)
        else:
            self.setText("")
            self.setStyleSheet("""
                PushButton {
                    background-color: white;
                    color: black;
                    border: 1px solid gray;
                    border-radius: 4px;
                }
            """)


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)

        self.config = config
        self.item_levels = ["primary", "normal", "advanced", "superior"]
        ls_names = self.config.static_config.lesson_region_name
        key = self.config.server_mode
        if self.config.server_mode == 'Global':
            key += "_en-us"
        self.lesson_names = ls_names[key]
        self.priority_list = self.config.get('lesson_times')
        self.needed_levels = self.config.get('lesson_each_region_object_priority')
        self.check_config_validation()

        self.vBoxLayout = QVBoxLayout(self)
        self.lesson_enableFavorStudent_check_box_description = QLabel(self.tr('优先做指定学生存在的日程'), self)
        # 保留顶部的 CheckBox
        from qfluentwidgets import CheckBox
        self.lesson_enableFavorStudent_check_box = CheckBox('', self)
        self.lesson_enableFavorStudent_check_box.setChecked(self.config.get('lesson_enableInviteFavorStudent'))

        self.lesson_favorStudent_LineEdit_description = QLabel(self.tr('指定学生'), self)
        self.lesson_favorStudent_LineEdit = LineEdit(self)
        self.lesson_favorStudent_LineEdit.setText('>'.join(self.config.get('lesson_favorStudent')))
        self.accept_favor_student = PushButton(self.tr('确定'), self)

        self.relationship_check_box_description = QLabel(self.tr('优先做好感等级多的日程'), self)
        self.relationship_check_box = CheckBox('', self)
        self.relationship_check_box.setChecked(self.config.get('lesson_relationship_first'))

        self.check_box_for_lesson_levels = []
        self.lesson_time_input = []
        int_validator = QIntValidator(0, 99, self)
        self.vBoxLayout.setSpacing(7)

        for i in range(len(self.lesson_names)):
            self.check_box_for_lesson_levels.append([])
            for j in range(4):
                btn = StateButton(self, checked=(self.item_levels[j] in self.needed_levels[i]))
                self.check_box_for_lesson_levels[i].append(btn)
            itm = LineEdit(self)
            itm.setFixedHeight(30)
            self.lesson_time_input.append(itm)
            self.lesson_time_input[i].setValidator(int_validator)
            self.lesson_time_input[i].setText(str(self.priority_list[i]))
            self.lesson_time_input[i].setFixedWidth(50)

        self.__init_Signals_and_Slots()
        self.__init_layouts()

    def check_config_validation(self):
        if len(self.priority_list) != len(self.lesson_names):
            self.priority_list = [1] * len(self.lesson_names)
            self.config.set('lesson_times', self.priority_list)
        if len(self.needed_levels) != len(self.lesson_names):
            temp = []
            for _ in range(len(self.lesson_names)):
                temp.append(self.item_levels)
            self.needed_levels = temp
            self.config.set('lesson_each_region_object_priority', self.needed_levels)

    def Slot_for_accept_favor_student(self):
        res = self.lesson_favorStudent_LineEdit.text().split('>')
        self.config.set('lesson_favorStudent', res)
        return notification.success(self.tr('指定学生(填写指南见wiki)'), f'{self.tr("指定学生设置成功为:")}{res}',
                                    self.config)

    def Slot_for_lesson_level_change(self):
        res = []
        for i in range(len(self.lesson_names)):
            temp = []
            for j in range(4):
                if self.check_box_for_lesson_levels[i][j].isChecked():
                    temp.append(self.item_levels[j])
            res.append(temp)
        self.needed_levels = res
        self.config.set('lesson_each_region_object_priority', self.needed_levels)

    @delay(1)
    def Slot_for_lesson_time_change(self, _):
        res = []
        for i in range(len(self.lesson_names)):
            res.append(int(self.lesson_time_input[i].text()))
        self.priority_list = res
        self.config.set('lesson_times', self.priority_list)
        return notification.success(self.tr('日程次数'), f'{self.tr("日程次数设置成功为:")}{self.priority_list}',
                                    self.config)

    def __init_Signals_and_Slots(self):
        self.lesson_enableFavorStudent_check_box.stateChanged.connect(self.Slot_for_enableFavorStudent_check_box)
        self.accept_favor_student.clicked.connect(self.Slot_for_accept_favor_student)
        self.relationship_check_box.stateChanged.connect(self.Slot_for_relationship_check_box)
        for i in range(len(self.lesson_names)):
            for j in range(4):
                self.check_box_for_lesson_levels[i][j].toggled.connect(self.Slot_for_lesson_level_change)
            self.lesson_time_input[i].textChanged.connect(self.Slot_for_lesson_time_change)

    def __init_layouts(self):
        # 顶部三个配置项
        self.__init_enableFavorStudent_check_box_layout()
        self.__init_favorite_student_layout()
        self.__init_relationship_check_box_layout()

        # 表格布局
        self.tableLayout = QGridLayout()
        self.tableLayout.setSpacing(10)

        # 表头
        label_region = QLabel(self.tr("区域名称"), self)
        font = label_region.font()
        font.setBold(True)
        label_region.setFont(font)
        self.tableLayout.addWidget(label_region, 0, 0, Qt.AlignLeft)

        name = [self.tr("初级"), self.tr("普通"), self.tr("高级"), self.tr("特级")]
        for i, n in enumerate(name):
            label = QLabel(n, self)
            f = label.font()
            f.setBold(True)
            label.setFont(f)
            self.tableLayout.addWidget(label, 0, i + 1, Qt.AlignCenter)

        head_times = QLabel(self.tr("日程次数"), self)
        f2 = head_times.font()
        f2.setBold(True)
        head_times.setFont(f2)
        self.tableLayout.addWidget(head_times, 0, 5, Qt.AlignRight)

        # 每一行数据
        for row, region_name in enumerate(self.lesson_names, start=1):
            self.tableLayout.addWidget(QLabel(region_name, self), row, 0, Qt.AlignLeft)

            # 四个小按钮
            for col in range(4):
                wrapper = QHBoxLayout()
                wrapper.addStretch()
                wrapper.addWidget(self.check_box_for_lesson_levels[row - 1][col])
                wrapper.addStretch()
                self.tableLayout.addLayout(wrapper, row, col + 1)

            wrapper_input = QHBoxLayout()
            wrapper_input.addStretch()
            wrapper_input.addWidget(self.lesson_time_input[row - 1], 0, Qt.AlignRight)
            self.tableLayout.addLayout(wrapper_input, row, 5)

        self.vBoxLayout.addLayout(self.tableLayout)

    def __init_enableFavorStudent_check_box_layout(self):
        temp = QHBoxLayout()
        temp.addWidget(self.lesson_enableFavorStudent_check_box_description)
        temp.addWidget(self.lesson_enableFavorStudent_check_box)
        self.vBoxLayout.addLayout(temp)

    def __init_favorite_student_layout(self):
        temp = QHBoxLayout()
        temp.addWidget(self.lesson_favorStudent_LineEdit_description)
        temp.addWidget(self.lesson_favorStudent_LineEdit)
        temp.addWidget(self.accept_favor_student)
        self.vBoxLayout.addLayout(temp)

    def __init_relationship_check_box_layout(self):
        temp = QHBoxLayout()
        temp.addWidget(self.relationship_check_box_description)
        temp.addWidget(self.relationship_check_box)
        self.vBoxLayout.addLayout(temp)

    def Slot_for_relationship_check_box(self, state):
        self.config.set('lesson_relationship_first', state == Qt.Checked)

    def Slot_for_enableFavorStudent_check_box(self, state):
        self.config.set('lesson_enableInviteFavorStudent', state == Qt.Checked)
