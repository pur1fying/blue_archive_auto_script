from .expandTemplate import TemplateLayout


def fhx():
    try:
        import main
        t = main.Main()
        t.solve('de_clothes')
    except Exception as e:
        print(e)


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '一键反和谐',
                'type': 'button',
                'selection': fhx,
                'key': None
            },
            {
                'label': '显示首页头图（下次启动时生效）',
                'type': 'switch',
                'key': 'bannerVisibility'
            }
        ]

        super().__init__(parent=parent, configItems=configItems)
