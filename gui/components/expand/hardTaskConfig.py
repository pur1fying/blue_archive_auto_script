from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QHBoxLayout, QLabel
from qfluentwidgets import LineEdit, PushButton

from .expandTemplate import TemplateLayout
from ...util import notification

class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        HardTaskConfig = QObject()
        configItems = [
            {
                'label': HardTaskConfig.tr('打到SSS'),
                'key': 'explore_hard_task_need_sss',
                'type': 'switch'
            },
            {
                'label': HardTaskConfig.tr('拿礼物'),
                'key': 'explore_hard_task_need_present',
                'type': 'switch'
            },
            {
                'label': HardTaskConfig.tr('完成成就任务'),
                'key': 'explore_hard_task_need_task',
                'type': 'switch'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config, context="HardTaskConfig")

        self.push_card = QHBoxLayout()
        self.push_card_label = QHBoxLayout()
        self.label_tip_push = QLabel(
            self.tr('<b>困难图队伍属性和普通图相同(见普通图推图设置)，请按照帮助中说明选择推困难图关卡并按对应图设置队伍</b>'),
            self)
        self.input_push = LineEdit(self)
        self.accept_push = PushButton(self.tr('开始推图'), self)

        self.input_push.setText(self.config.get('explore_hard_task_list'))
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

        self.vBoxLayout.addLayout(self.push_card_label)
        self.vBoxLayout.addLayout(self.push_card)

    def _accept_push(self):
        value = self.input_push.text()
        self.config.set('explore_hard_task_list', value)
        notification.success(self.tr('困难关推图'), f'{self.tr("你的困难关配置已经被设置为：")}{value}，{self.tr("正在推困难关。")}', self.config)
        import threading
        threading.Thread(target=self.action).start()

    def action(self):
        self.config.get_main_thread().start_hard_task()
