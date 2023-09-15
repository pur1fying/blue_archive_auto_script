import json

from main import Main


class Scheduler(Main):
    def __init__(self):
        super().__init__()
        self.runningPath = '../config/gui/config/running.json'
        with open(self.runningPath, 'r', encoding='utf-8') as f:
            self.status_board = json.load(f)
        # self.status_board[]





