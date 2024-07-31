from PyQt5.QtCore import QObject
from .expandTemplate import TemplateLayout


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
        self.main_thread = config.get_main_thread()
        super().__init__(parent=parent, configItems=configItems, config=config, context='EventMapConfig')
        print(self.gen_event_formation_attr())

    def activity_story(self):
        import threading
        threading.Thread(target=self.main_thread.start_explore_activity_story).start()

    def activity_mission(self):
        import threading
        threading.Thread(target=self.main_thread.start_explore_activity_mission).start()

    def activity_challenge(self):
        import threading
        threading.Thread(target=self.main_thread.start_explore_activity_challenge).start()

    def gen_event_formation_attr(self):
        current_event = self.config.static_config['current_game_activity'][self.config.server_mode]
        print(current_event)
        if current_event is None:
            return None
        import importlib
        try:
            module = importlib.import_module('src.explore_task_data.activities.' + current_event)
            stage_data = getattr(module, 'stage_data')
        except ModuleNotFoundError:
            return None
        ret = dict(activity_name=current_event, story=dict(), mission=dict(), challenge=dict())
        print(stage_data)
        en2cn = {
            "story": "故事",
            "mission": "任务",
            "challenge": "挑战",
        }
        from module.explore_normal_task import formation_attr_to_cn
        for key, value in stage_data.items():
            print(key)
            if key == "story" or key == "mission" or key == "challenge":
                for i in range(len(value)):
                    print(value[i])
                    ret[key][en2cn[key] + str(i+1)] = formation_attr_to_cn(value[i])
                continue
            tp = None
            if key.startswith("story"):
                tp = "story"
            elif key.startswith("mission"):
                tp = "mission"
            elif key.startswith("challenge"):
                tp = "challenge"
            if tp is None:
                continue
            pos = key.find("_")
            if pos == -1:
                continue
            number = key[len(tp):pos]
            name = en2cn[tp] + number
            if "sss" in key:
                name += "三星"
            elif "task" in key:
                name += "成就任务"
            team = ""
            for s in value['start']:
                temp = formation_attr_to_cn(s[0])
                if temp is not None:
                    team += temp + " "
            if team.endswith(" "):
                team = team[:-1]
            ret[tp][name] = team
        print(ret)
        return ret

