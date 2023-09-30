import time
import uiautomator2 as u2
from gui.util import log


def implement(self):
    common_task_count = [(7, 1, 6)]  # 可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(普通)打k次
    hard_task_count = [(4, 3, 1)]  # 可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(困难)打k次

    if len(common_task_count) != 0 or len(hard_task_count) != 0:
        all_task_x_coordinate = 1118
        common_task_y_coordinates = [242, 342, 438, 538, 569, 469, 369, 269]
        hard_task_y_coordinates = [250, 360, 470]
        self.click(816, 267)
        left_change_page_x = 32
        right_change_page_x = 1247
        change_page_y = 360
        time.sleep(2)
        if len(common_task_count) != 0:
            log.line(self.loggerBox)
            log.d("common task begin", level=1, logger_box=self.loggerBox)
            log.d("change to common level", level=1, logger_box=self.loggerBox)
            self.click(800, 150)
            time.sleep(0.1)
            for i in range(0, len(common_task_count)):
                cur_lo = self.pd_pos()
                log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
                if cur_lo[0:4] != "task":
                    log.d("incorrect page exit common task", level=3, logger_box=self.loggerBox)
                    break
                cur_num = int(cur_lo[5:])
                tar_num = common_task_count[i][0]
                tar_level = common_task_count[i][1]
                tar_times = common_task_count[i][2]
                log.d("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started",
                      level=1, logger_box=self.loggerBox)
                while cur_num != tar_num:
                    if cur_num > tar_num:
                        self.click(left_change_page_x, change_page_y)
                    else:
                        self.click(right_change_page_x, change_page_y)
                    cur_lo = self.pd_pos()
                    if cur_lo[0:4] != "task":
                        log.d("incorrect page exit task clear event power", level=3, logger_box=self.loggerBox)
                        return
                    cur_num = int(cur_lo[5:])
                    log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)

                log.d("find target page " + cur_lo, level=1, logger_box=self.loggerBox)
                if tar_level >= 5:
                    page_task_numbers = [8, 6, 7]
                    self.connection.swipe(928, 560, 928, 0, 0.5)
                    log.d("SWIPE", level=1, logger_box=self.loggerBox)
                    time.sleep(0.5)
                    if tar_num < 4:
                        tar_level = page_task_numbers[tar_num - 1] + (5 - tar_level) - 1
                else:
                    tar_level -= 1
                self.click(all_task_x_coordinate, common_task_y_coordinates[tar_level])
                time.sleep(0.5)
                for j in range(0, tar_times - 1):
                    self.click(1033, 297)
                    time.sleep(0.6)
                self.click(937, 404)
                if self.pd_pos() == "charge_power":
                    log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
                    return
                self.click(767, 501)
                while 1:
                    if not self.pd_pos() == "task_" + str(tar_num):
                        for j in range(0, 4):
                            self.connection.click(651, 663)
                            self.click_time = time.time() - self.base_time
                            time.sleep(0.1)
                    else:
                        break
                log.d("task finished", level=1, logger_box=self.loggerBox)
            log.d("common task finished", level=1, logger_box=self.loggerBox)

        if len(hard_task_count) != 0:
            log.line(self.loggerBox)
            log.d("hard task begin", level=1, logger_box=self.loggerBox)

            log.d("change to hard level", level=1, logger_box=self.loggerBox)
            self.connection.click(1065, 150)
            time.sleep(0.1)

            for i in range(0, len(hard_task_count)):
                cur_lo = self.pd_pos()
                if cur_lo[0:4] != "task":
                    log.d("incorrect page exit common task", level=3, logger_box=self.loggerBox)
                    break
                cur_num = int(cur_lo[5:])
                log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
                tar_num = hard_task_count[i][0]
                tar_level = hard_task_count[i][1]
                tar_times = hard_task_count[i][2]
                log.d("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started",
                      level=1, logger_box=self.loggerBox)
                while cur_num != tar_num:
                    if cur_num > tar_num:
                        self.connection.click(left_change_page_x, change_page_y)
                        self.set_click_time()
                        log.d("Click :(" + str(left_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), level=1,
                              logger_box=self.loggerBox)
                    else:
                        self.connection.click(right_change_page_x, change_page_y)
                        self.set_click_time()
                        log.d("Click :(" + str(right_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), level=1,
                              logger_box=self.loggerBox)
                    cur_lo = self.pd_pos()
                    if cur_lo[0:4] != "task":
                        log.d("incorrect page exit task clear power", level=3, logger_box=self.loggerBox)
                        return
                    cur_num = int(cur_lo[5:])
                    log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)

                log.d("find target page " + cur_lo, level=1, logger_box=self.loggerBox)
                tar_level -= 1

                self.connection.click(all_task_x_coordinate, hard_task_y_coordinates[tar_level])
                self.set_click_time()
                log.d("Click :(" + str(all_task_x_coordinate) + " " + str(
                    hard_task_y_coordinates[tar_level]) + ")" + " click_time = " + str(self.click_time),
                      level=1, logger_box=self.loggerBox)
                time.sleep(0.5)
                for j in range(0, tar_times - 1):
                    self.connection.click(1033, 297)
                    time.sleep(0.6)
                self.connection.click(937, 404)
                self.set_click_time()
                lo = self.pd_pos()
                if lo == "charge_power":
                    log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
                    break
                if lo == "charge_notice":
                    log.d("inadequate fight time available", level=3, logger_box=self.loggerBox)
                    break
                self.click(767, 501)
                while 1:
                    lo = self.pd_pos()
                    if lo != "task_" + str(tar_num):
                        for j in range(0, 4):
                            self.connection.click(651, 663)
                            self.set_click_time()
                            time.sleep(0.1)
                    else:
                        break
                log.d("task finished", level=1, logger_box=self.loggerBox)
            log.d("hard task finished", level=1, logger_box=self.loggerBox)
    self.main_activity[10][1] = 1
    log.d("clear event power task finished", level=1, logger_box=self.loggerBox)
