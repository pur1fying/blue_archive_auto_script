import os
import threading
import time

import cv2
import numpy as np
import uiautomator2 as u2
from cnocr import CnOcr

import module
from core.exception import ScriptError
from core.scheduler import Scheduler
from core.setup import Setup
from core.utils import kmp, get_x_y, pd_rgb
# from debug.debugger import start_debugger
from gui.util import log
from gui.util.config_set import ConfigSet


class Main(Setup):

    def __init__(self, logger_box=None, button_signal=None, update_signal=None):
        super().__init__()
        self.ocr = None
        self.loggerBox = logger_box
        self.config = ConfigSet()
        self.total_force_fight_difficulty_name = ["NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME"]
        self.total_force_fight_name = "white_and_black"
        self.screenshot_flag_run = None
        self.unknown_ui_page_count = None
        self.io_err_solved_count = 0
        self.io_err_count = 0
        self.io_err_rate = 10
        self.screenshot_interval = 0.5
        self.button_signal = button_signal
        self.flag_run = True
        self.click_interval = 3
        self._server_record = ''
        self._first_started = True
        self.connection = None
        self.activity_name_list = self.main_activity.copy()
        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]
        try:
            self.common_task_count = self.config.get('mainlinePriority')  # **可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(普通)打k次
            self.hard_task_count = self.config.get('hardPriority')  # **可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(困难)打k次
            if self.common_task_count == '':
                self.common_task_count = []
            else:
                self.common_task_count = [tuple([int(y) for y in x.split('-')]) for x in
                                          self.common_task_count.split(',')]
            if self.hard_task_count == '':
                self.hard_task_count = []
            else:
                self.hard_task_count = [tuple([int(y) for y in x.split('-')]) for x in
                                        self.hard_task_count.split(',')]
        except ValueError as e:
            self.common_task_count = []
            self.hard_task_count = []

        self.common_task_status = np.full(len(self.common_task_count), False, dtype=bool)
        self.hard_task_status = np.full(len(self.hard_task_count), False, dtype=bool)
        self.scheduler = Scheduler(update_signal)
        # start_debugger()

    def _init_emulator(self) -> bool:
        # noinspection PyBroadException
        print("--------init emulator----------")
        try:
            server = self.config.get('server')
            self.package_name = 'com.RoamingStar.BlueArchive' \
                if server == '官服' else 'com.RoamingStar.BlueArchive.bilibili'
            self.adb_port = self.config.get('adbPort')
            if not self._first_started and self._server_record == server:
                return True
            if not self.adb_port or self.adb_port == '0':
                self.connection = u2.connect()
            else:
                self.connection = u2.connect(f'127.0.0.1:{self.adb_port}')
            # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
            # emulator_path = qconfig.get(conf.emulatorPath)
            # if emulator_path:
            #     log.d("Emulator path: " + emulator_path, level=1, logger_box=self.loggerBox)
            #     log.d("Emulator is starting...", level=1, logger_box=self.loggerBox)
            #     subprocess.run(['start', emulator_path, '-avd', 'Pixel_2_API_29', '-port', '7555'])
            #     # time.sleep(10)
            #     log.d("Emulator has been started.", level=1, logger_box=self.loggerBox)

            self.unknown_ui_page_count = 0
            self.connection.app_start(self.package_name)
            t = self.connection.window_size()
            log.d("Screen Size  " + str(t), level=1, logger_box=self.loggerBox)
            if (t[0] == 1280 and t[1] == 720) or (t[1] == 1280 and t[0] == 720):
                log.d("Screen Size Fitted", level=1, logger_box=self.loggerBox)
            else:
                log.d("Screen Size unfitted", level=4, logger_box=self.loggerBox)
                self.send('stop')
                return False
            self._first_started = False
            self._server_record = server
            if not self.ocr:
                self.ocr = CnOcr(rec_model_name='densenet_lite_114-fc')
            print("--------Emulator Init Finished----------")
            return True
        except Exception as e:
            threading.Thread(target=self.simple_error, args=(e.__str__(),)).start()
            return False

    def get_x_y(self, target_array, path):
        # print(target_array.dtype)
        if path.startswith("./src"):
            path = path.replace("./src", "src")
        elif path.startswith("../src"):
            path = path.replace("../src", "src")
        img1 = target_array
        img2 = cv2.imread(path)
        if img2 is None:
            return [[-1, -1], [1]]
        # sys.stdout = open('data.log', 'w+')
        height, width, channels = img2.shape
        #    print(img2.shape)
        #    for i in range(0, height):
        #        print([x for x in img2[i, :, 0]])
        result = cv2.matchTemplate(img1, img2, cv2.TM_SQDIFF_NORMED)
        upper_left = cv2.minMaxLoc(result)[2]
        #    print(img1.shape)
        #    print(upper_left[0], upper_left[1])
        # cv2.imshow("img2", img2)
        converted = img1[upper_left[1]:upper_left[1] + height, upper_left[0]:upper_left[0] + width, :]
        #     cv2.imshow("img1", converted)
        sub = cv2.subtract(img2, converted)
        # cv2.imshow("result", cv2.subtract(img2, converted))
        # for i in range(0, height):
        #    print([x for x in converted[i, :, 0]])
        # cv2.imshow("img1", img1)
        # cv2.waitKey(0)
        location = (int(upper_left[0] + width / 2), int(upper_left[1] + height / 2))
        return location, result[upper_left[1], [upper_left[0]]]

    def send(self, msg):
        # try:
        if msg == "start":
            self.button_signal.emit("停止")
            self.start_instance()
        elif msg == "stop":
            self.button_signal.emit("启动")
            self.flag_run = False

    #         except Exception as e:

    #             log.d(e, level=3, logger_box=self.loggerBox)
    #             self.send('stop')

    def operation(self, operation_name, operation_locations=None, duration=0.0, path=None, name=None, anywhere=False):
        if not self.flag_run:
            return False
            # raise Exception("Shutdown")
        if operation_name[0:5] == "click":
            x = operation_locations[0]
            y = operation_locations[1]
            log.d(
                operation_name + ":(" + str(x) + " " + str(y) + ")" + " click_time = " + str(round(self.click_time, 3)),
                level=1,
                logger_box=self.loggerBox)
            noisex = np.random.uniform(-5,5)
            noisey = np.random.uniform(-5, 5)
            self.connection.click(x + noisex, y + noisey)
            self.set_click_time()

            time.sleep(duration)
            return "click success"
        elif operation_name == "swipe":
            x1 = operation_locations[0][0]
            y1 = operation_locations[0][1]
            x2 = operation_locations[1][0]
            y2 = operation_locations[1][1]
            self.connection.swipe(x1, y1, x2, y2, duration=duration)
            return "swipe success"
        elif operation_name == "stop_getting_screenshot_for_location":
            log.d("STOP getting screenshot for location", 1, logger_box=self.loggerBox)
            self.screenshot_flag_run = False
            return True
        elif operation_name == "start_getting_screenshot_for_location":
            log.d("START getting screenshot for location", 1, logger_box=self.loggerBox)
            self.screenshot_flag_run = True
            screenshot_thread = threading.Thread(target=self.run)
            screenshot_thread.start()
            return True
        elif operation_name == "get_current_position":
            if path:
                self.latest_img_array = self.operation("get_screenshot_array")
                return_data = get_x_y(self.latest_img_array, path)
                print(return_data)
                if return_data[1][0] <= 1e-03:
                    log.d("current_location : " + name, 1, logger_box=self.loggerBox)
                    time.sleep(self.screenshot_interval)
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
                            self.signal_stop()
                            return "UNKNOWN UI PAGE"
                            # exit(0)
                    else:
                        self.unknown_ui_page_count = 0
                        log.d("current_location : " + lo, 1, logger_box=self.loggerBox)
                        return lo
                time.sleep(self.screenshot_interval)
        elif operation_name == "get_screenshot_array":
            # try:
            #     screenshot = self.connection.screenshot()
            #     numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
            #     if abs(int(self.screenshot_interval * 100) - 50) > 1e-05:
            #         if self.io_err_solved_count == self.io_err_rate:
            #             log.d("The IOError cease to happen.", level=1, logger_box=self.loggerBox)
            #             log.d("Trying reducing the screenshot interval by 0.1s.", level=1, logger_box=self.loggerBox)
            #             self.screenshot_interval -= 0.1
            #             self.io_err_solved_count = 0
            #             self.io_err_count = max(self.io_err_count - 1, 0)
            #         else:
            #             self.io_err_solved_count += 1
            #     return numpy_array
            # except Exception as e:
            #     log.d("The IOError happened! Trying add the screenshot interval by 0.1s.",
            #           level=3, logger_box=self.loggerBox)
            #     if self.io_err_count >= self.io_err_rate:
            #         self.screenshot_interval += 0.1
            #         self.io_err_count = 0
            #     self.io_err_count += 1
            #     log.d(f'{e}! Trying screenshot again...', level=3, logger_box=self.loggerBox)
            #     time.sleep(1 + int(self.screenshot_interval))
            #     return None
            screenshot = self.connection.screenshot()
            numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
            return numpy_array

    def signal_stop(self):
        self.flag_run = False
        self.button_signal.emit("启动")

    def change_acc_auto(self):  # 战斗时自动开启3倍速和auto
        img1 = self.operation("get_screenshot_array")
        acc_r_ave = img1[625][1196][0] // 3 + img1[625][1215][0] // 3 + img1[625][1230][0] // 3
        print(acc_r_ave)
        if 250 <= acc_r_ave <= 260:
            log.d("CHANGE acceleration phase from 2 to 3", level=1, logger_box=self.loggerBox)
            self.operation("click@accleration", (1215, 625))
        elif 0 <= acc_r_ave <= 60:
            log.d("ACCELERATION phase 3", level=1, logger_box=self.loggerBox)
        elif 140 <= acc_r_ave <= 180:
            log.d("CHANGE acceleration phase from 1 to 3", level=1, logger_box=self.loggerBox)
            self.operation("click@accelereation", (1215, 625))
            self.operation("click@acceleration", (1215, 625))
        else:
            log.d("CAN'T DETECT acceleration BUTTON", level=2, logger_box=self.loggerBox)
        auto_r_ave = img1[677][1171][0] // 2 + img1[677][1246][0] // 2
        if 190 <= auto_r_ave <= 230:
            log.d("CHANGE MANUAL to auto", level=1, logger_box=self.loggerBox)
            self.operation("click@auto", (1215, 678))
        elif 0 <= auto_r_ave <= 60:
            log.d("AUTO", level=1, logger_box=self.loggerBox)
        else:
            log.d("can't identify auto button", level=2, logger_box=self.loggerBox)
        print(auto_r_ave)

    def common_fight_practice(self):

        flag = False
        for i in range(0, 20):
            img_shot = self.latest_img_array
            if pd_rgb(img_shot, 838, 690, 45, 65, 200, 220, 240, 255):
                flag = True
                break
            else:
                lo = self.operation("get_current_position", anywhere=True)
                if lo == "notice" or lo == "summary":
                    self.operation("click @confirm", (769, 500), duration=3)

                path = "src/common_button/plot_menu.png"
                return_data = get_x_y(img_shot, path)
                if return_data[1][0] <= 1e-03:
                    log.d("SKIP PLOT", level=1, logger_box=self.loggerBox)
                    self.operation("click @plot_menu", (return_data[0][0], return_data[0][1]), duration=0.5)
                    self.operation("click @skip plot", (1207, 123), duration=1)
                    self.operation("click @confirm", (766, 527), duration=1)
                    continue
                else:
                    self.operation("click @anywhere", (1150, 649), duration=1)

        if not flag:
            return False

        self.operation("stop_getting_screenshot_for_location")

        self.change_acc_auto()

        while 1:
            self.latest_img_array = self.operation("get_screenshot_array")
            path1 = "src/common_button/check_blue.png"
            path3 = "src/common_button/fail_check.png"
            return_data1 = get_x_y(self.latest_img_array, path1)
            return_data2 = get_x_y(self.latest_img_array, path3)
            if return_data1[1][0] < 1e-03 or return_data2[1][0] < 1e-03:
                if return_data1[1][0] < 1e-03:
                    log.d("fight succeeded", level=1, logger_box=self.loggerBox)
                    success = True
                    self.operation("click@confirm", (return_data1[0][0], return_data1[0][1]))
                else:
                    log.d("fight failed", level=1, logger_box=self.loggerBox)
                    success = False
                    self.operation("click@confirm", (return_data2[0][0], return_data2[0][1]))
                break
            else:
                self.operation("click", (767, 500))
                log.d("fighting", level=1, logger_box=self.loggerBox)
            time.sleep(1)

        self.operation("start_getting_screenshot_for_location")

        if not success:
            while 1:
                time.sleep(1)
                self.latest_img_array = self.operation("get_screenshot_array")
                path2 = "src/common_button/fail_back.png"
                return_data1 = get_x_y(self.latest_img_array, path2)
                if return_data1[1][0] < 1e-03:
                    log.d("Fail Back", level=1, logger_box=self.loggerBox)
                    self.operation("click@confirm", (return_data1[0][0], return_data1[0][1]))
                    break
        else:
            self.common_positional_bug_detect_method("fight_success", 1171, 60)
            self.operation("click@confirm", (772, 657))

        time.sleep(4)
        return success

    def special_task_common_operation(self, a, b, f=True):
        special_task_lox = 1120
        special_task_loy = [180, 286, 386, 489, 564, 432, 530, 628]
        fail_cnt = 0
        # difficulty_name = ["A", "B", "C", "D", "E", "F", "G", "H"]
        log.d("-------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("try to swipe to TOP page", level=1, logger_box=self.loggerBox)
        # ocr_result = self.img_ocr(img_shot)
        while fail_cnt <= 3:
            log.d("SWIPE UPWARDS", level=1, logger_box=self.loggerBox)
            self.operation("swipe", [(762, 200), (762, 460)], duration=0.1)
            time.sleep(1)
            img_shot = self.operation("get_screenshot_array")
            ocr_result = self.img_ocr(img_shot)
            if kmp("A", ocr_result) == 0:
                fail_cnt += 1
                if fail_cnt <= 3:
                    log.d("FAIL , TRY AGAIN", 1, logger_box=self.loggerBox)
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
                log.d("SWIPE DOWNWARDS", level=1, logger_box=self.loggerBox)
                self.operation("swipe", [(762, 460), (762, 200)], duration=0.1)
                time.sleep(1)
                img_shot = self.operation("get_screenshot_array")
                ocr_res = self.img_ocr(img_shot)
                if (kmp("H", ocr_res) == 0 and kmp("G", ocr_res) == 0 and kmp("F", ocr_res) == 0 and kmp("E",
                                                                                                         ocr_res) == 0) or kmp(
                    "A", ocr_res) != 0:
                    print(ocr_res)
                    fail_cnt += 1
                    if fail_cnt <= 3:
                        log.d("FAIL , TRY AGAIN", 1, logger_box=self.loggerBox)
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

        self.operation("click", (special_task_lox, special_task_loy[a - 1]))

        if self.operation("get_current_position") == "notice":
            log.d("UNLOCK", level=2, logger_box=self.loggerBox)
            self.operation("click", (1240, 39))
            self.operation("click", (1240, 39))
        else:
            for i in range(0, b - 1):
                if f:
                    self.operation("click", (1033, 297), duration=0.6)
                else:
                    self.operation("click", (1033, 297), duration=0.2)
            self.operation("click", (937, 404),duration=0.5)
            lo = self.operation("get_current_position")
            if lo == "charge_power":
                log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
                self.operation("click", (1240, 39))
                self.operation("click", (1240, 39))
                self.operation("click", (1240, 39))
            elif lo == "charge_notice":
                log.d("inadequate ticket , exit task", level=3, logger_box=self.loggerBox)
                self.operation("click", (1240, 39))
                self.operation("click", (1240, 39))
                self.operation("click", (1240, 39))

            elif lo == "notice":
                self.operation("click", (767, 501), duration=2)
            else:
                log.d("AUTO FIGHT UNLOCK , exit task", level=3, logger_box=self.loggerBox)
        return True

    def main_to_page(self, index, path=None, name=None, any=False):
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
        while i != step and self.flag_run:
            x = procedure[0][i]
            y = procedure[1][i]
            page = procedure[2][i]
            self.operation("click", (x, y))
            if self.operation("get_current_position", path=path, name=name, anywhere=any) != page:
                if times <= 1:
                    times += 1
                    log.d("not in page " + str(page) + " , count = " + str(times), level=2, logger_box=self.loggerBox)
                elif times == 2:
                    log.d("not in page " + str(page) + " , return to main page", level=2, logger_box=self.loggerBox)
                    self.common_positional_bug_detect_method("main_page", 1240, 37, anywhere=any, path=path, name=name)
                    times = 0
                    i = 0
            else:
                times = 0
                i += 1

    def start_instance(self):
        if self._init_emulator():
            self.thread_starter()

    def worker(self):

        shot_time = time.time() - self.base_time
        self.latest_img_array = self.operation("get_screenshot_array")
        ct = time.time()

        self.get_keyword_appear_time(self.img_ocr(self.latest_img_array))
        # print("shot time", shot_time,"click time",self.click_time)

        locate_res = self.return_location()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, shot_time])
        if len(self.pos) > 2:
            #        print("exceed len 2", shot_time)
            self.pos.pop()

    def common_icon_bug_detect_method(self, path, x, y, name, times=3,interval=0.5):
        if not self.flag_run:
            return False
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("BEGIN DETECT ICON FOR " + name.upper(), 1, logger_box=self.loggerBox)
        cnt = 1
        path = path
        return_data = self.get_x_y(self.operation("get_screenshot_array"), path)
        print(return_data)
        while cnt <= times:
            if not self.flag_run:
                return False

            if return_data[1][0] <= 1e-03:
                log.d("SUCCESSFULLY DETECT POSITION FOR " + name.upper(), 1, logger_box=self.loggerBox)
                log.d(

                    "------------------------------------------------------------------------------------------------",
                    1, logger_box=self.loggerBox)
                return True
            log.d("FAIL TIME : " + str(cnt) + " min_val: " + str(return_data[1][0]), 2, logger_box=self.loggerBox)
            cnt += 1
            self.operation("click", (x, y), duration=interval)
            return_data = self.get_x_y(self.operation("get_screenshot_array"), path)
            print(return_data)

        log.d("CAN'T DETECT BUTTON FOR " + name.upper(), 3, logger_box=self.loggerBox)
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        return False

    def common_positional_bug_detect_method(self, pos, x, y, times=3, anywhere=False, path=None, name=None):
        if not self.flag_run:
            return False
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("BEGIN DETECT POSITION " + pos.upper(), 1, logger_box=self.loggerBox)
        cnt = 1
        t = self.operation("get_current_position", path=path, name=name, anywhere=anywhere)
        while cnt <= times:
            if not self.flag_run:
                return False
            if t == pos:
                log.d("SUCCESSFULLY DETECT POSITION " + pos.upper(), 1, logger_box=self.loggerBox)
                log.d(
                    "------------------------------------------------------------------------------------------------",
                    1,
                    logger_box=self.loggerBox)
                return True
            log.d("FAIL TIME : " + str(cnt), 2, logger_box=self.loggerBox)
            cnt += 1
            self.operation("click", (x, y), duration=self.screenshot_interval)

            t = self.operation("get_current_position", path=path, name=name, anywhere=anywhere)

        log.d("CAN'T DETECT POSITION " + pos.upper(), 3, logger_box=self.loggerBox)
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        return False

    def quick_method_to_main_page(self):
        log.d("TO MAIN PAGE", 1, logger_box=self.loggerBox)
        image_names = [
            "back_to_main_page",
            "menu",
            "skip_plot_button",
            "back_to_home",
            "cross4",
            "momotalk_cross",
            "cross1",
            "cross2",
            "cross3",
            "cross6",
            "cross5",
        ]
        lo = self.operation("get_current_position", anywhere=True)
        while lo != "main_page" and self.flag_run:
            print(lo)
            last_x = -1
            last_y = -1
            cnt = 0
            click_flag = False
            ocr_res = self.img_ocr(self.latest_img_array)
            if lo == "notice":
                self.operation("click@confirm", (767, 501))
            if ocr_res != "":
                if kmp(ocr_res, "是否跳过"):
                    self.operation("click@skip", (765, 500))
                    continue
            for image_name in image_names:
                path = os.path.join("src/common_button/", image_name + ".png")
                # print(image_name)
                return_data = get_x_y(self.latest_img_array, path)
                #   print(return_data)
                #   print(return_data)
                if return_data[1][0] <= 1e-03:
                    click_flag = True
                    self.operation("click", (return_data[0][0], return_data[0][1]))
                    if image_name == "skip_plot_button":
                        time.sleep(0.5)
                        self.operation("click", (770, 518))
                    break
                elif abs(last_x - return_data[0][0]) <= 5 and abs(last_y - return_data[0][1]) <= 5:
                    cnt += 1
                    if cnt == 4:
                        click_flag = True
                        self.operation("click", (last_x, last_y))
                        break
                last_x = return_data[0][0]
                last_y = return_data[0][1]
            if not click_flag:
                self.operation("click", (1239, 24))
                self.operation("click", (330, 345))

            lo = self.operation("get_current_position", anywhere=True)

    def run(self):
        while self.screenshot_flag_run and self.flag_run:
            threading.Thread(target=self.worker, daemon=True).start()
            # self.worker()
            time.sleep(self.screenshot_interval)
            # print(f'{self.flag_run}')
            # 可设置参数 time.sleep(i) 截屏速度为i秒/次，越快程序作出反映的时间便越快，
            # 同时对电脑的性能要求也会提高，目前推荐设置为1，后续优化后可以设置更低的值
        print("run stop")

    def thread_starter(self):  # 不要每次点击启动都跑这个
        self.operation("start_getting_screenshot_for_location")
        self.quick_method_to_main_page()
        log.line(self.loggerBox)
        log.d("start activities", level=1, logger_box=self.loggerBox)
        print('--------------Start activities...---------------')
        print(self.main_activity)
        # self.main_to_page(4)
        # self.solve(self.main_activity[4][0])
        # for i in range(0, len(self.main_activity)):
        #     print(1)
        #     if not (i == 11 or i == 8):
        #         self.common_positional_bug_detect_method("main_page", 1236, 39, times=7, anywhere=True)
        #         print(self.main_activity[i][0])
        #         self.main_to_page(i)
        #         self.solve(self.main_activity[i][0])


        while self.flag_run:
            next_func_name = self.scheduler.heartbeat()
            if next_func_name:
                log.d(f'{next_func_name} start', level=1, logger_box=self.loggerBox)
                i = self.activity_name_list.index(next_func_name)
                if i != 14:
                    self.common_positional_bug_detect_method("main_page", 1236, 39, times=7, anywhere=True)
                    self.main_to_page(i)
                if self.solve(next_func_name):
                    self.scheduler.systole(next_func_name)
                else:
                    self.flag_run = False
                    self.common_positional_bug_detect_method("main_page", 1236, 39, times=7, anywhere=True)
            else:
                time.sleep(2)


        # for i in range(0, len(self.main_activity)):
        #     print(self.main_activity[i][0], self.main_activity[i][1])
        #     if self.main_activity[i][1] == 0:
        #         log.line(self.loggerBox)
        #         print(self.main_activity[i][0])
        #         log.d("begin " + self.main_activity[i][0] + " task", level=1, logger_box=self.loggerBox)
        #         if i != 8 and i != 14:
        #             self.to_main_page()
        #             self.main_to_page(i)
        #         self.solve(self.main_activity[i][0])
        #         print(self.main_activity[i][0], self.main_activity[i][1])
        # count = 0
        # for i in range(0, len(self.main_activity)):
        #     if self.main_activity[i][1] == 1:
        #         count += 1
        # if count == 13:
        #     self.send('stop')

        #     self.flag_run = False

    def solve(self, activity) -> bool:
        try:
            return module.__dict__[activity].implement(self)
        except Exception as e:
            threading.Thread(target=self.simple_error, args=(e.__str__(),)).start()
            return False

    def simple_error(self, info: str):
        raise ScriptError(message=info, context=self)

if __name__ == '__main__':
    # # print(time.time())
    t = Main()
    t._init_emulator()
    t.flag_run = True
    path2 = "src/shop/update.png"
    img = t.operation("get_screenshot_array")
    return_data1 = get_x_y(img, path2)
    print(return_data1)
    # for i in range(0, len(t.total_force_fight_difficulty_name)):
    #     path1 = "src/total_force_fight/white_and_black/" + t.total_force_fight_difficulty_name[i] + "_BRIGHT.png"
    #     path2 = "src/total_force_fight/white_and_black/" + t.total_force_fight_difficulty_name[i] + "_GREY.png"
    #     return_data1 = t.get_x_y(img, path1)
    #     return_data2 = t.get_x_y(img, path2)
    #     print(t.total_force_fight_difficulty_name[i])
    #     print(return_data1, return_data2)
    #

    ocr_res = t.img_ocr(img)
    print(str(ocr_res))
    t.get_keyword_appear_time(ocr_res)
    print(str(t.return_location()))
