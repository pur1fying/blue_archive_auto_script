import threading
import time

import numpy as np
import uiautomator2 as u2
from qfluentwidgets import qconfig

import module
from core.setup import Setup
from core.utils import kmp, get_x_y
from gui.components.logger_box import LoggerBox
from gui.util import log
from gui.util.config import conf


class Main(Setup):

    def __init__(self, logger_box: LoggerBox = None):
        super().__init__()
        self.unknown_ui_page_count = None
        self.loggerBox = logger_box
        self.flag_run = False
        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]

        for i in range(0, 3):  # 可设置参数 range(0,i) 中 i 表示前 i 项任务不做
            self.main_activity[i][1] = 1

    def _init_emulator(self):
        # noinspection PyBroadException
        try:
            self.connection = u2.connect()
            print(1)

            # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
            server = qconfig.get(conf.server)
            self.package_name = 'com.RoamingStar.BlueArchive' if server == '官服' else ('com.RoamingStar.BlueArchive'
                                                                                        '.bilibili')

            self.unknown_ui_page_count = 0

            self.connection.app_start(self.package_name)
            t = self.connection.window_size()
            log.d("Screen Size  " + str(t), level=1, logger_box=self.loggerBox)
            if (t[0] == 1280 and t[1] == 720) or (t[1] == 1280 and t[0] == 720):
                log.d("Screen Size Fitted", level=1, logger_box=self.loggerBox)
            else:
                log.d("Screen Size unfitted", level=4, logger_box=self.loggerBox)
                self.flag_run = False
        except Exception as e:
            log.d(e, level=3, logger_box=self.loggerBox)
            self.flag_run = False

    def send(self, msg):
        if msg == "start":
            self.start_instance()
        elif msg == "stop":
            self.flag_run = False

    def click(self, x, y):  # 点击屏幕（x，y）处
        log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
              logger_box=self.loggerBox)
        self.connection.click(x, y)
        self.set_click_time()

    def change_acc_auto(self):  # 战斗时自动开启3倍速和auto
        img1 = self.get_screen_shot_array()
        acc_r_ave = img1[625][1196][0] // 3 + img1[625][1215][0] // 3 + img1[625][1230][0] // 3
        print(acc_r_ave)
        if 250 <= acc_r_ave <= 260:
            log.d("change acceleration phase from 2 to 3", level=1, logger_box=self.loggerBox)
            self.click(1215, 625)
        elif 0 <= acc_r_ave <= 60:
            log.d("acceleration phase 3", level=1, logger_box=self.loggerBox)
        elif 140 <= acc_r_ave <= 180:
            log.d("change acceleration phase from 1 to 3", level=1, logger_box=self.loggerBox)
            self.click(1215, 625)
            self.click(1215, 625)
        else:
            log.d("can't identify acceleration button", level=2, logger_box=self.loggerBox)

        auto_r_ave = img1[677][1171][0] // 2 + img1[677][1246][0] // 2
        if 190 <= auto_r_ave <= 230:
            log.d("change manual to auto", level=1, logger_box=self.loggerBox)
            self.click(1216, 678)
        elif 0 <= auto_r_ave <= 60:
            log.d("auto", level=1, logger_box=self.loggerBox)
        else:
            log.d("can't identify auto button", level=2, logger_box=self.loggerBox)
        print(auto_r_ave)

    def common_fight_practice(self):
        self.flag_run = False
        time.sleep(1)
        self.change_acc_auto()
        while 1:
            self.latest_img_array = self.get_screen_shot_array()
            path1 = "src/common_button/check_blue.png"
            path3 = "src/common_button/fail_check.png"
            return_data1 = get_x_y(self.latest_img_array, path1)
            return_data2 = get_x_y(self.latest_img_array, path3)
            if return_data1[1][0] < 1e-03 or return_data2[1][0] < 1e-03:
                if return_data1[1][0] < 1e-03:
                    log.d("fight succeeded", level=1, logger_box=self.loggerBox)
                    success = True
                    self.click(return_data1[0][0], return_data1[0][1])
                else:
                    log.d("fight failed", level=1, logger_box=self.loggerBox)
                    success = False
                    self.click(return_data2[0][0], return_data2[0][1])
                break
            else:
                self.click(767, 500)
                log.d("fighting", level=1, logger_box=self.loggerBox)
            time.sleep(2)

        thread_run = threading.Thread(target=self.run)
        thread_run.start()

        if not success:
            while 1:
                self.latest_img_array = self.get_screen_shot_array()
                path2 = "src/common_button/fail_check.png"
                return_data1 = get_x_y(self.latest_img_array, path2)
                if return_data1[1][0] < 1e-03:
                    log.d("Fail Back", level=1, logger_box=self.loggerBox)
                    self.click(return_data1[0][0], return_data1[0][1])
                    break
                time.sleep(2)
        else:
            while 1:
                self.latest_img_array = self.get_screen_shot_array()
                path2 = "src/common_button/check_yellow.png"
                return_data1 = get_x_y(self.latest_img_array, path2)
                print(return_data1[1][0])
                if return_data1[1][0] < 1e-03:
                    log.d("reward collected success back", level=1, logger_box=self.loggerBox)
                    self.click(return_data1[0][0], return_data1[0][1])
                    break
                time.sleep(2)

        time.sleep(5)
        return success

    def special_task_common_operation(self, a, b, f=True):
        special_task_lox = 1120
        special_task_loy = [180, 286, 386, 489, 564, 432, 530, 628]
        fail_cnt = 0
        difficulty_name = ["A", "B", "C", "D", "E", "F", "G", "H"]
        img_shot = self.get_screen_shot_array()
        ocr_res = self.img_ocr(img_shot)

        highest_level = 8

        for i in range(0, 3):
            if kmp(difficulty_name[i], ocr_res):
                highest_level = i + 1
                break

        if a >= highest_level: #肯定未通关
            log.d("UNLOCKED", level=2, logger_box=self.loggerBox)
            return True

        log.d("-------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("try to swipe to TOP page", level=1, logger_box=self.loggerBox)
        while fail_cnt <= 3:
            log.d("swipe", level=1, logger_box=self.loggerBox)
            self.connection.swipe(916, 200, 916, 460, 0.1)
            time.sleep(1)
            img_shot = self.get_screen_shot_array()
            ocr_res = self.img_ocr(img_shot)
            if kmp("A", ocr_res) == 0:
                fail_cnt += 1
                if fail_cnt <= 3:
                    log.d("TRY AGAIN", 1, logger_box=self.loggerBox)
                else:
                    log.d("FAIL to swipe to TOP page", level=2, logger_box=self.loggerBox)
                    log.d("-------------------------------------------------------------------------------", 1,
                          logger_box=self.loggerBox)
                    return False
            else:
                log.d("SUCCESSFULLY swipe to TOP page", level=1, logger_box=self.loggerBox)
                log.d("-------------------------------------------------------------------------------", 1,
                      logger_box=self.loggerBox)
                break

        if a >= 6:
            fail_cnt = 0
            log.d("-------------------------------------------------------------------------------", 1,
                  logger_box=self.loggerBox)
            log.d("try to swipe to LOWEST page", level=1, logger_box=self.loggerBox)
            while fail_cnt <= 3:
                log.d("swipe", level=1, logger_box=self.loggerBox)
                self.connection.swipe(916, 460, 916, 200, 0.1)
                time.sleep(1)
                img_shot = self.get_screen_shot_array()
                ocr_res = self.img_ocr(img_shot)
                if kmp("D", ocr_res) == 0 or kmp("A", ocr_res) != 0:
                    fail_cnt += 1
                    if fail_cnt <= 3:
                        log.d("TRY AGAIN", 1, logger_box=self.loggerBox)
                    else:
                        log.d("FAIL to swipe to LOWEST page", level=2, logger_box=self.loggerBox)
                        log.d("-------------------------------------------------------------------------------", 1,
                              logger_box=self.loggerBox)
                        return False
                else:
                    log.d("SUCCESSFULLY swipe to LOWEST page", level=1, logger_box=self.loggerBox)
                    log.d("-------------------------------------------------------------------------------", 1,
                          logger_box=self.loggerBox)
                    break

        self.click(special_task_lox, special_task_loy[a - 1])

        if self.pd_pos() == "notice":
            log.d("UNLOCKED", level=2, logger_box=self.loggerBox)
        else:
            for i in range(0, b - 1):
                self.click(1033, 297)
                if f:
                    time.sleep(0.6)
                else:
                    time.sleep(0.2)
            self.click(937, 404)
            lo = self.pd_pos()
            if lo == "charge_power":
                log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
            elif lo == "charge_notice":
                log.d("inadequate ticket , exit task", level=3, logger_box=self.loggerBox)
            elif lo == "notice":
                self.click(767, 501)
                time.sleep(2)
            else:
                log.d("AUTO FIGHT UNLOCKED , exit task", level=3, logger_box=self.loggerBox)
        return True
    def main_to_page(self, index, path=None, name=None):
        self.to_page[7] = [[217, 940], [659, self.schedule_lo_y[self.schedule_pri[0] - 1]],
                           ["schedule", "schedule" + str(self.schedule_pri[0])]]
        procedure = self.to_page[index]
        step = 0
        if len(procedure) != 0:
            step = len(procedure[0])
        if step:
            log.d("begin main to page " + str(procedure[2][step - 1]), level=1, logger_box=self.loggerBox)
        i = 0
        times = 0
        while i != step:
            x = procedure[0][i]
            y = procedure[1][i]
            page = procedure[2][i]
            self.click(x, y)
            if self.pd_pos(path=path, name=name) != page:
                if times <= 1:
                    times += 1
                    log.d("not in page " + str(page) + " , count = " + str(times), level=2, logger_box=self.loggerBox)
                elif times == 2:
                    log.d("not in page " + str(page) + " , return to main page", level=2, logger_box=self.loggerBox)
                    self.to_main_page()
                    times = 0
                    i = 0
            else:
                times = 0
                i += 1

    def start_instance(self):
        self._init_emulator()
        self.thread_starter()

    def get_screen_shot_array(self):
        screenshot = self.connection.screenshot()
        numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
        return numpy_array

    def worker(self):
        shot_time = time.time() - self.base_time
        # print(shot_time)
        self.latest_img_array = self.get_screen_shot_array()
        ct = time.time()
        self.get_keyword_appear_time(self.img_ocr(self.latest_img_array))
        #  print("shot time", shot_time,"click time",self.click_time)
        locate_res = self.return_location()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, shot_time])
        if len(self.pos) > 2:
            #     print("exceed len 2", shot_time)
            self.pos.pop()

    def common_positional_bug_detect_method(self, pos, x, y, times=3, any=False, path=None, name=None):
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("BEGIN DETECT POSITION " + pos.upper(), 1, logger_box=self.loggerBox)
        cnt = 1
        while self.pd_pos(path=path, name=name, anywhere=any) != pos and cnt <= times:
            log.d("FAIL TIME : " + str(cnt), 2, logger_box=self.loggerBox)
            cnt += 1
            self.click(x, y)
            time.sleep(2)
        if cnt == times + 1:
            log.d("CAN'T DETECT POSITION " + pos.upper(), 3, logger_box=self.loggerBox)
            log.d("------------------------------------------------------------------------------------------------", 1,
                  logger_box=self.loggerBox)
            return False

        else:
            log.d("SUCCESSFULLY DETECT POSITION " + pos.upper(), 1, logger_box=self.loggerBox)
            log.d("------------------------------------------------------------------------------------------------", 1,
                  logger_box=self.loggerBox)
            return True

    def run(self):

        log.d("start getting screenshot", 1, self.loggerBox)
        while self.flag_run:
            ts = threading.Thread(target=self.worker)
            ts.start()
            time.sleep(1)
            # print(f'{self.flag_run}')
            # 可设置参数 time.sleep(i) 截屏速度为i秒/次，越快程序作出反映的时间便越快，
            # 同时对电脑的性能要求也会提高，目前推荐设置为1，后续优化后可以设置更低的值
        log.d("stop getting screenshot", 1, self.loggerBox)

    def thread_starter(self):  # 不要每次点击启动都跑这个
        thread_run = threading.Thread(target=self.run)
        thread_run.start()
        lo = self.pd_pos(anywhere=True)
        while lo != "main_page" and lo != "notice" and lo != "main_notice":
            self.click(1236, 39)
            self.click(108, 368)
            lo = self.pd_pos(anywhere=True)
        if lo == "main_notice":
            self.click(1138, 101)
        elif lo == "notice":
            self.click(763, 500)
        log.line(self.loggerBox)
        log.d("start activities", level=1, logger_box=self.loggerBox)
        for i in range(0, len(self.main_activity)):
            print(self.main_activity[i][0], self.main_activity[i][1])
            if self.main_activity[i][1] == 0:
                log.line(self.loggerBox)
                print(self.main_activity[i][0])
                log.d("begin " + self.main_activity[i][0] + " task", level=1, logger_box=self.loggerBox)
                if i != 14:
                    self.to_main_page()
                    self.main_to_page(i)
                self.solve(self.main_activity[i][0])
                print(self.main_activity[i][0], self.main_activity[i][1])
        count = 0
        for i in range(0, len(self.main_activity)):
            if self.main_activity[i][1] == 1:
                count += 1
        if count == 13:
            self.flag_run = False

    def pd_pos(self, path=None, name=None, anywhere=False):
        if path:
            return_data = get_x_y(self.latest_img_array, path)
            print(return_data)
            if return_data[1][0] <= 1e-03:
                log.d("current_location : " + name, 1, logger_box=self.loggerBox)
                return name
        while len(self.pos) > 0 and self.pos[len(self.pos) - 1][1] < self.click_time:
            self.pos.pop()
        while 1:
            if len(self.pos) == 2 and self.pos[0][0] == self.pos[1][0]:
                lo = self.pos[0][0]
                self.pos.clear()
                if lo == "UNKNOWN UI PAGE":
                    if anywhere:
                        log.d("anywhere accepted", 1, logger_box=self.loggerBox)
                        return "click_anywhere"
                    elif self.unknown_ui_page_count < 20:
                        self.unknown_ui_page_count += 1
                        log.d("UNKNOWN UI PAGE COUNT:" + str(self.unknown_ui_page_count), 2,
                              logger_box=self.loggerBox)
                    elif self.unknown_ui_page_count == 20:
                        log.d("Unknown ui page", 3, logger_box=self.loggerBox)
                        self.flag_run = False
                else:
                    self.unknown_ui_page_count = 0
                    log.d("current_location : " + lo, 1, logger_box=self.loggerBox)
                    return lo
            time.sleep(1)

    def solve(self, activity):
        try:
            module.__dict__[activity].implement(self)
        except Exception as e:
            log.d(e, level=3, logger_box=self.loggerBox)
            self.flag_run = False

    def to_main_page(self):
        while not self.pd_pos() == "main_page":
            self.click(1236, 39)

if __name__ == "__main__":
    t = Main()
    t._init_emulator()
    a = t.get_screen_shot_array()
    print(t.img_ocr(a))
    t.get_keyword_appear_time(t.img_ocr(a))
    print(t.return_location())
