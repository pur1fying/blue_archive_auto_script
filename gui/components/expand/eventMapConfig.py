from math import ceil

import numpy as np
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import TableWidget

from .expandTemplate import TemplateLayout
from gui.util.translator import baasTranslator as bt


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
        activity_formation = self.gen_event_formation_attr()
        activity_name = activity_formation['activity_name'] if activity_formation else self.tr('无')
        name_label = QLabel(self.tr('当期活动：') + activity_name, self)
        optionPanel = QHBoxLayout()
        optionPanel.addWidget(name_label, 0, Qt.AlignLeft)
        self.vBoxLayout.addLayout(optionPanel)
        if activity_formation:
            total_list = []
            challenge = activity_formation.get('mission', None)
            if challenge:
                challenge_list = np.array(
                    [(k, v) for k, v in zip(list(challenge.keys()), list(challenge.values()))]).flatten().tolist()
                total_list.extend(challenge_list)
            story = activity_formation.get('story', None)
            if story:
                story_list = np.array(
                    [(k, v) for k, v in zip(list(story.keys()), list(story.values()))]).flatten().tolist()
                total_list.extend(story_list)
            mission = activity_formation.get('challenge', None)
            if mission:
                mission_list = np.array(
                    [(k, v) for k, v in zip(list(mission.keys()), list(mission.values()))]).flatten().tolist()
                total_list.extend(mission_list)

            if len(total_list) > 0:
                labelComponent = QLabel(self.tr('任务属性对应表'), self)
                optionPanel = QHBoxLayout()
                optionPanel.addWidget(labelComponent, 0, Qt.AlignLeft)
                self.vBoxLayout.addLayout(optionPanel)

                tableView = TableWidget(self)
                tableView.setWordWrap(False)
                tableView.setRowCount(ceil(len(total_list)/4))
                tableView.setColumnCount(4)
                tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                tableView.setHorizontalHeaderLabels(
                    [self.tr('关卡'), self.tr('属性'), self.tr('关卡'), self.tr('属性')])
                tableView.setColumnWidth(0, 50)
                tableView.setColumnWidth(1, 175)
                tableView.setColumnWidth(2, 50)
                tableView.setColumnWidth(3, 175)
                for i in range(len(total_list)):
                    tableView.setItem(i // 4, i % 4, QTableWidgetItem(total_list[i]))
                tableView.setEditTriggers(tableView.NoEditTriggers)
                tableView.setSelectionBehavior(tableView.SelectRows)
                tableView.setSelectionMode(tableView.SingleSelection)
                tableView.setSortingEnabled(True)
                tableView.setAlternatingRowColors(True)
                tableView.setShowGrid(True)
                tableView.setGridStyle(Qt.SolidLine)
                tableView.setCornerButtonEnabled(True)
                tableView.setFixedHeight(200)
                self.vBoxLayout.addWidget(tableView)
                self.vBoxLayout.setContentsMargins(20, 0, 20, 20)

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
        current_event = self.config.static_config.current_game_activity[self.config.server_mode]
        if current_event is None:
            return None
        import json
        try:
            file_path = f"src/explore_task_data/activities/{current_event}.json"
            with open(file_path, "r") as f:
                stage_data = json.load(f)
        except FileNotFoundError:
            return None
        ret = dict(activity_name=current_event, story=dict(), mission=dict(), challenge=dict())
        en2cn = {
            "story": self.tr("故事"),
            "mission": self.tr("任务"),
            "challenge": self.tr("挑战"),
        }
        for key, value in stage_data.items():
            if key == "story" or key == "mission" or key == "challenge":
                for i in range(len(value)):
                    ret[key][en2cn[key] + str(i + 1)] = formation_attr_to_cn(value[i])
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
                name += self.tr("三星")
            if "task" in key:
                name += self.tr("成就任务")
            team = ""
            for s in value['start']:
                temp = bt.tr('ConfigTranslation', formation_attr_to_cn(s[0]))
                if temp is not None:
                    team += temp + " "
            if team.endswith(" "):
                team = team[:-1]
            ret[tp][name] = team
        return ret


def formation_attr_to_cn(attr):
    attrMap = {"burst": "爆发", "pierce": "贯穿", "mystic": "神秘", "shock": "振动"}
    if attr not in attrMap:
        return None
    return attrMap[attr]
