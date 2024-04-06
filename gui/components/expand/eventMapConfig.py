from PyQt5.QtCore import QObject
from .expandTemplate import TemplateLayout
from ...util.common_methods import get_context_thread


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        # name it EventMapConfig to have context with same name
        EventMapConfig = QObject()
        configItems = [
            {
                'label': EventMapConfig.tr('推故事'),
                'type': 'button',
                'selection': self.activity_story
            },
            {
                'label': EventMapConfig.tr('推任务'),
                'type': 'button',
                'selection': self.activity_mission
            },
            {
                'label': EventMapConfig.tr('推挑战'),
                'type': 'button',
                'selection': self.activity_challenge
            },
        ]
        super().__init__(parent=parent, configItems=configItems, config=config, context='EventMapConfig')

    def activity_story(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_explore_activity_story).start()

    def activity_mission(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_explore_activity_mission).start()

    def activity_challenge(self):
        import threading
        threading.Thread(target=get_context_thread(self).start_explore_activity_challenge).start()
