import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qfluentwidgets import LineEdit, TabBar, CheckBox


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.hBoxLayout = QVBoxLayout(self)
        self.create_priority = self.get_create_priority()
        self.lay1 = QHBoxLayout()
        self.lay2 = QHBoxLayout()
        self.lay3 = QHBoxLayout()
        self.layout_for_acc_ticket = QHBoxLayout()

        self.label = QLabel(self.tr('目前制造物品优先级，排在前面的会优先选择'), self)
        self.input1 = QLabel(self)
        self.input2 = LineEdit(self)
        self.accept = QPushButton(self.tr('确定'), self)
        self.label_for_use_acc_ticket_check_box = QLabel(self.tr('是否使用加速券'), self)
        self.use_acc_ticket_checkbox = CheckBox(self)
        self.use_acc_ticket_checkbox.setChecked(self.config.get('use_acceleration_ticket'))
        self.use_acc_ticket_checkbox.stateChanged.connect(self.Slot_for_use_acc_ticket_check_box)
        self.layout_for_acc_ticket.addWidget(self.label_for_use_acc_ticket_check_box)
        self.layout_for_acc_ticket.addWidget(self.use_acc_ticket_checkbox)
        self.hBoxLayout.addLayout(self.layout_for_acc_ticket)

        time = self.config.get('createTime')

        # self.setFixedHeight(120)
        self.set_priority_text()
        self.input1.setFixedWidth(600)
        self.input2.setText(time)

        self.tabBar = TabBar(self)
        self.tabBar.setMovable(True)
        self.tabBar.setTabsClosable(False)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabMaximumWidth(200)
        self.tabBar.setAddButtonVisible(False)
        self.tabBar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tabBar.setFixedHeight(60)

        self.tabBar.setFixedWidth(750)
        for item in self.create_priority:
            self.tabBar.addTab(f'{random.Random().randint(0, 1000)}_{item}', item)

        self.accept.clicked.connect(self.__accept_main)

        self.lay1.addWidget(self.label, 0, Qt.AlignLeft)
        self.lay2.addWidget(self.input1, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.input2, 1, Qt.AlignLeft)
        self.lay2.addWidget(self.accept, 0, Qt.AlignLeft)

        self.lay3.addWidget(self.tabBar, 1, Qt.AlignLeft)

        self.lay1.addStretch(1)
        self.lay1.setAlignment(Qt.AlignCenter)
        self.lay2.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.lay1)
        self.hBoxLayout.addLayout(self.lay2)
        self.hBoxLayout.addLayout(self.lay3)
        self.hBoxLayout.setContentsMargins(20, 10, 20, 10)

    def __accept_main(self):
        # input1_content = self.input1.text()
        input2_content = self.input2.text()
        #
        # self.config.set('createPriority', input1_content)
        self.config.set('createTime', input2_content)
        #
        # w = InfoBar(
        #     icon=InfoBarIcon.SUCCESS,
        #     title='设置成功',
        #     content=f'制造次数：{input2_content}',
        #     orient=Qt.Vertical,
        #     position=InfoBarPosition.TOP_RIGHT,
        #     duration=800,
        #     parent=self.parent().parent().parent().parent()
        # )
        # w.show()
        print('test')
        print('>'.join(list(map(lambda x: x.text(), self.tabBar.items))))
        for i in range(0, len(self.create_priority)):
            self.create_priority[i] = self.tabBar.items[i].text()
        self.config.set('createPriority', self.create_priority)
        self.set_priority_text()

    def get_create_priority(self):
        default_priority = self.config.static_config['create_default_priority'][self.config.server_mode]
        current_priority = self.config.get('createPriority')
        res = []
        for i in range(0, len(current_priority)):
            if current_priority[i] in default_priority:
                res.append(current_priority[i])
        for j in range(0, len(default_priority)):
            if default_priority[j] not in res:
                res.append(default_priority[j])
        self.config.set('createPriority', res)
        return res

    def set_priority_text(self):
        res = ""
        for i in range(0, len(self.create_priority)):
            res += self.create_priority[i]
            if i != len(self.create_priority) - 1:
                res += '>'
        self.input1.setText(res)

    def Slot_for_use_acc_ticket_check_box(self, state):
        self.config.set('use_acceleration_ticket', state == Qt.Checked)
