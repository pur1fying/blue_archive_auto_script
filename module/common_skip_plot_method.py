import time

from core.utils import get_x_y
from gui.util import log


def implement(self):
    fail_cnt = 0
    path = "src/skip_plot/skip_plot_button.png"
    while fail_cnt <= 7:
        self.latest_img_array = self.get_screen_shot_array()
        return_data = get_x_y(self.latest_img_array, path)
        print(return_data)
        if return_data[1][0] < 1e-03:
            log.d("find skip plot button", 1, logger_box=self.loggerBox)
            self.click(return_data[0][0], return_data[0][1])
            time.sleep(1)
            log.d("skip plot", 1, logger_box=self.loggerBox)
            self.click(766, 520)
            return True
        else:
            fail_cnt += 1
            log.d("can't find skip plot button, fail count: " + str(fail_cnt), 2, logger_box=self.loggerBox)
            self.click(1205, 37)
            time.sleep(1)
    log.d("skip plot fail", 3, logger_box=self.loggerBox)
