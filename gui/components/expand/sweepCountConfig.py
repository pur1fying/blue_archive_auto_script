from PyQt5.QtCore import QObject
from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        SweepCountConfig = QObject()
        sweep_label_description = {
            'CN': SweepCountConfig.tr('<b>活动关卡：关卡号与剩余扫荡次数均以英文逗号分隔、按顺序配对。剩余次数跨次运行累计扣减，扣到 0 跳过该关卡；填 -1 表示该关卡最后扫且次数无限。</b>'),
            'Global': SweepCountConfig.tr('<b>Activity stages: stage numbers and remaining sweep counts are comma-separated and paired in order. Remaining counts persist across runs and decrement each sweep; 0 skips a stage, -1 means sweep last with unlimited times.</b>'),
            'JP': SweepCountConfig.tr('<b>活動ステージ：ステージ番号と残りスイープ回数はカンマ区切りで順に対応付けます。残り回数は実行ごとに減算され、0でそのステージをスキップ、-1は最後に無制限でスイープします。</b>'),
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
                'label': SweepCountConfig.tr('活动关卡扫荡关卡（逗号分隔）'),
                'type': 'text',
                'key': 'activity_sweep_task_number'
            },
            {
                'label': SweepCountConfig.tr('活动关卡扫荡剩余次数（-1=无限且最后扫）'),
                'type': 'text',
                'key': 'activity_sweep_times'
            },
            {
                'label': SweepCountConfig.tr('特殊委托扫荡'),
                'type': 'text',
                'key': 'special_task_times'
            },
            {
                'label': SweepCountConfig.tr('<b>用券数目设置，下拉框选择</b>'),
                'type': 'label'
            },
            {
                'label': SweepCountConfig.tr('悬赏委托扫荡券购买次数'),
                'type': 'combo',
                'key': 'purchase_rewarded_task_ticket_times',
                'selection': ['max', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
            },
            {
                'label': SweepCountConfig.tr('日程券购买次数'),
                'type': 'combo',
                'key': 'purchase_lesson_ticket_times',
                'selection': ['max', '0', '1', '2', '3', '4']
            },
            {
                'label': SweepCountConfig.tr('学园交流会扫荡券购买次数'),
                'type': 'combo',
                'key': 'purchase_scrimmage_ticket_times',
                'selection': ['max', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

            }
        ]
        super().__init__(parent=parent, configItems=configItems, config=config, context='SweepCountConfig')
