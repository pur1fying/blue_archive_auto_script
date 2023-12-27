from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel
from qfluentwidgets import LineEdit, PushButton, InfoBar, InfoBarIcon, InfoBarPosition

from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '是否手动已经SSS',
                'key': 'hard_task_sss',
                'type': 'switch'
            },
            {
                'label': '是否需要拾取钻石',
                'key': 'hard_task_collect_present',
                'type': 'switch'
            },
            {
                'label': '是否已经完成该困难关',
                'key': 'hard_task_accomplishment',
                'type': 'switch'
            },
            {
                'label': """
    一组由逗号隔开的数据
    按逗号拆分后变为一个列表如果列表元素只有一个数字
    例子：
    15
    need_sss true
    need_present false
    need task true
    15图所有关打到sss并且完成挑战任务
    及根据need_sss/present/task 将这个图所有任务(15-1,15-2,15-3)都完成对应要求

    如果是一个数字并跟字符串，则用‘-’分隔
    例子: 15-sss-present
    会将这张图所有任务(15-1,15-2,15-3)打到sss并拿礼物

    如果有两个数字则指定到对应关卡
    例子:15-3-sss
    会将15-3打到sss
                """,
                'type': 'label'
            },
        ]

        super().__init__(parent=parent, configItems=configItems)

        self.push_card = QHBoxLayout(self)
        self.push_card_label = QHBoxLayout(self)
        self.label_tip_push = QLabel(
            '<b>按照以上说明填写推困难图选项</b>', self)
        self.input_push = LineEdit(self)
        self.accept_push = PushButton('保存配置', self)

        self.input_push.setFixedWidth(700)
        self.accept_push.clicked.connect(self._accept_push)

        self.push_card_label.addWidget(self.label_tip_push, 0, Qt.AlignLeft)
        self.push_card.addWidget(self.input_push, 1, Qt.AlignLeft)
        self.push_card.addWidget(self.accept_push, 0, Qt.AlignLeft)

        self.push_card.addStretch(1)
        self.push_card.setAlignment(Qt.AlignCenter)
        self.push_card.setContentsMargins(10, 0, 0, 10)

        self.push_card_label.addStretch(1)
        self.push_card_label.setAlignment(Qt.AlignCenter)
        self.push_card_label.setContentsMargins(10, 0, 0, 10)

        self.hBoxLayout.addLayout(self.push_card_label)
        self.hBoxLayout.addLayout(self.push_card)

    def _accept_push(self):
        value = self.input_push.text()
        self.set('explore_hard_task_list', value)
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的困难关配置已经被设置为：{value}',
            orient=Qt.Vertical,  # vertical layout
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.parent().parent().parent().parent().parent().parent().parent()
        )
        w.show()
