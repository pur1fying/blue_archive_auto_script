from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import ComboBox, LineEdit, PushButton

import main
from .expandTemplate import TemplateLayout
from gui.util.config_set import ConfigSet


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
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
        ]

        super().__init__(parent=parent, configItems=configItems)

        self.push_card = QHBoxLayout(self)
        self.push_card_label = QHBoxLayout(self)
        self.label_tip_push = QLabel(
            '<b>推图选项</b>&nbsp;请在下面填写要推的图的章节数，如“15,16,14”为依次推15图,16图,14图：', self)
        self.input_push = LineEdit(self)
        self.accept_push = PushButton('开始推图', self)

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
        push_list = [int(x) for x in self.input_push.text().split(',')]
        self.set('explore_normal_task_regions', push_list)
        t = main.Main()
        t.solve('explore_normal_task')
