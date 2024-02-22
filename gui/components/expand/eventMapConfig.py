from .expandTemplate import TemplateLayout
# TODO: Prepare to support the following import
# from ...util.common_methods import get_context_thread

class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '推故事',
                'type': 'button',
                # TODO: Plot push function
                'selection': lambda: print('推故事')
            },
            {
                'label': '推任务',
                'type': 'button',
                # TODO: Task push function
                'selection': lambda: print('推任务')
            },
            {
                'label': '推挑战',
                'type': 'button',
                # TODO: Challenge push function
                'selection': lambda: print('推挑战')
            },
        ]
        super().__init__(parent=parent, configItems=configItems, config=config)
