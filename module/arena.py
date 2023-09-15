import time

from core.utils import get_screen_shot_array, get_x_y
from gui.util import log
import uiautomator2 as u2


def implement(self):
    img_shot = get_screen_shot_array()
    path2 = "src/arena/collect_reward.png"
    return_data1 = get_x_y(img_shot, path2)
    print(return_data1)
    if return_data1[1][0] <= 1e-03:
        log.d("collect reward", level=1, logger_box=self.loggerBox)
        self.click(return_data1[0][0], return_data1[0][1])
        log.d("Click :(" + str(return_data1[0][0]) + " " + str(
            return_data1[0][1]) + ")" + " click_time = " + str(self.click_time), level=1,
              logger_box=self.loggerBox)
        time.sleep(2)
        self.click(666, 672)
        time.sleep(0.5)
    else:
        log.d("reward collected", level=1, logger_box=self.loggerBox)
    img_shot = get_screen_shot_array()
    path2 = "src/arena/collect_reward1.png"
    return_data1 = get_x_y(img_shot, path2)
    print(return_data1)
    if return_data1[1][0] <= 1e-03:
        log.d("collect reward", level=1, logger_box=self.loggerBox)
        self.click(return_data1[0][0], return_data1[0][1])
        log.d("Click :(" + str(return_data1[0][0]) + " " + str(
            return_data1[0][1]) + ")" + " click_time = " + str(self.click_time), level=1,
              logger_box=self.loggerBox)
        time.sleep(2)
        self.click(666, 672)
        time.sleep(0.5)
    else:
        log.d("reward collected", level=1, logger_box=self.loggerBox)
    choice = 1
    x = 844
    y = [261, 414, 581]
    y = y[choice - 1]
    f_skip = False

    while 1:
        u2.connect().click(x, y)
        time.sleep(1)
        u2.connect().click(638, 569)
        lo = self.pd_pos()
        while lo != "notice" and lo != "attack_formation":
            lo = self.pd_pos()
        if lo == "notice":
            self.main_activity[9][1] = 1
            log.d("task arena finished", level=1, logger_box=self.loggerBox)
            return
        elif lo == "attack_formation":
            if not f_skip:
                img_shot = get_screen_shot_array()
                path2 = "src/arena/skip.png"
                return_data1 = get_x_y(img_shot, path2)
                print(return_data1)
                if return_data1[1][0] <= 1e-03:
                    log.d("skip choice on", level=1, logger_box=self.loggerBox)
                else:
                    log.d("skip choice off , turn on skip choice", level=1, logger_box=self.loggerBox)
                    u2.connect().click(1122, 602)
                    time.sleep(0.1)
                f_skip = True
        time.sleep(0.5)
        u2.connect().click(1169, 670)
        if self.pd_pos() == "notice":
            time.sleep(2)
            u2.connect().click(1169, 670)
        while self.pd_pos() != "arena":
            u2.connect().click(666, 555)

        time.sleep(45)
