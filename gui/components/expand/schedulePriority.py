from PyQt5.QtCore import Qt, QTranslator, QLocale
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import LineEdit, CheckBox

from core.utils import delay
from gui.util import notification


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.item_levels = ["primary", "normal", "advanced", "superior"]
        ls_names = self.config.static_config['lesson_region_name']
        self.lesson_names = ls_names[self.config.server_mode]
        self.priority_list = self.config.get('lesson_times')
        self.needed_levels = self.config.get('lesson_each_region_object_priority')
        self.check_config_validation()
        self.vBoxLayout = QVBoxLayout(self)
        self.relationship_check_box_description = QLabel(self.tr('优先做好感等级多的日程'), self)
        self.relationship_check_box = CheckBox('', self)
        self.relationship_check_box.setChecked(self.config.get('lesson_relationship_first'))
        self.hBoxLayout = QHBoxLayout()
        self.check_box_for_lesson_levels = []
        self.lesson_time_input = []
        int_validator = QIntValidator(0, 99, self)
        self.vBoxLayout.setSpacing(7)
        for i in range(0, len(self.lesson_names)):
            self.check_box_for_lesson_levels.append([])
            for j in range(0, 4):
                self.check_box_for_lesson_levels[i].append(CheckBox(self))
                if self.item_levels[j] in self.needed_levels[i]:
                    self.check_box_for_lesson_levels[i][j].setChecked(True)
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
            for i in range(0, len(self.lesson_names)):
                temp.append(self.item_levels)
            self.needed_levels = temp
            self.config.set('lesson_each_region_object_priority', self.needed_levels)

    def Slot_for_lesson_level_change(self):
        res = []
        for i in range(0, len(self.lesson_names)):
            temp = []
            for j in range(0, 4):
                if self.check_box_for_lesson_levels[i][j].isChecked():
                    temp.append(self.item_levels[j])
            res.append(temp)
        self.needed_levels = res
        self.config.set('lesson_each_region_object_priority', self.needed_levels)

    @delay(1)
    def Slot_for_lesson_time_change(self, _):
        res = []
        for i in range(0, len(self.lesson_names)):
            res.append(int(self.lesson_time_input[i].text()))
        self.priority_list = res
        self.config.set('lesson_times', self.priority_list)
        return notification.success(self.tr('日程次数'), f'{self.tr("日程次数设置成功为:")}{self.priority_list}', self.config)

    def __init_Signals_and_Slots(self):
        self.relationship_check_box.stateChanged.connect(self.Slot_for_relationship_check_box)
        for i in range(0, len(self.lesson_names)):
            for j in range(0, 4):
                self.check_box_for_lesson_levels[i][j].stateChanged.connect(self.Slot_for_lesson_level_change)
            self.lesson_time_input[i].textChanged.connect(self.Slot_for_lesson_time_change)

    def __init_layouts(self):
        self.__init_relationship_check_box_layout()
        self.__init_region_name_layout()
        self.__init_lesson_level_layout()
        self.__init_lesson_times_layout()
        self.vBoxLayout.addLayout(self.hBoxLayout)

    def __init_relationship_check_box_layout(self):
        temp = QHBoxLayout()
        temp.addWidget(self.relationship_check_box_description)
        temp.addWidget(self.relationship_check_box)
        self.vBoxLayout.addLayout(temp)

    def __init_region_name_layout(self):
        temp = QVBoxLayout()
        temp.addWidget(QLabel(self.tr("区域名称"), self), 0, Qt.AlignLeft)
        for i in range(0, len(self.lesson_names)):
            temp.addWidget(QLabel(self.lesson_names[i], self), 0, Qt.AlignLeft)
        self.hBoxLayout.addLayout(temp)

    def __init_lesson_level_layout(self):
        name = [self.tr("初级"), self.tr("普通"), self.tr("高级"), self.tr("特级")]
        for i in range(0, 4):
            temp = QVBoxLayout()
            temp.setContentsMargins(0, 5, 0, 5)
            temp.setSpacing(15)
            temp.addWidget(QLabel(name[i], self), 0, Qt.AlignLeft)
            for j in range(0, len(self.lesson_names)):
                temp.addWidget(self.check_box_for_lesson_levels[j][i], 0, Qt.AlignLeft)
            self.hBoxLayout.addLayout(temp)

    def __init_lesson_times_layout(self):
        temp = QVBoxLayout()
        temp.addWidget(QLabel(self.tr("日程次数"), self), 0, Qt.AlignLeft)
        for i in range(0, len(self.lesson_names)):
            temp.addWidget(self.lesson_time_input[i], 0, Qt.AlignLeft)
        self.hBoxLayout.addLayout(temp)

    def Slot_for_relationship_check_box(self, state):
        self.config.set('lesson_relationship_first', state == Qt.Checked)
