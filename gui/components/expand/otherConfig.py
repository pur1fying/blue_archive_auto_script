from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '一键反和谐',
                'type': 'button',
                'selection': self.fhx,
                'key': None
            },
            {
                'label': '修复Mumu无法登录日服',
                'type': 'button',
                'selection': self.mumu_JP_login_fixer,
                'key': None
            },
            {
                'label': '显示首页头图（下次启动时生效）',
                'type': 'switch',
                'key': 'bannerVisibility'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config)

    def mumu_JP_login_fixer(self):
        self.config.get_main_thread().start_mumu_JP_login_fixer()

    def fhx(self):
        self.config.get_main_thread().start_fhx()
