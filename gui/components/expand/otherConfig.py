from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '一键反和谐',
                'type': 'button',
                'selection': self.fhx,
                'key': None
            },
            {
                'label': '显示首页头图（下次启动时生效）',
                'type': 'switch',
                'key': 'bannerVisibility'
            }
        ]

        super().__init__(parent=parent, configItems=configItems)

    def get_thread(self, parent=None):
        if parent is None:
            parent = self.parent()
        for component in parent.children():
            if type(component).__name__ == 'HomeFragment':
                return component.get_main_thread()
        return self.get_thread(parent.parent())

    def fhx(self):
        self.get_thread().start_fhx()
