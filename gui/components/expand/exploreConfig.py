from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QHBoxLayout, QLabel
from qfluentwidgets import LineEdit, PushButton

from .expandTemplate import TemplateLayout
from ...util import notification


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        ExploreConfig = QObject()
        self.config = config
        configItems = [
            {
                'label': ExploreConfig.tr('是否手动boss战（进入关卡后暂停等待手操）'),
                'key': 'manual_boss',
                'type': 'switch'
            },
            {
                'label': ExploreConfig.tr('是否不强制打到sss（启用后跳过已通过但未sss的关卡）'),
                'key': 'explore_normal_task_force_sss',
                'type': 'switch'
            },
            {
                'label': ExploreConfig.tr('开启后强制打每一个指定的关卡（不管是否sss）'),
                'key': 'explore_normal_task_force_each_fight',
                'type': 'switch'
            },
            {
                'label': ExploreConfig.tr('爆发一队'),
                'key': 'burst1',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': ExploreConfig.tr('爆发二队'),
                'key': 'burst2',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': ExploreConfig.tr('贯穿一队'),
                'key': 'pierce1',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': ExploreConfig.tr('贯穿二队'),
                'key': 'pierce2',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': ExploreConfig.tr('神秘一队'),
                'key': 'mystic1',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
            {
                'label': ExploreConfig.tr('神秘二队'),
                'key': 'mystic2',
                'selection': ['1', '2', '3', '4'],
                'type': 'combo'
            },
        ]
        if self.config.server_mode == 'JP' or self.config.server_mode == 'Global':
            configItems.extend([
                {
                    'label': ExploreConfig.tr('振动一队'),
                    'key': 'shock1',
                    'selection': ['1', '2', '3', '4'],
                    'type': 'combo'
                },
                {
                    'label': ExploreConfig.tr('振动二队'),
                    'key': 'shock2',
                    'selection': ['1', '2', '3', '4'],
                    'type': 'combo'
                }
            ])
        super().__init__(parent=parent, configItems=configItems, config=config, context='ExploreConfig')

        self.push_card = QHBoxLayout()
        self.push_card_label = QHBoxLayout()
        self.label_tip_push = QLabel(
            '<b>' + self.tr('推图选项') + '</b>&nbsp;' + self.tr('请在下面填写要推的图,填写方式见-普通图自动推图说明-'), self)
        self.input_push = LineEdit(self)
        self.accept_push = PushButton(self.tr('开始推图'), self)

        self.input_push.setText(
            self.config.get('explore_normal_task_regions').__str__().replace('[', '').replace(']', ''))
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
        self.config.set('explore_normal_task_regions', self.input_push.text())
        value = self.input_push.text()
        notification.success(self.tr('普通关推图'), f'{self.tr("你的普通关配置已经被设置为：")}{value}，{self.tr("正在推普通关。")}', self.config)
        sig = self.config.get_signal('update_signal')
        sig.emit(['普通关推图'])
        import threading
        threading.Thread(target=self.action).start()

    def action(self):
        self.config.get_main_thread().start_normal_task()
