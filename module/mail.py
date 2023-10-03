import time

from core.utils import get_x_y
from gui.util import log


def implement(self):
    self.latest_img_array = self.get_screen_shot_array()
    path2 = "../src/mail/collect_all_bright.png"
    path3 = "../src/mail/collect_all_grey.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    return_data2 = get_x_y(self.latest_img_array, path3)
    print(return_data1)
    print(return_data2)
    if return_data2[1][0] <= 1e-03:
        log.d("mail reward has been collected", level=1, logger_box=self.loggerBox)
    elif return_data1[1][0] <= 1e-03:
        log.d("collect mail reward", level=1, logger_box=self.loggerBox)
        self.click(return_data1[0][0], return_data1[0][1])
    else:
        log.d("Can't detect button", level=2, logger_box=self.loggerBox)
        return False

    self.main_activity[2][1] = 1
    log.d("mail task finished", level=1, logger_box=self.loggerBox)
    return True

