from PyQt5.QtCore import QObject
from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        OtherConfig = QObject()
        configItems = [
            {
                'label': OtherConfig.tr('一键反和谐'),
                'type': 'button',
                'selection': self.fhx,
                'key': None
            },
            {
                'label': OtherConfig.tr('显示首页头图（下次启动时生效）'),
                'type': 'switch',
                'key': 'bannerVisibility'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config, context="OtherConfig")

    def fhx(self):
        self.config.get_main_thread().start_fhx()
