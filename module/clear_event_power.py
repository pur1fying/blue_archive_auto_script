import time

from core.utils import get_x_y
from gui.util import log


def implement(self):
    
    if len(self.common_task_count) != 0 or len(self.self.hard_task_count) != 0:
        all_task_x_coordinate = 1118
        common_task_y_coordinates = [242, 342, 438, 538, 569, 469, 369, 269]
        hard_task_y_coordinates = [250, 360, 470]
        self.operation("click@event", (816, 267))
        left_change_page_x = 32
        right_change_page_x = 1247
        change_page_y = 360
        time.sleep(2)
        if len(self.common_task_count) != 0:
            log.line(self.loggerBox)
            log.d("common task begin", level=1, logger_box=self.loggerBox)
            log.d("change to common level", level=1, logger_box=self.loggerBox)

            if not self.operation("click@common_level", (682, 141), duration=0.5):
                return False
            self.common_icon_bug_detect_method("src/event/common_task.png", 682, 141, "common_task",times=6)

            for i in range(0, len(self.common_task_count)):
                cur_lo = self.operation("get_current_position",)
                log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
                if cur_lo[0:4] != "task":
                    log.d("incorrect page exit common task", level=3, logger_box=self.loggerBox)
                    break
                cur_num = int(cur_lo[5:])
                tar_num = self.common_task_count[i][0]
                tar_level = self.common_task_count[i][1]
                tar_times = self.common_task_count[i][2]
                log.d("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started",
                      level=1, logger_box=self.loggerBox)
                while cur_num != tar_num:
                    if cur_num > tar_num:
                        self.operation("click@change_to_left", (left_change_page_x, change_page_y))
                    else:
                        self.operation("click@change_to_right", (right_change_page_x, change_page_y))
                    cur_lo = self.operation("get_current_position",)
                    if cur_lo[0:4] != "task":
                        log.d("unexpected page exit task clear event power", level=3, logger_box=self.loggerBox)
                        return False
                    cur_num = int(cur_lo[5:])
                    log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)

                log.d("find target page " + cur_lo, level=1, logger_box=self.loggerBox)
                if tar_level >= 5:
                    page_task_numbers = [8, 6, 7]
                    self.operation("swipe", [(928, 560), (928, 0)], duration=0.2)
                    log.d("SWIPE UPWARD", level=1, logger_box=self.loggerBox)
                    time.sleep(1)
                    if tar_num < 4:
                        tar_level = page_task_numbers[tar_num - 1] + (5 - tar_level) - 1
                else:
                    tar_level -= 1

                self.operation("click", (all_task_x_coordinate, common_task_y_coordinates[tar_level]),duration=0.5)
                path = "src/event/auto clear bright.png"
                img = self.operation("get_screenshot_array")
                return_data = get_x_y(img, path)
                if not return_data[1][0] <= 1e-03:
                    log.d("unable to auto clear", level=4, logger_box=self.loggerBox)
                    self.operation("click@anywhere", (649,646))
                    continue
                for j in range(0, tar_times - 1):
                    self.operation("click@add", (1033, 297), duration=0.6)
                self.operation("click", (937, 404))
                if self.operation("get_current_position",) == "charge_power":
                    log.d("inadequate power , exit task", level=2, logger_box=self.loggerBox)
                    return True
                self.operation("click", (767, 504))
                if not self.common_positional_bug_detect_method("task_" + str(tar_num), 651, 663, times=10, anywhere=True):
                    return False
                log.d("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " finished",
                      level=1, logger_box=self.loggerBox)
                log.d("common task finished", level=1, logger_box=self.loggerBox)

        if len(self.hard_task_count) != 0:
            log.line(self.loggerBox)
            log.d("hard task begin", level=1, logger_box=self.loggerBox)

            log.d("change to HARD level", level=1, logger_box=self.loggerBox)

            self.operation("click", (1186, 141), duration=0.5)
            self.common_icon_bug_detect_method("src/event/hard_task.png", 1186, 141, "hard_task",times=6)

            for i in range(0, len(self.hard_task_count)):
                cur_lo = self.operation("get_current_position",)
                if cur_lo[0:4] != "task":
                    log.d("incorrect page exit common task", level=3, logger_box=self.loggerBox)
                    break
                cur_num = int(cur_lo[5:])
                log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
                tar_num = self.hard_task_count[i][0]
                tar_level = self.hard_task_count[i][1]
                tar_times = self.hard_task_count[i][2]
                log.d("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started",
                      level=1, logger_box=self.loggerBox)
                while cur_num != tar_num:
                    if cur_num > tar_num:
                        self.operation("click@change_to_left", (left_change_page_x, change_page_y))
                    else:
                        self.operation("click@change_to_left", (right_change_page_x, change_page_y))
                    cur_lo = self.operation("get_current_position",)
                    if cur_lo[0:4] != "task":
                        log.d("unexpected page exit task clear power", level=3, logger_box=self.loggerBox)
                        return False
                    cur_num = int(cur_lo[5:])
                    log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)

                log.d("find target page " + cur_lo, level=1, logger_box=self.loggerBox)
                tar_level -= 1

                self.operation("click", (all_task_x_coordinate, hard_task_y_coordinates[tar_level]),duration=0.5)
                path = "src/event/auto clear bright.png"
                img = self.operation("get_screenshot_array")
                return_data = get_x_y(img, path)
                if not return_data[1][0] <= 1e-03:
                    log.d("unable to auto clear", level=2, logger_box=self.loggerBox)
                    self.operation("click@anywhere", (649, 646))
                    continue
                for j in range(0, tar_times - 1):
                    self.operation("click@add", (1033,297))

                time.sleep(0.3)
                self.operation("click", (937, 404))
                lo = self.operation("get_current_position")
                if lo == "charge_power":
                    log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
                    return True

                self.hard_task_status[i] = True

                if lo == "charge_notice":
                    log.d("inadequate fight time available , Try next task", level=3, logger_box=self.loggerBox)
                    if not self.common_positional_bug_detect_method("task_" + str(tar_num), 651, 663, anywhere=True,
                                                                    times=8):
                        return False
                    continue
                if lo == "task_message":
                    log.d("current task AUTO FIGHT UNLOCKED , Try next task", level=2, logger_box=self.loggerBox)
                    if not self.common_positional_bug_detect_method("task_" + str(tar_num), 651, 663, anywhere=True,
                                                                    times=8):
                        return False
                    continue

                self.operation("click", (767, 504))

                if not self.common_positional_bug_detect_method("task_" + str(tar_num), 651, 663, anywhere=True, times=8):
                    return False

                log.d("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " finished",
                      level=1, logger_box=self.loggerBox)
            log.d("hard task finished", level=1, logger_box=self.loggerBox)

    self.main_activity[10][1] = 1
    log.d("clear event power task finished", level=1, logger_box=self.loggerBox)
    return True
