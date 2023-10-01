import time
import numpy as np

from core.utils import get_x_y
from gui.util import log
from module import common_solve_affection_story_method


def implement(self):
    self.click(172, 275)
    time.sleep(0.5)
    self.latest_img_array = self.get_screen_shot_array()
    path1 = "src/momo_talk/unread_mode.png"
    path2 = "src/momo_talk/newest_mode.png"
    return_data1 = get_x_y(self.latest_img_array, path1)
    return_data2 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    print(return_data2)
    if return_data1[1][0] < 1e-03:
        log.d("unread mode", 1, logger_box=self.loggerBox)
    elif return_data2[1][0] < 1e-03:
        log.d("newest message mode", 1, logger_box=self.loggerBox)
        log.d("change to unread mode", 1, logger_box=self.loggerBox)
        self.click(514, 177)
        time.sleep(0.3)
        self.click(451, 297)
        time.sleep(0.3)
        self.click(451, 363)
        time.sleep(0.5)
    else:
        log.d("can't detect mode button quit momo_talk task", 2, logger_box=self.loggerBox)
        return

    while 1:
        self.latest_img_array = self.get_screen_shot_array()
        location_y = 210
        red_dot = np.array([25, 71, 251])
        location_x = 637
        dy = 18
        unread_location = []
        while location_y <= 630:
            if np.array_equal(self.latest_img_array[location_y][location_x], red_dot) and np.array_equal(
                    self.latest_img_array[location_y + dy][location_x], red_dot):
                unread_location.append([location_x, location_y + dy / 2])
                location_y += 60
            else:
                location_y += 1
        length = len(unread_location)
        log.d("find  " + str(length) + "  unread message", 1, logger_box=self.loggerBox)

        if length == 0:
            log.d("momo_talk task finished", 1, logger_box=self.loggerBox)
            self.main_activity[14][1] = True
            return
        else:
            for i in range(0, len(unread_location)):
                self.click(unread_location[i][0], unread_location[i][1])
                time.sleep(0.5)
                common_solve_affection_story_method.implement(self)
                time.sleep(2)
                fail_cnt = 0
                flag = False
                while fail_cnt <= 5:
                    if self.pd_pos("src/momo_talk/momo_talk2.png", "momo_talk2") != "momo_talk2":
                        self.click(629, 105)
                        fail_cnt += 1
                        time.sleep(2)
                    else:
                        flag = True
                        break
                if not flag:
                    return
        self.click(170, 197)
        time.sleep(0.5)
        self.click(170, 270)
        time.sleep(0.5)
