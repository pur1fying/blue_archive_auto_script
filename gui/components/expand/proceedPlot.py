from .expandTemplate import TemplateLayout
from ...util.common_methods import get_context_thread


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '主线剧情需要推的章节数',
                'type': 'text',
                'key': 'main_story_regions'
            },
            {
                'label': '开始推主线剧情',
                'type': 'button',
                'selection': self.proceed_main_plot,
                'key': None
            },
            {
                'label': '开始推小组剧情',
                'type': 'button',
                'selection': self.proceed_group_plot,
                'key': None
            },
            {
                'label': '开始推支线剧情',
                'type': 'button',
                'selection': self.proceed_branch_plot,
                'key': None
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config)

    def proceed_main_plot(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_main_story).start()

    def proceed_group_plot(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_group_story).start()

    def proceed_branch_plot(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_mini_story).start()
