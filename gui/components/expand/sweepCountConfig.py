from PyQt5.QtCore import QObject
from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        SweepCountConfig = QObject()
        sweep_label_description = {
            'CN': SweepCountConfig.tr('<b>各区域扫荡次数以英文逗号分隔</b>'),
            'Global': SweepCountConfig.tr('<b>各区域扫荡次数以英文逗号分隔，扫荡次数可以为max</b>'),
            'JP': SweepCountConfig.tr('<b>各区域扫荡次数以英文逗号分隔，扫荡次数可以为max</b>'),
        }
        configItems = [
            {
                'label': sweep_label_description[config.server_mode],
                'type': 'label'
            },
            {
                'label': SweepCountConfig.tr('悬赏委托扫荡'),
                'type': 'text',
                'key': 'rewarded_task_times'
            },
            {
                'label': SweepCountConfig.tr('学园交流会扫荡'),
                'type': 'text',
                'key': 'scrimmage_times'
            },
            {
                'label': SweepCountConfig.tr('活动关卡扫荡关卡'),
                'type': 'text',
                'key': 'activity_sweep_task_number'
            },
            {
                'label': SweepCountConfig.tr('活动关卡扫荡次数'),
                'type': 'text',
                'key': 'activity_sweep_times'
            },
            {
                'label': SweepCountConfig.tr('特殊委托扫荡'),
                'type': 'text',
                'key': 'special_task_times'
            },
        ]
        additional_items = [
            {
                'label': SweepCountConfig.tr('国服购买邀请券可在<b>商店购买</b>中实现'),
                'type': 'label'
            }
        ]
        if config.server_mode in ['JP', 'Global']:
            additional_items = [
                {
                    'label': SweepCountConfig.tr('<b>用券数目设置，下拉框选择</b>'),
                    'type': 'label'
                },
                {
                    'label': SweepCountConfig.tr('悬赏委托扫荡券购买次数'),
                    'type': 'combo',
                    'key': 'purchase_rewarded_task_ticket_times',
                    'selection': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'max']
                },
                {
                    'label': SweepCountConfig.tr('日程券购买次数'),
                    'type': 'combo',
                    'key': 'purchase_lesson_ticket_times',
                    'selection': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'max']
                },
                {
                    'label': SweepCountConfig.tr('学园交流会扫荡券购买次数'),
                    'type': 'combo',
                    'key': 'purchase_scrimmage_ticket_times',
                    'selection': ['0', '1', '2', '3', '4', 'max']
                }
            ]
        for item in additional_items:
            configItems.append(item)
        super().__init__(parent=parent, configItems=configItems, config=config, context='SweepCountConfig')
