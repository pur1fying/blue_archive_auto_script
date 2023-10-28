import time

from core.utils import get_x_y
from gui.util import log


def implement(self, activity="collect_daily_power"):
    while 1:
        path1 = self.operation("get_screenshot_array")
        path2 = "../src/daily_task/daily_task_collect_all_bright.png"
        path3 = "../src/daily_task/daily_task_collect_all_grey.png"
        return_data1 = get_x_y(path1, path2)
        return_data2 = get_x_y(path1, path3)
        print(return_data1)
        print(return_data2)
        if return_data2[1][0] <= 1e-03:
            log.d("work reward has been collected", level=1, logger_box=self.loggerBox)
            self.operation("click@home", (1240, 29))
            break
        elif return_data1[1][0] <= 1e-03:
            log.d("collect work task reward", level=1, logger_box=self.loggerBox)
            self.operation("click@collect_all", (return_data1[0][0], return_data1[0][1]), duration=2)
            self.operation("click@anywhere", (217, 63), duration=0.5)
            self.operation("click@anywhere", (217, 63))
            if not self.common_positional_bug_detect_method("work_task", 217, 63):
                return False
        else:
            log.d("Can't detect button", level=2, logger_box=self.loggerBox)
            return False

    if activity == "collect_daily_power":
        self.main_activity[3][1] = 1
        log.d("collect daily power task finished", level=1, logger_box=self.loggerBox)
    else:
        self.main_activity[13][1] = 1
        log.d("collect reward task finished", level=1, logger_box=self.loggerBox)
    return True
