from .expandTemplate import TemplateLayout
from ...util.common_methods import get_context_thread


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '推故事',
                'type': 'button',
                'selection': self.activity_story
            },
            {
                'label': '推任务',
                'type': 'button',
                'selection': self.activity_mission
            },
            {
                'label': '推挑战',
                'type': 'button',
                'selection': self.activity_challenge
            },
        ]
        self.main_thread = config.get_main_thread()
        super().__init__(parent=parent, configItems=configItems, config=config)

    def activity_story(self):
        import threading
        threading.Thread(target=self.main_thread.start_explore_activity_story).start()

    def activity_mission(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_explore_activity_mission).start()

    def activity_challenge(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_explore_activity_challenge).start()
