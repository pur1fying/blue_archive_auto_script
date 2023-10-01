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

        for i in range(0, 14):  # 可设置参数 range(0,i) 中 i 表示前 i 项任务不做
            self.main_activity[i][1] = 1

    def _init_emulator(self):
        # noinspection PyBroadException
        try:
            self.connection = u2.connect()
            print(1)

            # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
            server = qconfig.get(conf.server)
            self.package_name = 'com.RoamingStar.BlueArchive' if server == '官服' else 'com.RoamingStar.BlueArchive.bilibili'

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
        self.set_click_time()
        log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
              logger_box=self.loggerBox)
        time.sleep(0.5)
        self.connection.click(x, y)

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
        self.connection.swipe(916, 160, 916, 680, 0.1)
        time.sleep(0.5)
        log.d("swipe", level=1, logger_box=self.loggerBox)
        if a >= 6:
            self.connection.swipe(916, 680, 916, 160, 0.1)
            log.d("swipe", level=1, logger_box=self.loggerBox)
            time.sleep(1)

        self.click(special_task_lox, special_task_loy[a - 1])
        if self.pd_pos() == "notice":
            log.d("UNLOCKED", level=3, logger_box=self.loggerBox)
        else:
            for i in range(0, b - 1):
                self.click(1033, 297)
                if f:
                    time.sleep(0.6)
            self.click(937, 404)
        lo = self.pd_pos()
        if lo == "charge_power":
            log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
        elif lo == "charge_notice":
            log.d("inadequate ticket , exit task", level=3, logger_box=self.loggerBox)
        else:
            self.click(767, 501)

    def main_to_page(self, index):
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
            if self.pd_pos() != page:
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
        self.latest_img_array = self.get_screen_shot_array()
        self.get_keyword_appear_time(self.img_ocr(self.latest_img_array))
        locate_res = self.return_location()
        ct = time.time()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, ct - self.base_time])
        if len(self.pos) > 2:
            self.pos.pop()

    def run(self):

        log.d("start getting screenshot", 1, self.loggerBox)
        while self.flag_run:
            ts = threading.Thread(target=self.worker)
            ts.start()
            time.sleep(0.5)
            # print(f'{self.flag_run}')
            # 可设置参数 time.sleep(i) 截屏速度为i秒/次，越快程序作出反映的时间便越快，
            # 同时对电脑的性能要求也会提高，目前推荐设置为1，后续优化后可以设置更低的值
        log.d("stop getting screenshot", 1, self.loggerBox)

    def thread_starter(self):
        thread_run = threading.Thread(target=self.run)
        thread_run.start()
        lo = self.pd_pos()
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
                self.to_main_page()
                self.main_to_page(i)
                self.solve(self.main_activity[i][0])
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

    def common_create_judge(self):
        pri = self.pri  # 可设置参数，越靠前的节点在制造时越优先选择
        node_x = [839, 508, 416, 302, 174]
        node_y = [277, 388, 471, 529, 555]
        # 572 278
        node = []
        for i in range(0, 5):
            self.click(node_x[i], node_y[i])
            time.sleep(0.5 if i == 0 else 0.1)
            node_info = self.img_ocr(self.get_screen_shot_array())
            for k in range(0, len(pri)):
                if kmp(pri[k], node_info) > 0:
                    if k == 0:
                        log.d("choose node :" + pri[0], level=1, logger_box=self.loggerBox)
                        return i
                    else:
                        node.append(pri[k])
        log.d("detected nodes:" + str(node), 1, logger_box=self.loggerBox)
        for i in range(1, len(pri)):
            for j in range(0, len(node)):
                if node[j][0:len(pri[i])] == pri[i]:
                    log.d("choose node :" + pri[i], level=1, logger_box=self.loggerBox)
                    return j

    def common_create_collect_operation(self):
        self.latest_img_array = self.get_screen_shot_array()
        path2 = "./src/create/collect.png"
        path3 = "./src/create/finish_instantly.png"
        return_data1 = get_x_y(self.latest_img_array, path2)
        return_data2 = get_x_y(self.latest_img_array, path3)
        print(return_data1)
        print(return_data2)
        while return_data1[1][0] < 1e-03 or return_data2[1][0] < 1e-03:
            if return_data1[1][0] < 0.01:
                log.d("collect finished creature", level=1, logger_box=self.loggerBox)
                self.click(return_data1[0][0], return_data1[0][1])
                time.sleep(2)
                self.click(628, 665)
                time.sleep(1)
            if return_data2[1][0] < 0.01:
                log.d("accelerate unfinished creature", level=1, logger_box=self.loggerBox)
                self.click(return_data2[0][0], return_data2[0][1])
                time.sleep(0.5)
                self.click(775, 477)
                time.sleep(2)
            self.latest_img_array = self.get_screen_shot_array()
            return_data1 = get_x_y(self.latest_img_array, path2)
            return_data2 = get_x_y(self.latest_img_array, path3)

    def to_main_page(self):
        while True:
            if not self.pd_pos() == "main_page":
                self.click(1236, 39)
            else:
                break


# if __name__ == '__main__':
#    thread_run = threading.Thread(target=b_aas.run)
#    thread_run.start()
#    b_aas.main_to_page(14)
#    print(b_aas.common_create_judge())
#    print(b_aas.common_fight_practice())
# Main().solve("arena")


if __name__ == "__main__":
    t = Main()
    t.start_instance()
    a = t.get_screen_shot_array()
    print(t.img_ocr(a))
    t.get_keyword_appear_time(t.img_ocr(a))
    print(t.return_location())
