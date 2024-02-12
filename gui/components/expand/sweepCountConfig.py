from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '各扫荡区域次数以逗号分隔，日服、国际服扫荡次数可以为max',
                'type': 'label'
            },
            {
                'label': '学园交流会扫荡',
                'type': 'text',
                'key': 'scrimmage_times'
            },
            {
                'label': '活动关卡扫荡',
                'type': 'text',
                'key': 'activity_sweep_times'
            },
            {
                'label': '特殊委托扫荡',
                'type': 'text',
                'key': 'special_task_times'
            }
        ]
        super().__init__(parent=parent, configItems=configItems, config=config)
