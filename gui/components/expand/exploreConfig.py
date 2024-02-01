from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel
from qfluentwidgets import LineEdit, PushButton, InfoBar, InfoBarIcon, InfoBarPosition

from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '开启此按钮点击推图进行活动任务关推图(当前活动:69号新春狂想曲)',
                'key': 'explore_activity',
                'type': 'switch'
            },
            {
                'label': '是否手动boss战（进入关卡后暂停等待手操）',
                'key': 'manual_boss',
                'type': 'switch'
            },
            {
                'label': '爆发一队',
                'key': 'burst1',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': '爆发二队',
                'key': 'burst2',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': '贯穿一队',
                'key': 'pierce1',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': '贯穿二队',
                'key': 'pierce2',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': '神秘一队',
                'key': 'mystic1',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': '神秘二队',
                'key': 'mystic2',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': '各图需要队伍17[爆发,贯穿] 16[贯穿,神秘] 15[神秘,神秘] 14[爆发,神秘] 13[贯穿,贯穿] 12[神秘,爆发] 11[贯穿,神秘] 10[爆发,神秘] 9[爆发,贯穿] ',
                'type': 'label'
            },
            {
                'label': '                      8[贯穿,贯穿]   7[爆发,爆发]    6[贯穿,贯穿]    5[爆发]4[贯穿]',
                'type': 'label'
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
                         '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
                         '<b>如果有多个队伍一定要设置主队编号小于副队(如15图神秘1队必须小于神秘2队编号)</b>',
                'type': 'label'
            }
        ]

        super().__init__(parent=parent, configItems=configItems)

        self.push_card = QHBoxLayout(self)
        self.push_card_label = QHBoxLayout(self)
        self.label_tip_push = QLabel(
            '<b>推图选项</b>&nbsp;请在下面填写要推的图的章节数，如“15,16,14”为依次推15图,16图,14图：', self)
        self.input_push = LineEdit(self)
        self.accept_push = PushButton('开始推图', self)

        self.input_push.setText(self.get('explore_normal_task_regions').__str__().replace('[', '').replace(']', ''))
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
        if self.input_push.text() != '':
            push_list = [int(x) for x in self.input_push.text().split(',')]
            self.set('explore_normal_task_regions', push_list)
        value = self.input_push.text()
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的普通关配置已经被设置为：{value}，正在推普通关。',
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
        self.get_thread().start_normal_task()
