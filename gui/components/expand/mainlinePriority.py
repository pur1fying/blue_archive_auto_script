from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import PushButton, LineEdit, ComboBox
from gui.util import notification

from gui.util.translator import baasTranslator as bt


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.max_region = self.config.static_config.max_region[self.config.server_mode]
        self.info_widget = self.parent()
        self.vBoxLayout = QVBoxLayout(self)
        self.lay1 = QHBoxLayout()
        self.lay2 = QHBoxLayout()
        self.lay1_hard = QHBoxLayout()
        self.lay2_hard = QHBoxLayout()

        self.label = QLabel(self.tr('普通关卡与次数（如"1-1-1,1-2-3"表示关卡1-1打一次，然后关卡1-2打三次）：'), self)
        self.input = LineEdit(self)
        self.accept = PushButton(self.tr('确定'), self)
        self.label_hard = QLabel(self.tr('困难关卡设置同上，注意：次数最多为3），逗号均为英文逗号，日服、国际服可填max：'),self)
        self.input_hard = LineEdit(self)
        self.accept_hard = PushButton(self.tr('确定'), self)

        self.hard_task_combobox = ComboBox(self)
        self.each_student_task_number_dict = {
            self.tr("根据学生添加关卡"): [],
            self.tr("爱丽丝宝贝"): [],
        }
        for i in range(0, len(self.config.static_config.hard_task_student_material)):
            this_region = int(self.config.static_config.hard_task_student_material[i][0].split("-")[0])
            if this_region > self.max_region:
                break
            translated_name = bt.getStudent(self.config.static_config.hard_task_student_material[i][1])
            self.each_student_task_number_dict.setdefault(translated_name, [])
            temp = self.config.static_config.hard_task_student_material[i][0] + "-3"
            self.each_student_task_number_dict[translated_name].append(temp)

        for key in self.each_student_task_number_dict.keys():
            self.hard_task_combobox.addItem(key)
        self.hard_task_combobox.currentIndexChanged.connect(self.__hard_task_combobox_change)
        _set_main = self.config.get('mainlinePriority')
        _set_hard = self.config.get('hardPriority')

        self.setFixedHeight(200)

        self.input.setText(_set_main)
        self.input_hard.setText(_set_hard)

        self.input.setFixedWidth(700)
        self.input_hard.setFixedWidth(700)

        self.lay1.setContentsMargins(10, 0, 0, 10)
        self.lay2.setContentsMargins(10, 0, 0, 10)
        self.lay1_hard.setContentsMargins(10, 0, 0, 10)
        self.lay2_hard.setContentsMargins(10, 0, 0, 10)

        self.accept.clicked.connect(self.__accept_main)
        self.accept_hard.clicked.connect(self.__accept_hard)

        self.lay1.addWidget(self.label, 0, Qt.AlignLeft)
        self.lay2.addWidget(self.input, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.accept, 0, Qt.AlignLeft)
        self.lay1_hard.addWidget(self.label_hard, 0, Qt.AlignLeft)
        self.lay2_hard.addWidget(self.input_hard, 1, Qt.AlignLeft)
        self.lay2_hard.addWidget(self.accept_hard, 0, Qt.AlignLeft)

        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)
        self.lay2.setAlignment(Qt.AlignCenter)
        self.lay1_hard.addStretch(1)
        self.lay1_hard.setAlignment(Qt.AlignCenter)
        self.lay1_hard.addWidget(self.hard_task_combobox, 0, Qt.AlignRight)

        self.lay2_hard.setAlignment(Qt.AlignCenter)

        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)

        self.vBoxLayout.addLayout(self.lay1)
        self.vBoxLayout.addLayout(self.lay2)

        self.vBoxLayout.addLayout(self.lay1_hard)
        self.vBoxLayout.addLayout(self.lay2_hard)

    def __accept_main(self):
        try:
            from module.normal_task import readOneNormalTask
            input_content = self.input.text()
            if input_content == "":
                self.config.set('mainlinePriority', "")
                self.config.set("unfinished_normal_tasks", [])
                notification.success(self.tr('设置成功'), f'{self.tr("普通关扫荡设置已清空")}',self.config)
                return
            self.config.set('mainlinePriority', input_content)
            input_content = input_content.split(',')
            temp = []
            for i in range(0, len(input_content)):
                temp.append(readOneNormalTask(
                    input_content[i],
                    self.config.static_config.explore_normal_task_region_range)
                )
            self.config.set("unfinished_normal_tasks", temp)  # refresh the config unfinished_normal_tasks
            notification.success(self.tr('设置成功'), f'{self.tr("你的普通关卡已经被设置为：")}{input_content}',
                                 self.config)
        except Exception as e:
            notification.error(self.tr('设置失败'), f'{self.tr("请检查输入格式是否正确，错误信息：")}{e}', self.config)

    def __accept_hard(self):
        try:
            from module.hard_task import readOneHardTask
            input_content = self.input_hard.text()
            if input_content == "":
                self.config.set('hardPriority', "")
                self.config.set("unfinished_hard_tasks", [])
                notification.success(self.tr('设置成功'), f'{self.tr("困难关扫荡设置已清空")}', self.config)
                return
            self.config.set('hardPriority', input_content)
            input_content = input_content.split(',')
            temp = []
            for i in range(0, len(input_content)):
                temp.append(readOneHardTask(
                            input_content[i],
                            self.config.static_config.explore_hard_task_region_range
                    )
                )
            self.config.set("unfinished_hard_tasks", temp)  # refresh the config unfinished_hard_tasks
            notification.success(self.tr('设置成功'), f'{self.tr("你的困难关卡已经被设置为：")}{input_content}',
                                 self.config)
        except Exception as e:
            notification.error(self.tr('设置失败'), f'{self.tr("请检查输入格式是否正确，错误信息：")}{e}', self.config)

    def __hard_task_combobox_change(self):
        if self.hard_task_combobox.currentText() == self.tr("根据学生添加关卡"):
            return
        st = ""
        if self.input_hard.text() != "":
            st = self.input_hard.text() + ","
        self.input_hard.setText(
            st + ','.join(self.each_student_task_number_dict[self.hard_task_combobox.currentText()]))
        self.__accept_hard()
