from PyQt5.QtCore import QObject

from core.utils import detach
from gui.components.expand.expandTemplate import TemplateLayout
from ...util import notification


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        ExploreConfig = QObject()
        configItems = [
            {
                'label': ExploreConfig.tr('是否手动boss战'),
                'key': 'manual_boss',
                'type': 'switch',
                'tip': ExploreConfig.tr('普通图独有配置，进入关卡后暂停等待手操')
            },
            {
                'label': ExploreConfig.tr('普通图推图设置'),
                'key': 'explore_normal_task_list',
                'type': 'text__action',
                'tip': ExploreConfig.tr('请填写要推的图,填写方式见-普通图自动推图说明-'),
                'selection': self._action_normal

            },
            {
                'label': ExploreConfig.tr('困难图推图设置'),
                'key': 'explore_hard_task_list',
                'type': 'text__action',
                'tip': ExploreConfig.tr(
                    '困难图队伍属性和普通图相同(见普通图推图设置)，请按照帮助中说明选择推困难图关卡并按对应图设置队伍'),
                'selection': self._action_hard
            }
        ]
        super().__init__(parent=parent, config=config, configItems=configItems, context="ExploreConfig")

    @detach
    def _action_hard(self):
        nml_list = self.config.get('explore_hard_task_list')
        notification.success(self.tr('困难关推图'), self.tr("正在推困难关")+": "+str(nml_list), self.config)
        self.config.get_signal('update_signal').emit(['困难关推图'])
        self.config.get_main_thread().start_hard_task()

    @detach
    def _action_normal(self):
        nml_list = self.config.get('explore_normal_task_list')
        notification.success(self.tr('普通关推图'), self.tr("正在推普通关")+": "+str(nml_list), self.config)
        self.config.get_signal('update_signal').emit(['普通关推图'])
        self.config.get_main_thread().start_normal_task()
