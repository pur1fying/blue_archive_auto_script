import time
import numpy as np

from core.utils import get_x_y
from gui.util import log
from module import common_solve_affection_story_method


def implement(self):
    self.common_positional_bug_detect_method("main_page", 1236, 39, times=7, anywhere=True,path="src/momo_talk/momo_talk2.png", name="momo_talk2")

    self.operation("click", (172, 150),duration = 1.5)
    self.common_icon_bug_detect_method("src/momo_talk/momo_talk1.png", 170, 150,"momotalk1", times=5)
    self.operation("click", (172, 275),duration =0.2
                   )
    self.latest_img_array = self.operation("get_screenshot_array")
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
        self.operation("click", (514, 177), duration=0.3)
        self.operation("click", (451, 297), duration=0.3)
        self.operation("click", (514, 363), duration=0.5)
    else:
        log.d("can't detect mode button quit momo_talk task", 2, logger_box=self.loggerBox)
        return

    main_to_momotalk = True
    while 1:
        self.latest_img_array = self.operation("get_screenshot_array")
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
            if main_to_momotalk:
                log.d("momo_talk task finished", 1, logger_box=self.loggerBox)
                self.main_activity[14][1] = 1
                return True
            else:
                time.sleep(0.5)
                log.d("restart momo_talk task", 1, logger_box=self.loggerBox)
                self.operation("click", (1236, 39),duration = 0.2)
                return implement(self)
        else:
            for i in range(0, len(unread_location)):
                self.operation("click", (unread_location[i][0], unread_location[i][1]),duration = 0.5)
                common_solve_affection_story_method.implement(self)
                time.sleep(2)
                if not self.common_positional_bug_detect_method("momo_talk2", 664, 114, times=4, anywhere=True,
                                                                path="src/momo_talk/momo_talk2.png", name="momo_talk2"):
                    return False

        main_to_momotalk = False
        self.operation("click", (170, 197), duration=0.2)
        self.operation("click", (170, 270), duration=0.2)
