import time

from core.utils import get_x_y
from gui.util import log
from module import common_skip_plot_method


def implement(self):
    fail_cnt = 0
    while fail_cnt <= 5:
        path1 = "src/momo_talk/reply_button.png"
        path2 = "src/momo_talk/affection story.png"
        self.latest_img_array = self.get_screen_shot_array()
        return_data1 = get_x_y(self.latest_img_array, path1)
        return_data2 = get_x_y(self.latest_img_array, path2)
        print(return_data1)
        print(return_data2)
        if return_data2[1][0] <= 1e-03:
            log.d("enter affection story", 1, logger_box=self.loggerBox)
            self.click(return_data2[0][0] + 108, return_data2[0][1] + 45)
            time.sleep(0.5)
            self.click(925, 564)
            time.sleep(5)
            common_skip_plot_method.implement(self)
            return True
        elif return_data1[1][0] <= 1e-03:
            fail_cnt = 0
            log.d("reply_message", 1, logger_box=self.loggerBox)
            self.click(return_data1[0][0] + 166, return_data1[0][1] + 45)
            time.sleep(2)
        else:
            time.sleep(2)
            fail_cnt += 1
            log.d("can't find target button cnt = " + str(fail_cnt), 1, logger_box=self.loggerBox)
