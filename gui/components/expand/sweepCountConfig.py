from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '<b>各扫荡区域次数以逗号分隔，日服、国际服扫荡次数可以为max</b>',
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
            },
            {
                'label': '<b>用券数目设置，下拉框选择</b>',
                'type': 'label'
            },
            {
                'label': '悬赏委托扫荡券购买次数',
                'type': 'combo',
                'key': 'purchase_rewarded_task_ticket_times',
                'selection': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'max']
            },
            {
                'label': '日程扫荡券购买次数',
                'type': 'combo',
                'key': 'purchase_lesson_ticket_times',
                'selection': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'max']
            }
        ]
        if config.server_mode in ['JP', 'Global']:
            configItems.append({
                'label': '学园交流会扫荡券购买次数',
                'type': 'combo',
                'key': 'purchase_scrimmage_ticket_times',
                'selection': ['0', '1', '2', '3', '4', 'max']
            })
        super().__init__(parent=parent, configItems=configItems, config=config)
