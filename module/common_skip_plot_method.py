import time

from core.utils import get_x_y,pd_rgb
from gui.util import log


def pd_menu_bright(img_array):
    if pd_rgb(img_array, 1165, 45, 230, 255, 230, 255, 230, 255) and pd_rgb(img_array, 1238, 45, 230, 255, 230, 255, 230, 255):
        return True
    return False


def pd_skip_plot_button(img_array):
    if pd_rgb(img_array, 1189, 120, 30, 50, 55, 75, 90, 110) and pd_rgb(img_array, 1128, 104, 30, 50, 55, 75, 90, 110) and pd_rgb(img_array, 1125, 120, 245, 255, 245, 255, 245, 255) and pd_rgb(img_array, 1207, 120, 245, 255, 245, 255, 245, 255):
        return True
    return False


def pd_confirm_button(img_array):
    if pd_rgb(img_array, 709, 525, 110, 130, 210, 230, 245, 255) and pd_rgb(img_array, 826, 525, 110, 130, 210, 230, 245, 255) and pd_rgb(img_array, 770, 545, 110, 130, 210, 230, 245, 255):
        return True
    return False


def implement(self):
    fail_cnt = 0
    while fail_cnt <= 20:
        self.latest_img_array = self.operation("get_screenshot_array")
        if pd_confirm_button(self.latest_img_array):
            # print("A")
            log.d("find CONFIRM button", 1, logger_box=self.loggerBox)
            self.operation("click@confirm", (766, 520))
            return True
        else:
            fail_cnt += 1
            if pd_menu_bright(self.latest_img_array):
                # print("B")
                log.d("find MENU button", 2, logger_box=self.loggerBox)
                self.operation("click@menu", (1205, 34))
            elif pd_skip_plot_button(self.latest_img_array):
                # print("C")
                log.d("find SKIP PLOT button", 1, logger_box=self.loggerBox)
                self.operation("click@skip_plot", (1213, 116))
            # print("D")
            log.d("Didn't find confirm button, fail count: " + str(fail_cnt), 2, logger_box=self.loggerBox)
        time.sleep(1)
    log.d("skip plot fail", 3, logger_box=self.loggerBox)
    return False
