import log
from get_location import locate
import threading
import time
import os


class baas(locate):
    def __init__(self):
        super().__init__()
        self.main_activity = ["group", "mail", "collect_daily_power", "shop", "clear_power", "schedule", "cafe",
                              "create", "combat_power_fight", "arena", "rewarded_task", "collect_reward"]

        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]

        self.main_activity[0][1] = 1
        self.main_activity[1][1] = 1
        # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.package_name = 'com.RoamingStar.BlueArchive'
        self.exit_loop = False
        self.unknown_ui_page_count = 0
        self.pos = []
        self.base_time = 0.0
        self.alas_pause = False
        self.click_time = 0.0

    def start_ba(self):
        self.device.app_start(self.package_name)
        t = self.device.window_size()
        log.o_p("Screen Size  " + str(t), 1)
        if t[0] == 1280 and t[1] == 720:
            log.o_p("Screen Size Fitted", 1)
        else:
            log.o_p("Screen Size unfitted", 3)

    def worker(self):
        shot_time = time.time() - self.base_time
        path = self.get_screen_shot_path()

        self.get_keyword_appear_time(self.img_ocr(path))
        locate_res = self.return_location()
        ct = time.time()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, ct - self.base_time, path[5:]])
        if len(self.pos) > 2:
            self.pos.pop()
        print(self.pos)

    def run(self):
        self.base_time = time.time()
        while 1:
            if self.exit_loop:
                break
            threading.Thread(target=self.worker).start()
            time.sleep(1)

    def thread_starter(self):
        thread_run = threading.Thread(target=self.run)
        thread_run.start()
        for i in range(0, len(self.main_activity)):
            print(self.main_activity[i][0], self.main_activity[i][1])
            while self.main_activity[i][1] == 0:
                self.to_main_page()
                self.solve(self.main_activity[i][0])

    def pd_pos(self):
        while 1:
            if len(self.pos) == 2 and self.pos[0][0] == self.pos[1][0]:
                lo = self.pos[0][0]
                self.pos.clear()
                if lo == "UNKNOWN UI PAGE" and self.unknown_ui_page_count < 5:
                    self.unknown_ui_page_count += 1
                    log.o_p("UNKNOWN UI PAGE COUNT:" + str(self.unknown_ui_page_count), 2)
                elif lo == "UNKNOWN UI PAGE" and self.unknown_ui_page_count == 5:
                    log.o_p("current_location :" + str(lo), 3)
                else:
                    self.unknown_ui_page_count = 0
                    log.o_p("current_location : " + lo, 1)
                    return lo
            time.sleep(0.5)

    def solve(self, activity):
        self.to_main_page()
        if activity == "group":
            log.o_p("begin Group task", 1)
            to_group = [[580], [650], ["group"]]
            x = to_group[0][0]
            y = to_group[1][0]
            self.device.click(x, y)
            self.click_time = time.time() - self.base_time
            step = len(to_group[0])
            log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
            for i in range(0, step):
                page = to_group[2][i]
                lo = self.pd_pos()
                if lo == "-group":
                    log.o_p("Not in a group please get in a group", 2)
                    self.main_activity[0][1] = 1
                    self.to_main_page()
                elif lo == "group reward power" or lo == "group":
                    self.to_main_page()
                    self.main_activity[0][1] = 1
                    log.o_p("Group task finished", 1)
                elif lo != page:
                    log.o_p("Not in page:" + str(page) + " begin return to main_page", 2)
                    self.to_main_page()
                    log.o_p("Restart group task", 1)
                    self.device.click(x, y)
                    self.click_time = time.time() - self.base_time
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                    i = -1
                if i+1 < step:
                    self.device.click(x, y)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")", 1)
                    self.click_time = time.time() - self.base_time

        elif activity == "mail":
            log.o_p("begin Mail task", 1)
            to_mail = [[1140], [42], ["mail"]]
            x = to_mail[0][0]
            y = to_mail[1][0]
            self.device.click(x, y)
            self.click_time = time.time() - self.base_time
            step = len(to_mail[0])
            log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
            for i in range(0, step):
                page = to_mail[2][i]
                lo = self.pd_pos()
                if lo != page:
                    log.o_p("Not in page:" + str(page) + " begin return to main_page", 2)
                    self.to_main_page()
                    log.o_p("Restart mail task", 1)
                    self.device.click(x, y)
                    self.click_time = time.time() - self.base_time
                    i = -1
                if i+1 < step:
                    self.device.click(x, y)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                    self.click_time = time.time() - self.base_time

            path1 = self.get_screen_shot_path()
            path2 = "src/mail/collect_all_bright.png"
            path3 = "src/mail/collect_all_grey.png"
            return_data1 = self.get_x_y(path1, path2)
            return_data2 = self.get_x_y(path1, path3)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 0.001:
                self.main_activity[1][1] = 1
                log.o_p("mail reward has been collected", 1)
                self.to_main_page()
                log.o_p("mail task finished", 1)
            elif return_data1[1][0] <= 0.01:
                log.o_p("collect mail reward", 1)
                self.device.click(return_data1[0][0], return_data1[0][1])
                self.click_time = time.time() - self.base_time
                lo = self.pd_pos()
                if lo == "click_forward":
                    self.main_activity[1][1] = 1
                    self.to_main_page()
                    log.o_p("mail task finished", 1)
                else:
                    log.o_p("Can't detect button", 2)

        elif activity == "collect_daily_power":
            log.o_p("begin collect daily power task", 1)
            to_work_task = [[64], [233], ["work_task"]]
            x = to_work_task[0][0]
            y = to_work_task[1][0]
            self.device.click(x, y)
            self.click_time = time.time() - self.base_time
            step = len(to_work_task[0])
            log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
            for i in range(0, step):
                page = to_work_task[2][i]
                lo = self.pd_pos()
                if lo != page:
                    log.o_p("Not in page:" + str(page) + " begin return to main_page", 2)
                    self.to_main_page()
                    log.o_p("Restart to work task", 1)
                    self.device.click(x, y)
                    self.click_time = time.time() - self.base_time
                    i = -1
                if i + 1 < step:
                    self.device.click(x, y)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                    self.click_time = time.time() - self.base_time

            path1 = self.get_screen_shot_path()
            path2 = "src/mail/collect_all_bright.png"
            path3 = "src/mail/collect_all_grey.png"
            return_data1 = self.get_x_y(path1, path2)
            return_data2 = self.get_x_y(path1, path3)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 0.001:
                self.main_activity[1][1] = 1
                log.o_p("mail reward has been collected", 1)
                self.to_main_page()
                log.o_p("mail task finished", 1)
            elif return_data1[1][0] <= 0.01:
                log.o_p("collect mail reward", 1)
                self.device.click(return_data1[0][0], return_data1[0][1])
                self.click_time = time.time() - self.base_time
                lo = self.pd_pos()
                if lo == "click_forward":
                    self.main_activity[1][1] = 1
                    self.to_main_page()
                    log.o_p("mail task finished", 1)
                else:
                    log.o_p("Can't detect button", 2)




        elif activity == "clear_power":
            log.o_p("begin task clear_power", 1)

            common_task_count = [(2, 5, 1), (7, 1, 1)]
            hard_task_count = [(4, 3, 1)]

            all_task_x_coordinate = 1118
            common_task_y_coordinates = [242, 342, 438, 538, 569, 469, 369, 269]
            hard_task_y_coordinates = [250, 360, 470]

            to_common_task = [[1159], [568], ["business_area"]]

            x = to_common_task[0][0]
            y = to_common_task[1][0]

            self.device.click(x, y)
            self.click_time = time.time() - self.base_time
            log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
            step = len(to_common_task[0])
            for i in range(0, step):
                page = to_common_task[2][i]
                lo = self.pd_pos()
                if lo != page:
                    log.o_p("Not in page:" + str(page) + " begin return to main_page", 2)
                    self.to_main_page()
                    log.o_p("Restart clear energy task", 1)
                    self.device.click(x, y)
                    self.click_time = time.time() - self.base_time
                    i = -1
                if i + 1 < step:
                    self.device.click(x, y)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")", 1)
                    self.click_time = time.time() - self.base_time

            x = 816
            y = 267
            self.device.click(x, y)
            self.click_time = time.time() - self.base_time
            left_change_page_x = 32
            right_change_page_x = 1247
            change_page_y = 360
            log.o_p("Click :(" + str(x) + " " + str(y) + ")" + "click_time = " + str(self.click_time), 1)
            if len(common_task_count) != 0:
                log.o_p("common task begin", 1)
                cur_lo = self.pd_pos()
                cur_num = int(cur_lo[5:])
                self.device.click(800, 150)
                time.sleep(0.1)
                log.o_p("change to common level", 1)
                log.o_p("now in page task_" + cur_lo, 1)
                for i in range(0, len(common_task_count)):
                    tar_num = common_task_count[i][0]
                    tar_level = common_task_count[i][1]
                    tar_times = common_task_count[i][2]
                    log.o_p("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started", 1)
                    while cur_num != tar_num:
                        if cur_num > tar_num:
                            self.device.click(left_change_page_x, change_page_y)
                            self.click_time = time.time() - self.base_time
                            log.o_p("Click :(" + str(left_change_page_x) + " " + str(
                                change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                        else:
                            self.device.click(right_change_page_x, change_page_y)
                            self.click_time = time.time() - self.base_time
                            log.o_p("Click :(" + str(right_change_page_x) + " " + str(
                                change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                        cur_lo = self.pd_pos()
                        cur_num = int(cur_lo[5:])
                        log.o_p("now in page task_" + cur_lo, 1)

                    log.o_p("find target page task " + cur_lo, 1)
                    if tar_level >= 5:
                        page_task_numbers = [8, 6, 7]
                        self.device.swipe(928, 560, 928, 0, 0.5)
                        log.o_p("SWIPE", 1)
                        time.sleep(0.5)
                        if tar_num < 4:
                            tar_level = page_task_numbers[tar_num - 1] + (5 - tar_level) - 1
                    else:
                        tar_level -= 1
                    self.device.click(all_task_x_coordinate, common_task_y_coordinates[tar_level])
                    self.click_time = time.time() - self.base_time
                    log.o_p("Click :(" + str(all_task_x_coordinate) + " " + str(
                        common_task_y_coordinates[tar_level]) + ")" + " click_time = " + str(self.click_time), 1)
                    time.sleep(0.5)
                    for j in range(0, tar_times - 1):
                        self.device.click(1033, 297)
                        time.sleep(0.5)
                    self.device.click(937, 404)
                    self.click_time = time.time() - self.base_time
                    time.sleep(0.5)
                    self.device.click(767, 501)
                    self.click_time = time.time() - self.base_time
                    while 1:
                        if not self.pd_pos() == "task_finish":
                            time.sleep(0.1)
                        else:
                            break
                    log.o_p("task finished", 1)
                    for j in range(0, 2):
                        self.device.click(60, 40)
                        self.click_time = time.time() - self.base_time
                        time.sleep(0.1)
                log.o_p("common task finished", 1)

        if len(hard_task_count) != 0:
            log.o_p("hard task begin", 1)
            cur_lo = self.pd_pos()
            cur_num = int(cur_lo[5:])
            self.device.click(1065, 150)
            time.sleep(0.1)
            log.o_p("change to hard level", 1)
            log.o_p("now in page task_" + cur_lo, 1)
            for i in range(0, len(hard_task_count)):
                tar_num = hard_task_count[i][0]
                tar_level = hard_task_count[i][1]
                tar_times = hard_task_count[i][2]
                log.o_p("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started", 1)
                while cur_num != tar_num:
                    if cur_num > tar_num:
                        self.device.click(left_change_page_x, change_page_y)
                        self.click_time = time.time() - self.base_time
                        log.o_p("Click :(" + str(left_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                    else:
                        self.device.click(right_change_page_x, change_page_y)
                        self.click_time = time.time() - self.base_time
                        log.o_p("Click :(" + str(right_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                    cur_lo = self.pd_pos()
                    cur_num = int(cur_lo[5:])
                    log.o_p("now in page task_" + cur_lo, 1)

                log.o_p("find target page task " + cur_lo, 1)
                tar_level -= 1

                self.device.click(all_task_x_coordinate, hard_task_y_coordinates[tar_level])
                self.click_time = time.time() - self.base_time
                log.o_p("Click :(" + str(all_task_x_coordinate) + " " + str(
                    hard_task_y_coordinates[tar_level]) + ")" + " click_time = " + str(self.click_time), 1)
                time.sleep(0.5)
                for j in range(0, tar_times - 1):
                    self.device.click(1033, 297)
                    time.sleep(0.5)
                self.device.click(937, 404)
                self.click_time = time.time() - self.base_time
                time.sleep(0.5)
                self.device.click(767, 501)
                self.click_time = time.time() - self.base_time
                while 1:
                    if not self.pd_pos() == "task_finish":
                        time.sleep(0.1)
                    else:
                        break
                log.o_p("task finished", 1)
                for j in range(0, 2):
                    self.device.click(60, 40)
                    self.click_time = time.time() - self.base_time
                    time.sleep(0.1)
            log.o_p("hard task finished", 1)
        self.to_main_page()



        activity[2][1] = 1
        log.o_p("clear energy task finished", 1)

    def to_main_page(self):
        while 1:
            if not self.pd_pos() == "main_page":
                self.device.click(60, 40)
                self.click_time = time.time() - self.base_time
                log.o_p("Click :(60,40) " + " click_time = " + str(self.click_time), 1)
            else:
                break


if __name__ == '__main__':
    b_aas = baas()
    b_aas.thread_starter()
