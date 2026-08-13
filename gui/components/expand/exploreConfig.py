from PyQt5.QtCore import QObject

from core.utils import detach
from gui.components.expand.expandTemplate import TemplateLayout
from gui.util.config_draft import ConfigDraft, as_live
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
                'label': ExploreConfig.tr('使用简易模式推图'),
                'key': 'explore_task_use_simple_mode',
                'type': 'switch',
                'tip': ExploreConfig.tr('简易模式只需要一支成形队伍, 角色较少时建议使用(默认使用第一支队伍)')
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

    def _publish_draft_for_action(self):
        """Card dialog injects ConfigDraft; tasks read live ConfigSet.

        执行 must flush the focused LineEdit and commit the draft first, otherwise
        start_*_task() still sees the old explore_*_task_list on disk/live memory.
        """
        cfg = self.config
        if isinstance(cfg, ConfigDraft):
            cfg.flush_and_commit(self)
            return as_live(cfg)
        return cfg

    @detach
    def _action_hard(self):
        live = self._publish_draft_for_action()
        nml_list = live.get('explore_hard_task_list')
        notification.success(self.tr('困难关推图'), self.tr("正在推困难关")+": "+str(nml_list), live)
        live.get_signal('update_signal').emit(['困难关推图'])
        live.get_main_thread().start_hard_task()

    @detach
    def _action_normal(self):
        live = self._publish_draft_for_action()
        nml_list = live.get('explore_normal_task_list')
        notification.success(self.tr('普通关推图'), self.tr("正在推普通关")+": "+str(nml_list), live)
        live.get_signal('update_signal').emit(['普通关推图'])
        live.get_main_thread().start_normal_task()
