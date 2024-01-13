from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel
from qfluentwidgets import LineEdit, PushButton, InfoBar, InfoBarIcon, InfoBarPosition

from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '打到SSS',
                'key': 'explore_hard_task_need_sss',
                'type': 'switch'
            },
            {
                'label': '拿礼物',
                'key': 'explore_hard_task_need_present',
                'type': 'switch'
            },
            {
                'label': '完成成就任务',
                'key': 'explore_hard_task_need_task',
                'type': 'switch'
            },
            {
                'label': """
    推图关卡中填写的数据不应该超出这些字符或单词 "-" , "sss", "present", "task", "," , 和数字
    按逗号拆分后变为若干关卡
    1.如果只有一个数字 或 指定关卡
    例子:15,12-2
    根据上面三个按钮的开关 将(15-1,15-2,15-3,12-2)打到sss/拿礼物/完成挑战任务

    2.如果是一个数字并跟字符串，则用‘-’分隔
    例子: 15-sss-present
    会将(15-1,15-2,15-3)打到sss并拿礼物

    3.如果有两个数字则指定到对应关卡
    例子:15-3-sss-task
    会将15-3打到sss并且完成挑战任务

    4.例子
    开关都开启，填写: 7,8-sss,9-3-task
    表示依次执行(7-1,7-2,7-3)打到sss,拿礼物并完成挑战任务,(8-1,8-2,8-3)打到sss，9-3完成挑战任务
    注:Baas会自动判断关卡是否已经打到sss，是否拿了礼物，如果已经打到sss或拿了礼物，则不会再次打该关卡
                """,
                'type': 'label'
            },
        ]

        super().__init__(parent=parent, configItems=configItems)

        self.push_card = QHBoxLayout(self)
        self.push_card_label = QHBoxLayout(self)
        self.label_tip_push = QLabel(
            '<b>困难图队伍属性和普通图相同(见普通图推图设置)，请按照以上说明选择推困难图关卡并按对应图设置队伍(额外需要: H15-3贯穿2队 H16-3:贯穿1队)</b>', self)
        self.input_push = LineEdit(self)
        self.accept_push = PushButton('开始推图', self)

        self.input_push.setText(self.get('explore_hard_task_list'))
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
            content=f'你的困难关配置已经被设置为：{value}，正在推困难关。',
            orient=Qt.Vertical,  # vertical layout
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.parent().parent().parent().parent().parent().parent().parent()
        )
        w.show()
        import threading
        threading.Thread(target=self.action).start()

    def get_thread(self, parent=None):
        if parent is None:
            parent = self.parent()
        for component in parent.children():
            if type(component).__name__ == 'HomeFragment':
                return component.get_main_thread()
        return self.get_thread(parent.parent())

    def action(self):
        self.get_thread().start_hard_task()
