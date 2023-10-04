import threading
import time

from core.utils import get_x_y
from gui.util import log


def implement(self):
    self.latest_img_array = self.get_screen_shot_array()
    path2 = "../src/arena/collect_reward.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    if return_data1[1][0] <= 1e-03:
        log.d("collect arena first reward", level=1, logger_box=self.loggerBox)
        self.click(return_data1[0][0], return_data1[0][1])
        time.sleep(2)
        self.click(666, 672)
        time.sleep(0.5)
    else:
        log.d("arena first reward has been collected", level=1, logger_box=self.loggerBox)

    self.latest_img_array = self.get_screen_shot_array()
    path2 = "../src/arena/collect_reward1.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    if return_data1[1][0] <= 1e-03:
        log.d("collect arena second reward", level=1, logger_box=self.loggerBox)
        self.click(return_data1[0][0], return_data1[0][1])
        log.d("Click :(" + str(return_data1[0][0]) + " " + str(
            return_data1[0][1]) + ")" + " click_time = " + str(self.click_time), level=1,
              logger_box=self.loggerBox)
        time.sleep(2)
        self.click(666, 672)
        time.sleep(0.5)
    else:
        log.d("arena second reward has been collected", level=1, logger_box=self.loggerBox)

    choice = 1
    x = 844
    y = [261, 414, 581]
    y = y[choice - 1]
    f_skip = False

    for i in range(0, 5):
        self.connection.click(x, y)
        time.sleep(1)
        self.connection.click(638, 569)
        lo = self.pd_pos()
        if lo == "notice":
            self.main_activity[9][1] = 1
            log.d("task arena finished", level=1, logger_box=self.loggerBox)
            return True
        elif lo == "attack_formation":
            if not f_skip:
                self.latest_img_array = self.get_screen_shot_array()
                path2 = "../src/arena/skip.png"
                return_data1 = get_x_y(self.latest_img_array, path2)
                if return_data1[1][0] <= 1e-03:
                    log.d("skip choice ON", level=1, logger_box=self.loggerBox)
                else:
                    log.d("skip choice OFF , TURN ON skip choice", level=1, logger_box=self.loggerBox)
                    self.connection.click(1122, 602)
                    time.sleep(0.3)
                f_skip = True

            self.connection.click(1169, 670)
            if not self.common_positional_bug_detect_method("arena", 1169, 670, times=10, anywhere=True):
                return False
            if i == 4:
                return True
            self.flag_run = False
            time.sleep(53)
            log.d("WAIT 53 SECONDS...", level=1, logger_box=self.loggerBox)
            threading.Thread(target=self.run).start()

