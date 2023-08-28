import os
import time

import uiautomator2 as u2

import log
from definemytime import return_current_time
from utils import get_x_y


class Operation:
    def __init__(self):
        self.device = u2.connect()

    def get_screen_shot_path(self, sleep_time=2):
        time.sleep(sleep_time)
        screenshot = self.device.screenshot()
        time.sleep(sleep_time)
        save_folder = "logs"
        t = return_current_time()
        file_name = t + ".png"
        save_path = os.path.join(save_folder, file_name)
        screenshot.save(save_path)
        return save_path

    def clicker(self, path1, add_x=0, add_y=0):
        shot_path = self.get_screen_shot_path()
        lo = get_x_y(shot_path, path1)
        log.o_p("click(" + str(lo[0]) + "," + str(lo[1]) + ")", 1)
        self.device.click(lo[0] + add_x, lo[1] + add_y)
