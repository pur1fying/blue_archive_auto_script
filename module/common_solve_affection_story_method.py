import time

from core.utils import get_x_y
from gui.util import log
from module import common_skip_plot_method


def implement(self):
    fail_cnt = 0
    self.operation("swipe", [(924, 330), (924, 230)],duration = 0.1)
    self.operation("click", (924, 330))
    while fail_cnt <= 4:
        path1 = "src/momo_talk/reply_button.png"
        path2 = "src/momo_talk/affection story.png"
        self.latest_img_array = self.operation("get_screenshot_array")
        return_data1 = get_x_y(self.latest_img_array, path1)
        return_data2 = get_x_y(self.latest_img_array, path2)
        print(return_data1)
        print(return_data2)
        if return_data2[1][0] <= 1e-03:
            log.d("enter affection story", 1, logger_box=self.loggerBox)
            self.operation("click", (return_data2[0][0] + 166, return_data2[0][1] + 45), duration=0.7)
            self.operation("click", (925, 564), duration=6)
            common_skip_plot_method.implement(self)
            return True
        elif return_data1[1][0] <= 1e-03:
            fail_cnt = 0
            self.operation("click@reply_message", (return_data1[0][0] + 166, return_data1[0][1] + 45), duration=2)
        else:
            time.sleep(2)
            fail_cnt += 1
            log.d("can't find target button cnt = " + str(fail_cnt), 1, logger_box=self.loggerBox)
    log.d("current conversation concluded", 1, logger_box=self.loggerBox)
