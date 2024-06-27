from .expandTemplate import TemplateLayout
from PyQt5.QtCore import QObject


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        PushConfig = QObject()
        configItems = [            {
                'label': PushConfig.tr('在运行出错时推送'),
                'key': 'push_after_error',
                'type': 'switch'
            },
            {
                'label': PushConfig.tr('在全部任务完成时推送'),
                'key': 'push_after_completion',
                'type': 'switch'
            },
            {
                'label': PushConfig.tr('json 推送'),
                'type': 'text',
                'key': 'push_json'
            },
            {
                'label': PushConfig.tr('ServerChan推送'),
                'type': 'text',
                'key': 'push_serverchan'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config, context="PushConfig")
