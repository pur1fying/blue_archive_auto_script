from core.utils import get_x_y
from gui.util import log
from datetime import datetime

x = {
    'menu': (107, 9, 162, 36)
}
def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    hour = current_time.hour
    if hour < 16:
        next_time = datetime(year, month, day, 16)
    else:
        next_time = datetime(year, month, day+1, 4)
    return next_time.timestamp()


def implement(self):
    self.operation("stop_getting_screenshot_for_location")

    self.latest_img_array = self.operation("get_screenshot_array")
    path2 = "../src/mail/collect_all_bright.png"
    path3 = "../src/mail/collect_all_grey.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    return_data2 = get_x_y(self.latest_img_array, path3)
    print(return_data1)
    print(return_data2)
    if return_data2[1][0] <= 1e-03:
        log.d("mail reward has been collected", level=1, logger_box=self.loggerBox)
        self.operation("click", (1236, 39))
    elif return_data1[1][0] <= 1e-03:
        log.d("collect mail reward", level=1, logger_box=self.loggerBox)
        self.operation("click", (return_data1[0][0], return_data1[0][1]), duration=1.5)
        self.operation("click", (1236, 39),duration=0.5)
        self.operation("click", (1236, 39))
        self.operation("click", (1236, 39))

    else:
        log.d("Can't detect button", level=2, logger_box=self.loggerBox)
        self.operation("click", (1236, 39))
        return False

    self.main_activity[2][1] = 1
    log.d("mail task finished", level=1, logger_box=self.loggerBox)

    self.operation("start_getting_screenshot_for_location")
    return True

