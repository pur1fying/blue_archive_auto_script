import json
import os

from main import Main
import time


class Scheduler(Main):
    def __init__(self):
        super().__init__()
        self.runningPath = '../gui/config/running.json'
        with open(self.runningPath, 'r', encoding='utf-8') as f:
            self.status_board = json.load(f)

    def start_schedule(self):
        cur_time = int(time.time())
        if self.status_board['running']['name'] != 'empty':
            self.status_board['running'] = cur_time
        # if cur_time > self.status_board['running']:
        #     self



if __name__ == '__main__':
    # print(os.getcwd())
    # Scheduler()
    print(time.time())
