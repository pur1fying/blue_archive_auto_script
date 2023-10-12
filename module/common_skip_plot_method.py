import time

from core.utils import get_x_y
from gui.util import log


def implement(self):
    fail_cnt = 0
    self.operation("click", (1205, 37), duration=0.7)
    path = "src/common_button/skip_plot_button.png"
    while fail_cnt <= 7:
        self.latest_img_array = self.operation("get_screenshot_array")
        return_data = get_x_y(self.latest_img_array, path)
        print(return_data)
        if return_data[1][0] < 1e-03:
            log.d("find skip plot button", 1, logger_box=self.loggerBox)
            self.operation("click", (return_data[0][0], return_data[0][1]), duration=1)
            log.d("skip plot", 1, logger_box=self.loggerBox)
            self.operation("click", (766, 520))
            return True
        else:
            fail_cnt += 1
            log.d("can't find skip plot button, fail count: " + str(fail_cnt), 2, logger_box=self.loggerBox)
            self.operation("click", (1205, 37), duration=0.7)

    log.d("skip plot fail", 3, logger_box=self.loggerBox)
