import cv2
import shutil
import log
from get_location import locate
import threading
import time
import sys
import os

class baas(locate):

    def __init__(self):
        super().__init__()
        self.flag_run = True
        self.schedule_pri = [5, 4, 3, 2, 1]
        self.main_activity = ["cafe_reward", "group", "mail", "collect_daily_power", "shop", "collect_shop_power", "rewarded_task",
                              "schedule", "total_force_fight", "arena", "clear_event_power", "clear_special_task_power",
                              "create", "collect_reward"]

        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]

        for i in range(0, 12):
           self.main_activity[i][1] = 1
        # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.package_name = 'com.RoamingStar.BlueArchive'
        self.exit_loop = False
        self.unknown_ui_page_count = 0
        self.pos = []
        self.base_time = time.time()
        self.alas_pause = False
        self.click_time = 0.0

    def click_x_y(self, x, y):
        self.set_click_time()
        log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
        self.device.click(x, y)

    def change_acc_auto(self):
        path1 = self.get_screen_shot_path()
        img1 = cv2.imread(path1)
        acc_r_ave = img1[625][1196][0] // 3 + img1[625][1215][0] // 3 + img1[625][1230][0] // 3
        print(acc_r_ave)
        if 250 <= acc_r_ave <= 260:
            log.o_p("change acceleration phase from 2 to 3", 1)
            self.click_x_y(1215, 625)
        elif 0 <= acc_r_ave <= 60:
            log.o_p("acceleration phase 3", 1)
        elif 140 <= acc_r_ave <= 180:
            log.o_p("change acceleration phase from 1 to 3", 1)
            self.click_x_y(1215, 625)
            self.click_x_y(1215, 625)
        else:
            log.o_p("can't identify acceleration button", 2)

        auto_r_ave = img1[677][1171][0] // 2 + img1[677][1246][0] // 2
        if 190 <= auto_r_ave <= 230:
            log.o_p("change manual to auto", 1)
            self.click_x_y(1216, 678)
        elif 0 <= auto_r_ave <= 60:
            log.o_p("auto", 1)
        else:
            log.o_p("can't identify auto button", 2)
        print(auto_r_ave)

    def common_fight_practice(self):
        self.change_acc_auto()

        while 1:
            path1 = self.get_screen_shot_path()
            path2 = "src/common_button/check_blue.png"
            path3 = "src/common_button/damage_rank.png"
            path4 = "src/common_button/check_yellow.png"
            return_data1 = self.get_x_y(path1, path2)
            return_data2 = self.get_x_y(path1, path3)
            if return_data1[1][0] < 0.01 or return_data2[1][0] < 0.001:
                log.o_p("fight ended", 1)
                self.click_x_y(1171, 665)

                break
            else:
                self.click_x_y(184, 100)
                log.o_p("fighting", 1)
            time.sleep(2)

        while 1:
            path1 = self.get_screen_shot_path()
            path2 = "src/common_button/check_yellow.png"
            path3 = "src/common_button/back_to_main_page.png"
            return_data1 = self.get_x_y(path1, path2)
            return_data2 = self.get_x_y(path1, path3)
            if return_data1[1][0] < 0.01:
                log.o_p("reward collected", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])
                break
            elif return_data2[1][0] < 0.01:
                log.o_p("back to main page", 1)
                self.click_x_y(return_data2[0][0], return_data2[0][1])
            time.sleep(2)

    def special_task_common_operation(self, a, b, f=True):
        special_task_lox = 1120
        special_task_loy = [180, 286, 386, 489, 564, 432, 530, 628]
        self.device.swipe(916, 160, 916, 680, 0.1)
        time.sleep(0.5)
        log.o_p("swipe", 1)
        if a >= 6:
            self.device.swipe(916, 680, 916, 160, 0.1)
            log.o_p("swipe", 1)
            time.sleep(1)

        self.click_x_y(special_task_lox, special_task_loy[a - 1])
        if self.pd_pos() == "notice":
            log.o_p("UNLOCKED", 3)
        else:
            for i in range(0, b - 1):
                self.click_x_y(1033, 297)
                if f:
                    time.sleep(0.6)
            self.click_x_y(937, 404)
        lo = self.pd_pos()
        if lo == "charge_power":
            log.o_p("inadequate power , exit task", 3)
        elif lo == "charge_notice":
            log.o_p("inadequate ticket , exit task", 3)
        else:
            self.click_x_y(767, 501)

    def main_to_page(self, index):

        schedule_lo_y = [183, 297, 401, 508, 612]
        to_page = [[[93, 1114], [654, 649], ["cafe", "cafe_reward"]],
                   [[580], [650], ["group"]],
                   [[1140], [42], ["mail"]],
                   [[64], [233], ["work_task"]],
                   [[824], [648], ["shop"]],
                   [[824], [648], ["shop"]],
                   [[1200, 731], [570, 474], ["business_area", "rewarded_task"]],
                   [],
                   [[1200, 916, 1162, 1009, 1160], [570, 535, 225, 521, 650], ["business_area", "total_force_fight", "detailed_message", "attack_formation", "notice"]],
                   [[1193, 1092], [576, 525], ["business_area", "arena"]],
                   [[1159], [568], ["business_area"]],
                   [[1159, 727], [568, 576], ["business_area", "choose_special_task"]],
                   [[703], [649], ["manufacture_store"]],
                   [[64], [233], ["work_task"]]]
        to_page[7] = [[217, 940], [659, schedule_lo_y[self.schedule_pri[0] - 1]], ["schedule", "schedule" + str(self.schedule_pri[0])]]
        procedure = to_page[index]
        step = 0
        if len(procedure) != 0:
            step = len(procedure[0])
        if step:
            log.o_p("begin main to page " + str(procedure[2][step - 1]), 1)
        i = 0
        times = 0
        while i != step:
            x = procedure[0][i]
            y = procedure[1][i]
            page = procedure[2][i]
            self.click_x_y(x, y)

            if self.pd_pos() != page:
                if times == 0:
                    times += 1
                    log.o_p("not in page " + str(page) + " , count = " + str(times), 2)
                elif times == 1:
                    log.o_p("not in page " + str(page) + " , return to main page", 2)
                    self.to_main_page()
                    times = 0
                    i = 0
            else:
                times = 0
                i += 1

    def set_click_time(self):
        self.click_time = time.time() - self.base_time

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
#       print(self.pos)

    def run(self):
        self.base_time = time.time()
        while self.flag_run:
            if self.exit_loop:
                break
            threading.Thread(target=self.worker).start()
            time.sleep(0.5)

    def thread_starter(self):
        thread_run = threading.Thread(target=self.run)
        thread_run.start()
        for i in range(0, len(self.main_activity)):
            print(self.main_activity[i][0], self.main_activity[i][1])
            if self.main_activity[i][1] == 0:
                print("----------------------------------------------------------------------------------------------")
                log.o_p("begin " + self.main_activity[i][0] + " task", 1)
                self.to_main_page()
                self.main_to_page(i)
                self.solve(self.main_activity[i][0])
        for i in range(0, len(self.main_activity)):
            print(self.main_activity[i][0], self.main_activity[i][1])
        self.flag_run = False

    def pd_pos(self):
        while len(self.pos) > 0 and self.pos[len(self.pos) - 1][1] < self.click_time:
            self.pos.pop()
        while 1:
            if len(self.pos) == 2 and self.pos[0][0] == self.pos[1][0]:
                lo = self.pos[0][0]
                self.pos.clear()
                if lo == "UNKNOWN UI PAGE" and self.unknown_ui_page_count < 5:
                    self.unknown_ui_page_count += 1
                    log.o_p("UNKNOWN UI PAGE COUNT:" + str(self.unknown_ui_page_count), 2)
                elif lo == "UNKNOWN UI PAGE" and self.unknown_ui_page_count == 5:
                    log.o_p("Unknown ui page", 3)
                    self.flag_run = False
                else:
                    self.unknown_ui_page_count = 0
                    log.o_p("current_location : " + lo, 1)
                    return lo
            time.sleep(0.5)

    def solve(self, activity):
        if activity == "cafe_reward":
            self.click_x_y(640, 521)
            log.o_p("cafe reward task finished", 1)
            self.main_activity[0][1] = 1

        elif activity == "group":
            log.o_p("group task finished", 1)
            self.main_activity[1][1] = 1

        elif activity == "mail":
            path1 = self.get_screen_shot_path()
            path2 = "src/mail/collect_all_bright.png"
            path3 = "src/mail/collect_all_grey.png"
            return_data1 = self.get_x_y(path1, path2)
            return_data2 = self.get_x_y(path1, path3)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 0.001:
                log.o_p("mail reward has been collected", 1)
            elif return_data1[1][0] <= 0.01:
                log.o_p("collect mail reward", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])
            else:
                log.o_p("Can't detect button", 2)

            self.main_activity[2][1] = 1
            log.o_p("mail task finished", 1)

        elif activity == "collect_daily_power" or activity == "collect_reward":
            while 1:
                path1 = self.get_screen_shot_path()
                path2 = "src/daily_task/daily_task_collect_all_bright.png"
                path3 = "src/daily_task/daily_task_collect_all_button_grey.png"
                return_data1 = self.get_x_y(path1, path2)
                return_data2 = self.get_x_y(path1, path3)
                print(return_data1)
                print(return_data2)
                if return_data2[1][0] <= 0.001:
                    log.o_p("work reward has been collected", 1)
                    break
                elif return_data1[1][0] <= 0.01:
                    log.o_p("collect work task reward", 1)
                    self.click_x_y(return_data1[0][0], return_data1[0][1])
                    time.sleep(2)
                    self.click_x_y(625, 667)
                    time.sleep(0.2)
                else:
                    log.o_p("Can't detect button", 2)
                    return
            if activity == "collect_daily_power":
                self.main_activity[3][1] = 1
            else:
                self.main_activity[13][1] = 1
            log.o_p("collect daily power task finished", 1)

        elif activity == "shop" or activity == "collect_shop_power":
            if activity == "collect_shop_power":
                x = 100
                y = 370
                self.click_x_y(x, y)
                time.sleep(0.5)

                buy_list_for_power_items = [[1000, 204], [1162, 204]]

                for i in range(0, len(buy_list_for_power_items)):
                    self.device.click(buy_list_for_power_items[i][0], buy_list_for_power_items[i][1])
                self.set_click_time()
            else :
                log.o_p("swipe", 1)
                self.device.swipe(932, 600, 932, 260, 0.1)
                buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                             [700, 461], [857, 461], [1000, 461], [1162, 461]]
                for i in range(0, len(buy_list_for_common_items)):
                    self.device.click(buy_list_for_common_items[i][0], buy_list_for_common_items[i][1])
                self.set_click_time()
            path1 = self.get_screen_shot_path()
            path2 = "src/shop/buy_bright.png"
            path3 = "src/shop/buy_grey.png"
            path4 = "src/shop/update.png"
            return_data1 = self.get_x_y(path1, path2)
            return_data2 = self.get_x_y(path1, path3)
            return_data3 = self.get_x_y(path1, path4)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 0.005:
                log.o_p("assets inadequate", 1)
            elif return_data1[1][0] <= 0.02:
                log.o_p("buy operation succeeded", 1)
                self.device.click(return_data1[0][0], return_data1[0][1])
                time.sleep(0.5)
                self.device.click(770, 480)
                self.set_click_time()
            elif return_data3[1][0] <= 0.002:
                log.o_p("items have been brought", 1)
            else:
                log.o_p("Can't detect button", 2)

            if activity == "collect_shop_power":
                self.main_activity[5][1] = 1
                log.o_p("collect shop power task finished", 1)
            else:
                self.main_activity[4][1] = 1
                log.o_p("shop task finished", 1)

        elif activity == "clear_event_power":

            common_task_count = [(7, 1, 6)]
            hard_task_count = [(4, 3, 1)]

            if len(common_task_count) != 0 or len(hard_task_count) != 0:
                all_task_x_coordinate = 1118
                common_task_y_coordinates = [242, 342, 438, 538, 569, 469, 369, 269]
                hard_task_y_coordinates = [250, 360, 470]
                self.click_x_y(816, 267)
                left_change_page_x = 32
                right_change_page_x = 1247
                change_page_y = 360
                time.sleep(2)
                if len(common_task_count) != 0:
                    print("----------------------------------------------------------------------------------------------")
                    log.o_p("common task begin", 1)
                    log.o_p("change to common level", 1)
                    self.click_x_y(800, 150)
                    time.sleep(0.1)
                    for i in range(0, len(common_task_count)):
                        cur_lo = self.pd_pos()
                        log.o_p("now in page " + cur_lo, 1)
                        if cur_lo[0:4] != "task":
                            log.o_p("incorrect page exit common task", 3)
                            break
                        cur_num = int(cur_lo[5:])
                        tar_num = common_task_count[i][0]
                        tar_level = common_task_count[i][1]
                        tar_times = common_task_count[i][2]
                        log.o_p("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started", 1)
                        while cur_num != tar_num:
                            if cur_num > tar_num:
                                self.click_x_y(left_change_page_x, change_page_y)
                            else:
                                self.click_x_y(right_change_page_x, change_page_y)
                            cur_lo = self.pd_pos()
                            if cur_lo[0:4] != "task":
                                log.o_p("incorrect page exit task clear event power", 3)
                                return
                            cur_num = int(cur_lo[5:])
                            log.o_p("now in page " + cur_lo, 1)

                        log.o_p("find target page " + cur_lo, 1)
                        if tar_level >= 5:
                            page_task_numbers = [8, 6, 7]
                            self.device.swipe(928, 560, 928, 0, 0.5)
                            log.o_p("SWIPE", 1)
                            time.sleep(0.5)
                            if tar_num < 4:
                                tar_level = page_task_numbers[tar_num - 1] + (5 - tar_level) - 1
                        else:
                            tar_level -= 1
                        self.click_x_y(all_task_x_coordinate, common_task_y_coordinates[tar_level])
                        time.sleep(0.5)
                        for j in range(0, tar_times - 1):
                            self.click_x_y(1033, 297)
                            time.sleep(0.6)
                        self.click_x_y(937, 404)
                        if self.pd_pos() == "charge_power":
                            log.o_p("inadequate power , exit task", 3)
                            return
                        self.click_x_y(767, 501)
                        while 1:
                            if not self.pd_pos() == "task_" + str(tar_num):
                                for j in range(0, 4):
                                    self.device.click(651, 663)
                                    self.click_time = time.time() - self.base_time
                                    time.sleep(0.1)
                            else:
                                break
                        log.o_p("task finished", 1)
                    log.o_p("common task finished", 1)

                if len(hard_task_count) != 0:
                    print("----------------------------------------------------------------------------------------------")
                    log.o_p("hard task begin", 1)

                    log.o_p("change to hard level", 1)
                    self.device.click(1065, 150)
                    time.sleep(0.1)

                    for i in range(0, len(hard_task_count)):
                        cur_lo = self.pd_pos()
                        if cur_lo[0:4] != "task":
                            log.o_p("incorrect page exit common task", 3)
                            break
                        cur_num = int(cur_lo[5:])
                        log.o_p("now in page " + cur_lo, 1)
                        tar_num = hard_task_count[i][0]
                        tar_level = hard_task_count[i][1]
                        tar_times = hard_task_count[i][2]
                        log.o_p("task " + str(tar_num) + "-" + str(tar_level) + ": " + str(tar_times) + " started", 1)
                        while cur_num != tar_num:
                            if cur_num > tar_num:
                                self.device.click(left_change_page_x, change_page_y)
                                self.set_click_time()
                                log.o_p("Click :(" + str(left_change_page_x) + " " + str(
                                    change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                            else:
                                self.device.click(right_change_page_x, change_page_y)
                                self.set_click_time()
                                log.o_p("Click :(" + str(right_change_page_x) + " " + str(
                                    change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                            cur_lo = self.pd_pos()
                            if cur_lo[0:4] != "task":
                                log.o_p("incorrect page exit task clear power", 3)
                                return
                            cur_num = int(cur_lo[5:])
                            log.o_p("now in page " + cur_lo, 1)

                        log.o_p("find target page " + cur_lo, 1)
                        tar_level -= 1

                        self.device.click(all_task_x_coordinate, hard_task_y_coordinates[tar_level])
                        self.set_click_time()
                        log.o_p("Click :(" + str(all_task_x_coordinate) + " " + str(
                            hard_task_y_coordinates[tar_level]) + ")" + " click_time = " + str(self.click_time), 1)
                        time.sleep(0.5)
                        for j in range(0, tar_times - 1):
                            self.device.click(1033, 297)
                            time.sleep(0.6)
                        self.device.click(937, 404)
                        self.set_click_time()
                        lo = self.pd_pos()
                        if lo == "charge_power":
                            log.o_p("inadequate power , exit task", 3)
                            break
                        if lo == "charge_notice":
                            log.o_p("inadequate fight time available", 3)
                            break
                        self.click_x_y(767, 501)
                        while 1:
                            lo = self.pd_pos()
                            if lo != "task_" + str(tar_num):
                                for j in range(0, 4):
                                    self.device.click(651, 663)
                                    self.set_click_time()
                                    time.sleep(0.1)
                            else:
                                break
                        log.o_p("task finished", 1)
                    log.o_p("hard task finished", 1)
            self.main_activity[10][1] = 1
            log.o_p("clear event power task finished", 1)

        elif activity == "clear_special_task_power":
            special_task_guard_count = [6, 1]
            special_task_credit_count = [3, 1]

            if len(special_task_guard_count) != 0:
                print("----------------------------------------------------------------------------------------------")
                log.o_p("special task guard begin", 1)

                self.click_x_y(959, 269)
                time.sleep(1.5)

                self.special_task_common_operation(special_task_guard_count[0], special_task_guard_count[1])
                log.o_p("special task guard finished", 1)

            if len(special_task_guard_count) != 0:
                print("----------------------------------------------------------------------------------------------")
                log.o_p("special task credit begin", 1)

                self.to_main_page()
                self.main_to_page(11)
                self.click_x_y(964, 408)
                time.sleep(1.5)

                self.special_task_common_operation(special_task_credit_count[0], special_task_credit_count[1])
                log.o_p("special task credit finished", 1)

            self.main_activity[11][1] = 1
            log.o_p("clear special task power finished", 1)
        elif activity == "rewarded_task":
            dif = [4, 4, 4]
            print("----------------------------------------------------------------------------------------------")
            log.o_p("rewarded task road begin", 1)
            self.click_x_y(957, 275)
            time.sleep(1.5)
            self.special_task_common_operation(dif[0], 6, False)
            log.o_p("rewarded task road finished", 1)

            print("----------------------------------------------------------------------------------------------")
            log.o_p("rewarded task rail begin", 1)
            self.main_to_page(6)
            self.click_x_y(957, 412)
            time.sleep(1.5)
            self.special_task_common_operation(dif[1], 6, False)
            log.o_p("rewarded task rail finished", 1)

            print("----------------------------------------------------------------------------------------------")
            log.o_p("rewarded task class begin", 1)
            self.main_to_page(6)
            self.click_x_y(957, 556)
            time.sleep(1.5)
            self.special_task_common_operation(dif[2], 6, False)
            log.o_p("rewarded task class finished", 1)

        elif activity == "schedule":
            region_name = ["沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区"]

            lo = [[300, 267], [645, 267], [985, 267],
                  [300, 413], [645, 413], [985, 413],
                  [300, 531], [645, 531], [985, 531]]
            region_schedule_total_count = [7, 7, 8, 8, 8]
            cur_num = self.schedule_pri[0]
            left_change_page_x = 32
            right_change_page_x = 1247
            change_page_y = 360
            for i in range(0, len(self.schedule_pri)):
                tar_num = self.schedule_pri[i]
                log.o_p("begin schedule in <" + region_name[tar_num - 1] + ">", 1)
                while cur_num != tar_num:
                    if cur_num > tar_num:
                        self.device.click(left_change_page_x, change_page_y)
                        self.set_click_time()
                        log.o_p("Click :(" + str(left_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                    else:
                        self.device.click(right_change_page_x, change_page_y)
                        self.set_click_time()
                        log.o_p("Click :(" + str(right_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                    cur_lo = self.pd_pos()
                    cur_num = int(cur_lo[8:])
                    log.o_p("now in page " + cur_lo, 1)
                x = 1160
                y = 664
                self.device.click(x, y)
                self.set_click_time()
                log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                if not self.pd_pos() == "all_schedule":
                    log.o_p("not in page all schedule , return", 3)
                    return
                path1 = self.get_screen_shot_path()
                path1 = self.img_crop(path1, 126, 1167, 98, 719)
                res = self.img_ocr(path1)
                count = self.kmp("需要评级", res)
                start = region_schedule_total_count[self.schedule_pri[0] - 1] - count
                for j in range(0, start):
                    x = lo[start - j - 1][0]
                    y = lo[start - j - 1][1]
                    self.device.click(x, y)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                    time.sleep(0.5)
                    x = 640
                    y = 556
                    self.device.click(640, 556)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                    self.set_click_time()
                    if self.pd_pos() == "notice":
                        self.main_activity[7][1] = 1
                        log.o_p("task schedule finished", 1)
                        return
                    time.sleep(2)
                    self.set_click_time()
                    while self.pd_pos() != "all_schedule":
                        self.click_x_y(919, 116)
                self.click_x_y(641, 668)

        elif activity == "total_force_fight":
            self.click_x_y(767, 500)
            time.sleep(4)
            self.click_x_y(764, 504)
            if self.pd_pos() == "notice":
                self.click_x_y(764, 504)
                time.sleep(4)

            self.common_fight_practice()

        elif activity == "create":
            collect = False
#            0.01 0.01 0.01 0.002 0.01
            path1 = self.get_screen_shot_path()
            path5 = "src/create/start_button_bright.png"
            path6 = "src/create/start_button_grey.png"
            self.common_create_collect_operation()
            log.o_p("all creature collected", 1)

            lox = 967
            loy = [273, 411, 548]
            collect = False
            for i in range(0, 3):
                self.click_x_y(lox, loy[i])
                if self.pd_pos() == "create":
                    self.click_x_y(907, 206)
                    time.sleep(0.2)
                    path1 = self.get_screen_shot_path()
                    return_data1 = self.get_x_y(path1, path5)
                    return_data2 = self.get_x_y(path1, path6)
                    if return_data2[1][0] < 0.002:
                        log.o_p("material inadequate", 2)
                        break
                    elif return_data1[1][0] < 0.01:
                        log.o_p("create start", 2)
                        collect = True
                        self.click_x_y(return_data1[0][0], return_data1[0][1])
                        time.sleep(3.5)
                        node_x = [572, 508, 416, 302, 174]
                        node_y = [278, 388, 471, 529, 555]
                        choice = self.common_create_judge()
                        if choice is not None:
                            self.click_x_y(node_x[choice], node_y[choice])
                            time.sleep(0.5)
                            self.click_x_y(1123, 650)
                            time.sleep(3)
                            self.click_x_y(1123, 650)
                            time.sleep(4)
        if collect:
            self.common_create_collect_operation()
            log.o_p("all creature collected", 1)
            self.main_activity[12][1] = 1
            log.o_p("Create task finished", 1)

        elif activity == "arena":
            while 1:
                path1 = self.get_screen_shot_path()
                path2 = "src/arena/collect_reward.png"
                return_data1 = self.get_x_y(path1, path2)
                print(return_data1)
                if return_data1[1][0] <= 0.04:
                    log.o_p("collect reward", 1)
                    self.device.click(return_data1[0][0], return_data1[0][1])
                    log.o_p("Click :(" + str(return_data1[0][0]) + " " + str(return_data1[0][1]) + ")" + " click_time = " + str(self.click_time), 1)
                    time.sleep(2)
                    self.device.click(666, 672)
                    self.set_click_time()
                    time.sleep(0.5)
                else:
                    log.o_p("reward collected", 1)
                    break

            choice = 1
            x = 844
            y = [261, 414, 581]
            y = y[choice - 1]
            f_skip = False

            while 1:
                self.device.click(x, y)
                time.sleep(1)
                self.device.click(638, 569)
                lo = self.pd_pos()
                while lo != "notice" and lo != "attack_formation":
                    lo = self.pd_pos()
                if lo == "notice":
                    self.main_activity[9][1] = 1
                    log.o_p("task arena finished", 1)
                    return
                elif lo == "attack_formation":
                    if not f_skip:
                        path1 = self.get_screen_shot_path()
                        path2 = "src/arena/skip.png"
                        return_data1 = self.get_x_y(path1, path2)
                        print(return_data1)
                        if return_data1[1][0] <= 0.02:
                            log.o_p("skip choice on", 1)
                        else:
                            log.o_p("skip choice off , turn on skip choice", 1)
                            self.device.click(1122, 602)
                            time.sleep(0.1)
                        f_skip = True
                self.device.click(1169, 670)
                if self.pd_pos() == "notice":
                    time.sleep(2)
                    self.device.click(1169, 670)
                while self.pd_pos() != "arena":
                    self.device.click(666, 555)

                time.sleep(45)

    def common_create_judge(self):
        pri = ["花", "Mo", "情人节", "果冻", "色彩", "灿烂", "光芒", "玲珑", "白金", "黄金", "铜", "白银", "金属", "隐然"]
        node_x = [839, 508, 416, 302, 174]
        node_y = [277, 388, 471, 529, 555]
        # 572 278
        node = []
        for i in range(0, 5):
            self.click_x_y(node_x[i], node_y[i])
            time.sleep(0.2 if i == 0 else 0.1)
            node_info = self.img_ocr(self.get_screen_shot_path())
            for k in range(0, len(pri)):
                if self.kmp(pri[k], node_info) > 0:
                    if k == 0:
                        log.o_p("choose node :" + pri[0], 1)
                        return i
                    else:
                        node.append(pri[k])
        print(node)
        for i in range(1, len(pri)):
            for j in range(0, len(node)):
                if node[j][0:len(pri[i])] == pri[i]:
                    return j
    def common_create_collect_operation(self):
        path1 = self.get_screen_shot_path()
        path3 = "src/create/collect.png"
        path4 = "src/create/finish_instantly.png"
        return_data1 = self.get_x_y(path1, path3)
        return_data2 = self.get_x_y(path1, path4)
        while return_data1[1][0] < 0.01 or return_data2[1][0] < 0.01:
            if return_data1[1][0] < 0.01:
                log.o_p("collect finished creature", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])
                time.sleep(2)
                self.click_x_y(628, 665)
                time.sleep(1)
            if return_data2[1][0] < 0.01:
                log.o_p("accelerate unfinished creature", 1)
                self.click_x_y(return_data2[0][0], return_data2[0][1])
                time.sleep(0.5)
                self.click_x_y(775, 477)
                time.sleep(2)
            path1 = self.get_screen_shot_path()
            time.sleep(0.2)
            return_data1 = self.get_x_y(path1, path3)
            return_data2 = self.get_x_y(path1, path4)

    def to_main_page(self):
        while 1:
            if not self.pd_pos() == "main_page":
                self.click_x_y(1236, 39)
            else:
                break


if __name__ == '__main__':
    def delete_all_files_in_directory(directory_path):
        try:
            # 使用 shutil.rmtree 递归删除目录及其内容
            shutil.rmtree(directory_path)
            print(f"已删除目录及其所有文件: {directory_path}")
        except Exception as e:
            print(f"发生错误: {e}")
    # 指定要删除文件的目录路径
    directory_to_delete = "logs"
    if os.path.exists("logs"):
        delete_all_files_in_directory(directory_to_delete)

    os.mkdir('logs')
    # os.makedirs("logs", exist_ok=True)
    b_aas = baas()
#    print(b_aas.common_create_judge())
#    b_aas.common_fight_practice()
    b_aas.thread_starter()