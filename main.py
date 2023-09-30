import uiautomator2 as u2
import log
from get_location import locate
import threading
import time
import numpy as np



class baas(locate):

    def __init__(self):
        exe_path = "H:\\MuMuPlayer-12.0\\shell\\MuMuPlayer.exe"  # 可设置 模拟器 .exe 文件路径
        #        subprocess.Popen(exe_path)
        #        time.sleep(30)
        simulator_port = 7555
        adb_command = f"adb connect 127.0.0.1:{simulator_port}"  # 可设置 模拟器 端口
        #        for i in range(0, 6):
        #           try:
        #                subprocess.run(adb_command, shell=True, check=True)
        #                print(f"成功连接到模拟器端口 {simulator_port}")
        #                break
        #            except subprocess.CalledProcessError:
        #               time.sleep(10)
        #               print(f"无法连接到模拟器端口 {simulator_port}")

        super().__init__()
        self.flag_run = True
        self.schedule_pri = [5, 4, 3, 2, 1]  # 可设置参数，日程区域优先级
        self.main_activity = ["cafe_reward", "group", "mail", "collect_daily_power", "shop", "collect_shop_power",
                              "rewarded_task",
                              "schedule", "total_force_fight", "arena", "clear_event_power", "clear_special_task_power",
                              "create", "collect_reward", "momo_talk"]

        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]

        for i in range(0, 12):  # 可设置参数 range(0,i) 中 i 表示前 i 项任务不做
            self.main_activity[i][1] = 1
        url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.total_force_fight_y = [225, 351, 487, 588]
        self.pri_total_force_fight = 1
        self.package_name = 'com.RoamingStar.BlueArchive'
        self.unknown_ui_page_count = 0
        self.pos = []
        self.latest_img_array = None
        self.base_time = time.time()
        self.alas_pause = False
        self.click_time = 0.0

    def click_x_y(self, x, y):  # 点击屏幕（x，y）处
        self.set_click_time()
        log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
        u2.connect().click(x, y)

    def change_acc_auto(self):  # 战斗时自动开启3倍速和auto
        img1 = self.get_screen_shot_array()
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

    def common_skip_plot_method(self):
        fail_cnt = 0
        path = "src/skip_plot/skip_plot_button.png"
        while fail_cnt <= 20:
            self.latest_img_array = self.get_screen_shot_array()
            return_data = self.get_x_y(self.latest_img_array, path)
            print(return_data)
            if return_data[1][0] < 1e-03:
                log.o_p("find skip plot button", 1)
                self.click_x_y(return_data[0][0],return_data[0][1])
                time.sleep(1)
                log.o_p("skip plot", 1)
                self.click_x_y(766, 520)
                return True
            else:
                fail_cnt += 1
                log.o_p("can't find skip plot button, fail count: " + str(fail_cnt), 2)
                self.click_x_y(1205, 37)
                time.sleep(1)
        log.o_p("skip plot fail", 3)

    def common_fight_practice(self):
        self.flag_run = False
        self.change_acc_auto()
        success = None
        while 1:
            self.latest_img_array = self.get_screen_shot_array()
            path1 = "src/common_button/check_blue.png"
            path3 = "src/common_button/fail_check.png"
            return_data1 = self.get_x_y(self.latest_img_array, path1)
            return_data2 = self.get_x_y(self.latest_img_array, path3)
            if return_data1[1][0] < 1e-03 or return_data2[1][0] < 1e-03:
                if return_data1[1][0] < 1e-03:
                    log.o_p("fight succeeded", 1)
                    success = True
                    self.click_x_y(return_data1[0][0], return_data1[0][1])
                else:
                    log.o_p("fight failed", 1)
                    success = False
                    self.click_x_y(return_data2[0][0], return_data2[0][1])
                break
            else:
                self.click_x_y(767, 500)
                log.o_p("fighting", 1)
            time.sleep(4)

        thread_run = threading.Thread(target=self.run)
        thread_run.start()

        if not success:
            while 1:
                self.latest_img_array = self.get_screen_shot_array()
                path2 = "src/common_button/fail_check.png"
                return_data1 = self.get_x_y(self.latest_img_array, path2)
                print(return_data1[1][0])
                if return_data1[1][0] < 1e-03:
                    log.o_p("fail back", 1)
                    self.click_x_y(return_data1[0][0], return_data1[0][1])
                    break
                time.sleep(2)
        else:
            while 1:
                self.latest_img_array = self.get_screen_shot_array()
                path2 = "src/common_button/check_yellow.png"
                return_data1 = self.get_x_y(self.latest_img_array, path2)
                if return_data1[1][0] < 1e-03:
                    log.o_p("reward collected success back", 1)
                    self.click_x_y(return_data1[0][0], return_data1[0][1])
                    break
                time.sleep(2)

        time.sleep(5)

        return success

    def special_task_common_operation(self, a, b, f=True):
        special_task_lox = 1120
        special_task_loy = [180, 286, 386, 489, 564, 432, 530, 628]
        u2.connect().swipe(916, 160, 916, 680, 0.1)
        time.sleep(0.5)
        log.o_p("swipe", 1)
        if a >= 6:
            u2.connect().swipe(916, 680, 916, 160, 0.1)
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
        to_page = [[[93, 1114], [654, 649], ["cafe", "cafe_reward"]],
                   [[580], [650], ["group"]],
                   [[1140], [42], ["mail"]],
                   [[64], [233], ["work_task"]],
                   [[824], [648], ["shop"]],
                   [[824], [648], ["shop"]],
                   [[1200, 731], [570, 474], ["business_area", "rewarded_task"]],
                   [],
                   [[1200, 916, 1162, 1009, 1160], [570, 535, 225, 521, 650],
                    ["business_area", "total_force_fight", "detailed_message", "attack_formation", "notice"]],
                   [[1193, 1092], [576, 525], ["business_area", "arena"]],
                   [[1159], [568], ["business_area"]],
                   [[1159, 727], [568, 576], ["business_area", "choose_special_task"]],
                   [[703], [649], ["manufacture_store"]],
                   [[64], [233], ["work_task"]],
                   [[167], [141], ["momo_talk1"]],
                   [[1200, 916, 1162, 1009], [570, 535, 225, 521],
                    ["business_area", "total_force_fight", "detailed_message", "attack_formation"]]
                   ]

        schedule_lo_y = [183, 297, 401, 508, 612]
        to_page[7] = [[217, 940], [659, schedule_lo_y[self.schedule_pri[0] - 1]],
                      ["schedule", "schedule" + str(self.schedule_pri[0])]]
        to_page[8][1][2] = self.total_force_fight_y[self.pri_total_force_fight]
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
        u2.connect().app_start(self.package_name)
        t = u2.connect().window_size()
        log.o_p("Screen Size  " + str(t), 1)
        if (t[0] == 1280 and t[1] == 720) or (t[1] == 1280 and t[0] == 720):
            log.o_p("Screen Size Fitted", 1)
        else:
            log.o_p("Screen Size unfitted", 4)
            exit(1)
        self.thread_starter()

    def worker(self):
        shot_time = time.time() - self.base_time
        self.latest_img_array = self.get_screen_shot_array()

        self.get_keyword_appear_time(self.img_ocr(self.latest_img_array))
        locate_res = self.return_location()
        ct = time.time()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, ct - self.base_time])
        if len(self.pos) > 2:
            self.pos.pop()

    #       print(self.pos)

    def run(self):
        self.flag_run = True
        log.o_p("start getting screenshot", 1)
        while self.flag_run:
            threading.Thread(target=self.worker).start()
            time.sleep(1)  # 可设置参数 time.sleep(i) 截屏速度为i秒/次，越快程序作出反映的时间便越快，同时对电脑的性能要求也会提高，目前推荐设置为1，后续优化后可以设置更低的值
        log.o_p("stop getting screenshot", 1)

    def thread_starter(self):
        thread_run = threading.Thread(target=self.run)
        thread_run.start()
        lo = self.pd_pos(anywhere=True)
        while lo != "main_page" and lo != "notice" and lo != "main_notice":
            self.click_x_y(1231, 31)
            self.click_x_y(108, 368)
            lo = self.pd_pos(anywhere=True)
        if lo == "main_notice":
            self.click_x_y(1138, 101)
        elif lo == "notice":
            self.click_x_y(763, 500)
        print("----------------------------------------------------------------------------------------------")
        print("----------------------------------------------------------------------------------------------")
        log.o_p("start activities", 1)
        while self.flag_run:
            for i in range(0, len(self.main_activity)):
                print(self.main_activity[i][0], self.main_activity[i][1])
                if self.main_activity[i][1] == 0:
                    print(
                        "----------------------------------------------------------------------------------------------")
                    log.o_p("begin " + self.main_activity[i][0] + " task", 1)
                    self.to_main_page()
                    self.main_to_page(i)
                    self.solve(self.main_activity[i][0])
        count = 0
        for i in range(0, len(self.main_activity)):
            if self.main_activity[i][1] == 1:
                count += 1
        if count == 13:
            self.flag_run = False

    def pd_pos(self, path=None,name=None,anywhere=False):
        if path:
            return_data = self.get_x_y(self.latest_img_array, path)
            print(return_data)
            if return_data[1][0] <= 1e-03:
                return name
        else:
            while len(self.pos) > 0 and self.pos[len(self.pos) - 1][1] < self.click_time:
                self.pos.pop()
            while 1:
                if len(self.pos) == 2 and self.pos[0][0] == self.pos[1][0]:
                    lo = self.pos[0][0]
                    self.pos.clear()
                    if lo == "UNKNOWN UI PAGE":
                        if anywhere:
                            return "click_anywhere"
                        elif self.unknown_ui_page_count < 20:
                            self.unknown_ui_page_count += 1
                            log.o_p("UNKNOWN UI PAGE COUNT:" + str(self.unknown_ui_page_count), 2)
                        elif self.unknown_ui_page_count == 20:
                            log.o_p("Unknown ui page", 3)
                            self.flag_run = False
                    else:
                        self.unknown_ui_page_count = 0
                        log.o_p("current_location : " + lo, 1)
                        return lo
                time.sleep(1)

    def solve(self, activity):
        if activity == "cafe_reward":
            self.click_x_y(640, 521)

            while self.pd_pos() != "cafe":
                self.click_x_y(274, 161)

            self.latest_img_array = self.get_screen_shot_array()
            path = "src/cafe/invitation_ticket.png"
            return_data1 = self.get_x_y(self.latest_img_array, path)
            print(return_data1)
            if return_data1[1][0] <= 1e-03:
                log.o_p("invitation available", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])

            else:
                log.o_p("invitation ticket used", 2)
            name_st = "爱丽丝邀请小春"
            student_name = ["爱丽丝", "小春"]
            detected_name = []
            i = 0
            while i < len(name_st):
                for j in range(0,student_name):
                    if name_st[i] == student_name[j][0]:
                        flag = True
                        for k in range(1,len(student_name[j])):
                            if name_st[i+k] != student_name[j][k]:
                                flag = False
                                break
                        if flag:
                            detected_name.append(student_name[j])
                        i = i + len(student_name[j])
                        break
                i = i + 1
            print(detected_name)
            self.main_activity[0][1] = 1
            log.o_p("cafe reward task finished", 1)

        elif activity == "group":
            log.o_p("group task finished", 1)
            self.main_activity[1][1] = 1

        elif activity == "mail":
            self.latest_img_array = self.get_screen_shot_array()
            path2 = "src/mail/collect_all_bright.png"
            path3 = "src/mail/collect_all_grey.png"
            return_data1 = self.get_x_y(self.latest_img_array, path2)
            return_data2 = self.get_x_y(self.latest_img_array, path3)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 1e-03:
                log.o_p("mail reward has been collected", 1)
            elif return_data1[1][0] <= 1e-03:
                log.o_p("collect mail reward", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])
            else:
                log.o_p("Can't detect button", 2)

            self.main_activity[2][1] = 1
            log.o_p("mail task finished", 1)

        elif activity == "collect_daily_power" or activity == "collect_reward":
            while 1:
                path1 = self.get_screen_shot_array()
                path2 = "src/daily_task/daily_task_collect_all_bright.png"
                path3 = "src/daily_task/daily_task_collect_all_grey.png"
                return_data1 = self.get_x_y(path1, path2)
                return_data2 = self.get_x_y(path1, path3)
                print(return_data1)
                print(return_data2)
                if return_data2[1][0] <= 1e-03:
                    log.o_p("work reward has been collected", 1)
                    break
                elif return_data1[1][0] <= 1e-03:
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
                self.click_x_y(100, 370)
                time.sleep(0.5)

                buy_list_for_power_items = [[1000, 204], [1162, 204]]

                for i in range(0, len(buy_list_for_power_items)):
                    u2.connect().click(buy_list_for_power_items[i][0], buy_list_for_power_items[i][1])
                self.set_click_time()
            else:
                log.o_p("swipe", 1)
                u2.connect().swipe(932, 600, 932, 260, 0.1)
                buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                             [700, 461], [857, 461], [1000, 461], [1162, 461]]
                for i in range(0, len(buy_list_for_common_items)):
                    u2.connect().click(buy_list_for_common_items[i][0], buy_list_for_common_items[i][1])
                self.set_click_time()
            self.latest_img_array = self.get_screen_shot_array()
            path2 = "src/shop/buy_bright.png"
            path3 = "src/shop/buy_grey.png"
            path4 = "src/shop/update.png"
            return_data1 = self.get_x_y(self.latest_img_array, path2)
            return_data2 = self.get_x_y(self.latest_img_array, path3)
            return_data3 = self.get_x_y(self.latest_img_array, path4)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 1e-03:
                log.o_p("assets inadequate", 1)
            elif return_data1[1][0] <= 1e-03:
                log.o_p("buy operation succeeded", 1)
                u2.connect().click(return_data1[0][0], return_data1[0][1])
                time.sleep(0.5)
                u2.connect().click(770, 480)
                self.set_click_time()
            elif return_data3[1][0] <= 1e-03:
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

            common_task_count = [(7, 1, 12)]  # 可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(普通)打k次
            hard_task_count = [(4, 3, 3)]  # 可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(困难)打k次

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
                    print(
                        "----------------------------------------------------------------------------------------------")
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
                            u2.connect().swipe(928, 560, 928, 0, 0.5)
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
                                    u2.connect().click(651, 663)
                                    self.click_time = time.time() - self.base_time
                                    time.sleep(0.1)
                            else:
                                break
                        log.o_p("task finished", 1)
                    log.o_p("common task finished", 1)

                if len(hard_task_count) != 0:
                    print(
                        "----------------------------------------------------------------------------------------------")
                    log.o_p("hard task begin", 1)

                    log.o_p("change to hard level", 1)
                    u2.connect().click(1065, 150)
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
                                u2.connect().click(left_change_page_x, change_page_y)
                                self.set_click_time()
                                log.o_p("Click :(" + str(left_change_page_x) + " " + str(
                                    change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                            else:
                                u2.connect().click(right_change_page_x, change_page_y)
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

                        u2.connect().click(all_task_x_coordinate, hard_task_y_coordinates[tar_level])
                        self.set_click_time()
                        log.o_p("Click :(" + str(all_task_x_coordinate) + " " + str(
                            hard_task_y_coordinates[tar_level]) + ")" + " click_time = " + str(self.click_time), 1)
                        time.sleep(0.5)
                        for j in range(0, tar_times - 1):
                            u2.connect().click(1033, 297)
                            time.sleep(0.6)
                        u2.connect().click(937, 404)
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
                                    u2.connect().click(651, 663)
                                    self.set_click_time()
                                    time.sleep(0.1)
                            else:
                                break
                        log.o_p("task finished", 1)
                    log.o_p("hard task finished", 1)
            self.main_activity[10][1] = 1
            log.o_p("clear event power task finished", 1)

        elif activity == "clear_special_task_power":
            special_task_guard_count = [6, 1]  # 可设置参数 [i,j]表示据点防御第i关打j次 , 请确保关卡已开启扫荡
            special_task_credit_count = [3, 1]  # 可设置参数 [i,j]表示信用回收第i关打j次 , 请确保关卡已开启扫荡

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
                        u2.connect().click(left_change_page_x, change_page_y)
                        self.set_click_time()
                        log.o_p("Click :(" + str(left_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                    else:
                        u2.connect().click(right_change_page_x, change_page_y)
                        self.set_click_time()
                        log.o_p("Click :(" + str(right_change_page_x) + " " + str(
                            change_page_y) + ")" + " click_time = " + str(self.click_time), 1)
                    cur_lo = self.pd_pos()
                    cur_num = int(cur_lo[8:])
                    log.o_p("now in page " + cur_lo, 1)
                x = 1160
                y = 664
                u2.connect().click(x, y)
                self.set_click_time()
                log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                if not self.pd_pos() == "all_schedule":
                    log.o_p("not in page all schedule , return", 3)
                    return
                self.latest_img_array = self.get_screen_shot_array()
                img_cro = self.img_crop(self.latest_img_array, 126, 1167, 98, 719)
                res = self.img_ocr(img_cro)
                count = self.kmp("需要评级", res)
                start = region_schedule_total_count[self.schedule_pri[0] - 1] - count
                for j in range(0, start):
                    x = lo[start - j - 1][0]
                    y = lo[start - j - 1][1]
                    u2.connect().click(x, y)
                    log.o_p("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), 1)
                    time.sleep(0.6)
                    x = 640
                    y = 556
                    u2.connect().click(640, 556)
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
            while self.pd_pos(True) != "notice":
                self.click_x_y(764, 504)
                time.sleep(4)
            self.click_x_y(764, 504)
            time.sleep(2)

            res = self.common_fight_practice()

            if not res:
                log.o_p("total force fight failed", 1)
                fail_count = 0
                fail_x = 68
                fail_count_y = [271, 353, 438]
                while fail_count <= 3:
                    fail_count = 1
                    self.to_main_page()
                    self.main_to_page(15)
                    log.o_p("continue with formation: " + str(fail_count + 1), 1)
                    self.click_x_y(fail_x, fail_count_y[fail_count - 1])
                    time.sleep(2)
                    self.click_x_y(1155, 658)
                    time.sleep(6)
                    self.click_x_y(764, 504)
                    while self.pd_pos() != "notice":
                        self.click_x_y(764, 504)
                        time.sleep(4)
                    res = self.common_fight_practice()
                    if not res:
                        fail_count += 1
                    else:
                        break
                log.o_p("total force fight difficulty " + str(self.pri_total_force_fight + 1) + "failed", 3)
                self.pri_total_force_fight -= 1
                time.sleep(4)
                self.click_x_y(1162, 225)
                log.o_p("give up", 3)
                time.sleep(0.5)
                self.click_x_y(821, 532)
                return

            if res:
                log.o_p("total force fight succeeded", 1)
                self.click_x_y(1156, self.total_force_fight_y[self.pri_total_force_fight])
                time.sleep(0.2)
                for i in range(0, 5):
                    self.click_x_y(1070, 297)
                while self.pd_pos() != "total_force_fight":
                    self.click_x_y(300, 50)
                self.click_x_y(1180, 655)
                time.sleep(0.8)
                self.click_x_y(923, 177)
                time.sleep(0.2)
                self.click_x_y(240, 303)
                time.sleep(0.2)
                self.click_x_y(1051, 577)
                self.main_activity[8][1] = 1
                return

        elif activity == "create":
            collect = False
            #            0.01 0.01 0.01 0.002 0.01
            path1 = self.get_screen_shot_array()
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
                    self.latest_img_array = self.get_screen_shot_array()
                    return_data1 = self.get_x_y(self.latest_img_array, path5)
                    return_data2 = self.get_x_y(self.latest_img_array, path6)
                    if return_data2[1][0] < 1e-03:
                        log.o_p("material inadequate", 2)
                        break
                    elif return_data1[1][0] < 1e-03:
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
                            time.sleep(6)
            if collect:
                self.to_main_page()
                self.main_to_page(12)
                self.common_create_collect_operation()
                log.o_p("all creature collected", 1)
                self.main_activity[12][1] = 1
                log.o_p("Create task finished", 1)

        elif activity == "arena":
            self.latest_img_array = self.get_screen_shot_array()
            path2 = "src/arena/collect_reward.png"
            return_data1 = self.get_x_y(self.latest_img_array, path2)
            print(return_data1)
            if return_data1[1][0] <= 1e-03:
                log.o_p("collect reward", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])
                log.o_p("Click :(" + str(return_data1[0][0]) + " " + str(
                    return_data1[0][1]) + ")" + " click_time = " + str(self.click_time), 1)
                time.sleep(2)
                self.click_x_y(666, 672)
                time.sleep(0.5)
            else:
                log.o_p("reward collected", 1)

            self.latest_img_array = self.get_screen_shot_array()
            path2 = "src/arena/collect_reward1.png"
            return_data1 = self.get_x_y(self.latest_img_array, path2)
            print(return_data1)
            if return_data1[1][0] <= 1e-03:
                log.o_p("collect reward", 1)
                self.click_x_y(return_data1[0][0], return_data1[0][1])
                log.o_p("Click :(" + str(return_data1[0][0]) + " " + str(
                    return_data1[0][1]) + ")" + " click_time = " + str(self.click_time), 1)
                time.sleep(2)
                self.click_x_y(666, 672)
                time.sleep(0.5)
            else:
                log.o_p("reward collected", 1)
            choice = 1
            x = 844
            y = [261, 414, 581]
            y = y[choice - 1]
            f_skip = False

            while 1:
                u2.connect().click(x, y)
                time.sleep(1)
                u2.connect().click(638, 569)
                lo = self.pd_pos()
                while lo != "notice" and lo != "attack_formation":
                    lo = self.pd_pos()
                if lo == "notice":
                    self.main_activity[9][1] = 1
                    log.o_p("task arena finished", 1)
                    return
                elif lo == "attack_formation":
                    if not f_skip:
                        self.latest_img_array = self.get_screen_shot_array()
                        path2 = "src/arena/skip.png"
                        return_data1 = self.get_x_y(self.latest_img_array, path2)
                        print(return_data1)
                        if return_data1[1][0] <= 1e-03:
                            log.o_p("skip choice on", 1)
                        else:
                            log.o_p("skip choice off , turn on skip choice", 1)
                            u2.connect().click(1122, 602)
                            time.sleep(0.1)
                        f_skip = True
                u2.connect().click(1169, 670)
                if self.pd_pos() == "notice":
                    time.sleep(2)
                    u2.connect().click(1169, 670)
                while self.pd_pos() != "arena":
                    u2.connect().click(666, 555)

                time.sleep(45)
        elif activity == "momo_talk":
            self.click_x_y(172, 275)
            time.sleep(0.5)
            self.latest_img_array = self.get_screen_shot_array()
            path1 = "src/momo_talk/unread_mode.png"
            path2 = "src/momo_talk/newest_mode.png"
            return_data1 = self.get_x_y(self.latest_img_array,path1)
            return_data2 = self.get_x_y(self.latest_img_array,path2)
            print(return_data1)
            print(return_data2)
            if return_data1[1][0] < 1e-03:
                log.o_p("unread mode", 1)
            elif return_data2[1][0] < 1e-03:
                log.o_p("newest message mode", 1)
                log.o_p("change to unread mode", 1)
                self.click_x_y(514, 177)
                time.sleep(0.3)
                self.click_x_y(451, 297)
                time.sleep(0.3)
                self.click_x_y(451, 363)
                time.sleep(0.5)
            else:
                log.o_p("can't detect mode button quit momo_talk task", 2)
                return

            while 1:
                self.latest_img_array = self.get_screen_shot_array()
                location_y = 210
                red_dot = np.array([25, 71, 251])
                location_x = 637
                dy = 18
                unread_location = []
                while location_y <= 630:
                    if np.array_equal(self.latest_img_array[location_y][location_x],red_dot) and np.array_equal(self.latest_img_array[location_y + dy][location_x],red_dot):
                        unread_location.append([location_x, location_y+dy/2])
                        location_y += 60
                    else:
                        location_y += 1
                length = len(unread_location)
                log.o_p("find  " + str(length) + "  unread message", 1)

                if length == 0:
                    log.o_p("momo_talk task finished", 1)
                    self.main_activity[14][1] = True
                    return
                else:
                    for i in range(0, len(unread_location)):
                        self.click_x_y(unread_location[i][0], unread_location[i][1])
                        time.sleep(0.5)
                        self.common_solve_affection_story_method()
                        time.sleep(2)
                        fail_cnt = 0
                        flag = False
                        while fail_cnt <= 5:
                            if self.pd_pos("src/momo_talk/momo_talk2.png","momo_talk2") != "momo_talk2":
                                self.click_x_y(629, 105)
                                fail_cnt += 1
                                time.sleep(2)
                            else:
                                flag = True
                                break
                        if not flag:
                            return
                self.click_x_y(170, 197)
                time.sleep(0.5)
                self.click_x_y(170, 270)
                time.sleep(0.5)

    def common_solve_affection_story_method(self):
        fail_cnt = 0
        while fail_cnt <= 5:
            path1 = "src/momo_talk/reply_button.png"
            path2 = "src/momo_talk/affection story.png"
            self.latest_img_array = self.get_screen_shot_array()
            return_data1 = self.get_x_y(self.latest_img_array, path1)
            return_data2 = self.get_x_y(self.latest_img_array, path2)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] <= 1e-03:
                log.o_p("enter affection story", 1)
                self.click_x_y(return_data2[0][0] + 108, return_data2[0][1] + 45)
                time.sleep(0.5)
                self.click_x_y(925, 564)
                time.sleep(5)
                self.common_skip_plot_method()
                return True
            elif return_data1[1][0] <= 1e-03:
                fail_cnt = 0
                log.o_p("reply_message", 1)
                self.click_x_y(return_data1[0][0] + 166,return_data1[0][1] + 45)
                time.sleep(2)
            else:
                time.sleep(2)
                fail_cnt += 1
                log.o_p("can't find target button cnt = "+str(fail_cnt), 1)

    def common_create_judge(self):
        pri = ["花", "Mo", "情人节", "果冻", "色彩", "灿烂", "光芒", "玲珑", "白金", "黄金", "铜", "白银", "金属",
               "隐然"]  # 可设置参数，越靠前的节点在制造时越优先选择
        node_x = [839, 508, 416, 302, 174]
        node_y = [277, 388, 471, 529, 555]
        # 572 278
        node = []
        for i in range(0, 5):
            self.click_x_y(node_x[i], node_y[i])
            time.sleep(0.2 if i == 0 else 0.1)
            node_info = self.img_ocr(self.get_screen_shot_array())
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
        self.latest_img_array = self.get_screen_shot_array()
        path2 = "src/create/collect.png"
        path3 = "src/create/finish_instantly.png"
        return_data1 = self.get_x_y(self.latest_img_array, path2)
        return_data2 = self.get_x_y(self.latest_img_array, path3)
        while return_data1[1][0] < 1e-03 or return_data2[1][0] < 1e-03:
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
            self.latest_img_array = self.get_screen_shot_array()
            return_data1 = self.get_x_y(self.latest_img_array, path2)
            return_data2 = self.get_x_y(self.latest_img_array, path3)

    def to_main_page(self):
        while 1:
            if not self.pd_pos() == "main_page":
                self.click_x_y(1236, 39)
            else:
                break


if __name__ == '__main__':
    b_aas = baas()
    #    thread_run = threading.Thread(target=b_aas.run)
    #    thread_run.start()
    #    b_aas.main_to_page(14)
    #    print(b_aas.common_create_judge())
    #    print(b_aas.common_fight_practice())
 #   b_aas.common_skip_plot_method()
    b_aas.start_ba()
