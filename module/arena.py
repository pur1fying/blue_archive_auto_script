import threading
import time

from core.utils import get_x_y
from gui.util import log


def implement(self):
    self.latest_img_array = self.operation("get_screenshot_array")
    path2 = "../src/arena/collect_reward.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    if return_data1[1][0] <= 1e-03:
        log.d("collect arena first reward", level=1, logger_box=self.loggerBox)
        self.operation("click@collect_reward1", (return_data1[0][0], return_data1[0][1]),duration=2)
        self.operation("click@anywhere", (666, 672),duration=0.5)
    else:
        log.d("arena first reward has been collected", level=1, logger_box=self.loggerBox)

    self.latest_img_array = self.operation("get_screenshot_array")
    path2 = "../src/arena/collect_reward1.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    if return_data1[1][0] <= 1e-03:
        log.d("collect arena second reward", level=1, logger_box=self.loggerBox)
        self.operation("click@collect_reward2", (return_data1[0][0], return_data1[0][1]),duration=2)
        self.operation("click@anywhere", (666, 672), duration=0.5)
    else:
        log.d("arena second reward has been collected", level=1, logger_box=self.loggerBox)

    choice = 1  # ** 总力战打第choice个对手
    x = 844
    y = [261, 414, 581]
    y = y[choice - 1]
    f_skip = False

    for i in range(0, 5):
        print(i)
        self.operation("click", (x, y), duration=1)
        self.operation("click", (638, 569),duration = self.screen_shot_interval * 2)

        lo = self.operation("get_current_position",)
        if lo == "notice": #没券了
            self.main_activity[9][1] = 1
            log.d("INADEQUATE TICKET", level=1, logger_box=self.loggerBox)
            self.operation("click", (1240, 39))
            self.operation("click", (1240, 39))
            self.operation("click", (1240, 39))
            return True
        elif lo == "attack_formation":
            if not f_skip:
                self.latest_img_array = self.operation("get_screenshot_array")
                path2 = "../src/arena/skip.png"
                return_data1 = get_x_y(self.latest_img_array, path2)
                if return_data1[1][0] <= 1e-03:
                    log.d("skip choice ON", level=1, logger_box=self.loggerBox)
                else:
                    log.d("skip choice OFF , TURN ON skip choice", level=1, logger_box=self.loggerBox)
                    self.operation("click", (1122, 602),duration=0.3)
                f_skip = True

            self.operation("click", (1169, 670), duration=1)
            self.operation("click", (1169, 670), duration=1)
            self.operation("click", (1169, 700), duration= self.screen_shot_interval * 2)
            if not self.common_positional_bug_detect_method("arena", 1169, 670, times=10, anywhere=True):
                return False
            if i == 4:
                log.d("FINISH 5 COMBAT,exit arena", level=1, logger_box=self.loggerBox)
                return True

            self.operation("stop_getting_screenshot_for_location")
            log.d("WAIT 53 SECONDS FOR THE NEXT COMBAT", level=1, logger_box=self.loggerBox)
            time.sleep(53)
            self.operation("start_getting_screenshot_for_location")