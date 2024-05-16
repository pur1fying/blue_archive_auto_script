from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [            {
                'label': '在运行出错时推送',
                'key': 'push_after_error',
                'type': 'switch'
            },
            {
                'label': '在全部任务完成时推送',
                'key': 'push_after_completion',
                'type': 'switch'
            },
            {
                'label': 'json 推送',
                'type': 'text',
                'key': 'push_json'
            },
            {
                'label': 'ServerChan推送',
                'type': 'text',
                'key': 'push_serverchan'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config)
