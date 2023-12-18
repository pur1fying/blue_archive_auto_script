import json
import logging
import sys
import threading
import time

import cv2
import numpy as np
import uiautomator2 as u2
from cnocr import CnOcr

import module
from core.exception import ScriptError
from core.notification import notify
from core.scheduler import Scheduler
from core.setup import Setup
from core.utils import kmp, get_x_y, check_sweep_availability
from core import position, color, image, stage
from gui.util import log
from gui.util.config_set import ConfigSet

func_dict = {
    'group': module.group.implement,
    'momo_talk': module.momo_talk.implement,
    'shop': module.shop.implement,
    'cafe_reward': module.cafe_reward.implement,
    'schedule': module.schedule.implement,
    'rewarded_task': module.rewarded_task.implement,
    'arena': module.arena.implement,
    'create': module.create.implement,
    'explore_normal_task': module.explore_normal_task.implement,
    'explore_hard_task': module.explore_hard_task.implement,
    'mail': module.mail.implement,
    'main_story': module.main_story.start,
    'scrimmage': module.scrimmage.implement,
    'collect_reward': module.collect_reward.implement,
    'normal_task': module.normal_task.implement,
}


class Main(Setup):
    def __init__(self, logger_box=None, button_signal=None, update_signal=None):
        super().__init__()
        self.package_name = None
        self.server = None
        self.rgb_feature = None
        self.ocr = None
        self.config = None
        self.logger = logging.getLogger("logger_name")
        formatter = logging.Formatter("%(levelname)8s |%(asctime)20s | %(message)s ")
        handler1 = logging.StreamHandler(stream=sys.stdout)
        handler1.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler1)

        self.init_all_data()

        self.loggerBox = logger_box
        self.total_force_fight_difficulty_name = ["HARDCORE", "VERYHARD", "EXTREME", "NORMAL", "HARD"]  # 当期总力战难度
        self.total_force_fight_difficulty_name_ordered = ["NORMAL", "HARD", "VERYHARD", "HARDCORE",
                                                          "EXTREME"]  # 当期总力战难度
        self.total_force_fight_difficulty_name_dict = {"NORMAL": 0, "HARD": 1, "VERYHARD": 2, "HARDCORE": 3,
                                                       "EXTREME": 4}
        self.total_force_fight_name = "chesed"  # 当期总力战名字
        self.screenshot_flag_run = None
        self.io_err_solved_count = 0
        self.io_err_count = 0
        self.io_err_rate = 10
        self.screenshot_interval = self.config['screenshot_interval']
        self.button_signal = button_signal
        self.flag_run = True
        self.next_task = ''
        self.stage_data = {}
        self.activity_name_list = self.main_activity.copy()
        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]
        try:
            self.common_task_count = self.config['mainlinePriority']  # **可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(普通)打k次
            self.hard_task_count = self.config['hardPriority']  # **可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(困难)打k次
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

    def click(self, x, y, wait=True, count=1, rate=0,duration=0):
        if wait:
            self.wait_loading()
        for i in range(count):
            self.logger.info("click x:%s y:%s", x, y)
            time.sleep(rate)
            self.connection.click(x, y)
            time.sleep(duration)

    def wait_loading(self):
        """
        检查是否加载中，
        """
        t_start = time.time()
        while 1:
            self.latest_img_array = cv2.cvtColor(np.array(self.connection.screenshot()), cv2.COLOR_RGB2BGR)
            if not color.judge_rgb_range(self.latest_img_array, 937, 648, 200, 255, 200, 255, 200, 255) or not \
                color.judge_rgb_range(self.latest_img_array, 919, 636, 200, 255, 200, 255, 200, 255):
                loading_pos = [[929, 664], [941, 660], [979, 662], [1077, 665], [1199, 665]]
                rgb_loading = [[200, 255, 200, 255, 200, 255], [200, 255, 200, 255, 200, 255],
                               [200, 255, 200, 255, 200, 255], [200, 255, 200, 255, 200, 255],
                               [255, 255, 255, 255, 255, 255]]
                t = len(loading_pos)
                for i in range(0, t):
                    if not color.judge_rgb_range(self.latest_img_array, loading_pos[i][0], loading_pos[i][1],
                                                 rgb_loading[i][0],
                                                 rgb_loading[i][1], rgb_loading[i][2], rgb_loading[i][3],
                                                 rgb_loading[i][4], rgb_loading[i][5]):
                        break
                else:
                    t_load = time.time() - t_start
                    self.logger.info("loading, t load : " + str(t_load))
                    if t_load > 20:
                        self.logger.warning("LOADING TOO LONG add screenshot interval to 1")
                        self.screenshot_interval = 1
                    time.sleep(self.screenshot_interval)
                    continue

            return True

    def get_screenshot_array(self):
        return cv2.cvtColor(np.array(self.connection.screenshot()), cv2.COLOR_RGB2BGR)

    def signal_stop(self):
        self.flag_run = False
        self.button_signal.emit("启动")

    def _init_emulator(self) -> bool:
        # noinspection PyBroadException
        print("--------init emulator----------")
        try:
            self.adb_port = self.config.get('adbPort')
            self.logger.info("adb port: " + str(self.adb_port))
            if not self.adb_port or self.adb_port == '0':
                self.connection = u2.connect()
            else:
                self.connection = u2.connect(f'127.0.0.1:{self.adb_port}')
            if 'com.github.uiautomator' not in self.connection.app_list():
                self.connection.app_install('ATX.apk')
            self.connection.app_start(self.package_name)
            temp = self.connection.window_size()
            self.logger.info("Screen Size  " + str(temp))  # 判断分辨率是否为1280x720
            if (temp[0] == 1280 and temp[1] == 720) or (temp[1] == 1280 and temp[0] == 720):
                self.logger.info("Screen Size Fitted")
            else:
                self.logger.info("Screen Size unfitted")
                self.send('stop')
                return False
            print("--------Emulator Init Finished----------")
            return True
        except Exception as e:
            threading.Thread(target=self.simple_error, args=(e.__str__(),)).start()
            return False

    def send(self, msg):
        if msg == "start":
            self.button_signal.emit("停止")
            self.start_instance()
        elif msg == "stop":
            self.button_signal.emit("启动")
            self.flag_run = False

    def thread_starter(self):  # 主程序，完成用户指定任务
        self.quick_method_to_main_page()
        log.line(self.loggerBox)
        log.d("start activities", level=1, logger_box=self.loggerBox)
        print('--------------Start activities...---------------')
        for i in range(0, len(self.main_activity)):
            print(self.main_activity[i][0])
            self.solve(self.main_activity[i][0])
        while self.flag_run:
            next_func_name = self.scheduler.heartbeat()
            if next_func_name:
                log.d(f'{next_func_name} start', level=1, logger_box=self.loggerBox)
                i = self.activity_name_list.index(next_func_name)
                if i != 14:
                    self.quick_method_to_main_page()
                if self.solve(next_func_name):
                    self.scheduler.systole(next_func_name)
                else:
                    self.flag_run = False
                    self.quick_method_to_main_page()
            else:
                # 返回None结束任务
                log.d('activities all finished', level=1, logger_box=self.loggerBox)
                notify(title='', body='任务已完成')
                break
        self.signal_stop()
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

    def start_instance(self):
        if self._init_emulator():
            self.thread_starter()

    def solve(self, activity) -> bool:
        try:
            return func_dict[activity](self)
        except Exception as e:
            threading.Thread(target=self.simple_error, args=(e.__str__(),)).start()
            return False

    def simple_error(self, info: str):
        raise ScriptError(message=info, context=self)

    def quick_method_to_main_page(self):
        if self.server == "CN":
            possibles = {
                'main_page_quick-home': (1236, 31, 3),
                'main_page_login-feature': (640, 360, 3),
                'main_page_news': (1142, 104, 3),
                'main_story_fight-confirm': (1168, 659, 3),
                'normal_task_task-finish': (1038, 662, 3),
                'normal_task_prize-confirm': (776, 655, 3),
                'normal_task_fail-confirm': (643, 658, 3),
                'normal_task_fight-task-info': (420, 592, 3),
                'normal_task_mission-operating-task-info': (1000, 664, 3),
                'normal_task_task-info': (1084, 139, 3),
                'normal_task_mission-operating-task-info-notice': (416, 595, 3),
                'normal_task_mission-pause': (768, 501, 3),
                'normal_task_task-begin-without-further-editing-notice': (888, 163, 3),
                'normal_task_task-operating-round-over-notice': (888, 163, 3),
                'buy_ap_notice': (920, 167, 3),
                'momo_talk_momotalk-peach': (1123, 122, 3),
                'cafe_students-arrived': (922, 189, 3),
                'group_sign-up-reward': (920, 159, 3),
                'cafe_cafe-reward-status': (905, 159, 3),
                'cafe_invitation-ticket': (835, 97, 3),
            }
            fail_cnt = 0
            while True:
                stage.wait_loading(self)
                self.latest_img_array = self.get_screenshot_array()  # 每次公用一张截图
                res = color.detect_rgb_one_time(self, [], [], ['main_page'])
                if res == ('end', 'main_page'):
                    break
                click_pos = [
                    [640, 100],
                    [1236, 31]
                ]
                los = [
                    "reward_acquired",
                    "home"
                ]
                res = color.detect_rgb_one_time(self, click_pos, los, [])
                if res == ('click', True):
                    continue

                # region 资源图片可能会出现的位置
                for asset, obj in possibles.items():
                    if image.compare_image(self, asset, obj[2], need_loading=False, image=self.latest_img_array,
                                           need_log=False):
                        self.logger.info("find " + asset)
                        self.click(obj[0], obj[1], False)
                        time.sleep(self.screenshot_interval)
                        fail_cnt = 0
                        break
                else:
                    fail_cnt += 1
                    if fail_cnt > 10:
                        self.logger.info("tentative clicks")
                        self.click(1236, 31, False)
                        self.click(640, 360, False)
                        fail_cnt = 0
                        time.sleep(self.screenshot_interval)
            self.click(851, 262, False)  # 和妹子互动
            return True
        elif self.server == "Global":
            click_pos = [
                [1240, 39],
                [838, 97],
                [640, 360],
                [889, 162],
                [640, 458],
                [640, 116],
                [962, 114],
                [1138, 114],
                [640, 558],
                [640, 360],
                [640, 360],
                [640, 360],
                [1120, 117],
                [910, 138],
                [904, 158],
                [902, 158],
                [922, 192],
                [922, 192],
                [917, 158],
                [898, 177],
                [886, 213],
                [644, 506],
                [1120, 162],
                [921, 164],
                [1129, 142],
                [1077, 98],
                [886, 166],
                [1015, 100],
                [637, 471],
                [637, 530],
                [637, 530],
                [921, 164],
                [889, 180],
                [919, 168],
                [649, 508],
                [887, 161],
                [920, 165],
                [637, 116],
                [871, 164],
            ]
            los = [
                "home",
                "invitation_ticket",
                "relationship_rank_up",
                "full_ap_notice",
                "guide",
                "reward_acquired",
                "location_info",
                "all_locations",
                "lesson_report",
                "sign_in1",
                "sign_in2",
                "sign_in3",
                "momotalk",
                "insufficient_inventory_space",
                "cafe_earning_status_bright",
                "cafe_earning_status_grey",
                "buy_notice_bright",
                "buy_notice_grey",
                "club_attendance_reward",
                "shop_buy_notice_bright",
                "shop_refresh_guide",
                "store_login_notice",
                "room_info",
                "purchase_bounty_ticket",
                "mission_info",
                "sweep_complete",
                "start_sweep_notice",
                "battle_opponent",
                "battle_result_lose",
                "battle_result_win",
                "best_season_record_reached",
                "purchase_scrimmage_ticket",
                "purchase_ticket_notice",
                "purchase_ap_notice",
                "skip_sweep_complete",
                "charge_challenge_counts",
                "purchase_lesson_ticket",
                "area_rank_up",
                "complete_instantly_notice",
            ]
            ends = ["main_page"]
            color.common_rgb_detect_method(self, click_pos, los, ends)
            self.click(851, 262, False)
            return True

    def init_rgb(self):
        try:
            self.logger.info("Start initializing rgb_feature")
            if self.server == 'CN':
                self.rgb_feature = json.load(open('src/rgb_feature/rgb_feature_CN.json'))['rgb_feature']
            elif self.server == 'Global':
                self.rgb_feature = json.load(open('src/rgb_feature/rgb_feature_Global.json'))['rgb_feature']
            self.logger.info("SUCCESS")
        except Exception as e:
            self.logger.error("rgb_feature initialization failed")
            self.logger.error(e)

    def init_config(self):
        try:

            self.logger.info("Start initializing config")
            self.config = self.operate_dict(ConfigSet().config)
            self.logger.info("SUCCESS")
        except Exception as e:
            self.logger.error("Config initialization failed")
            self.logger.error(e)

    def init_server(self):
        try:
            self.logger.info("Start initializing server")
            if self.config['Settings']['server'] == '官服' or self.config['Settings']['server'] == 'B服':
                self.server = 'CN'
            elif self.config['Settings']['server'] == '国际服':
                self.server = 'Global'
            self.logger.info("Current server: " + self.server)
        except Exception as e:
            self.logger.error("Server initialization failed")
            self.logger.error(e)

    def swipe(self, fx, fy, tx, ty,duration=None):
        self.logger.info("swipe %s %s %s %s", fx, fy, tx, ty)
        if duration is None:
            self.connection.swipe(fx, fy, tx, ty)
        else:
            self.connection.swipe(fx, fy, tx, ty,duration=duration)

    def init_ocr(self):
        try:
            self.logger.info("Start initializing OCR")
            if self.server == 'CN':
                self.ocrCN = CnOcr(rec_model_name='densenet_lite_114-fc')
                img_CN = cv2.imread('src/test_ocr/CN.png')
                self.logger.info("Test ocrCN : " + self.ocrCN.ocr_for_single_line(img_CN)['text'])
            elif self.server == 'Global':
                self.ocrEN = CnOcr(det_model_name="en_PP-OCRv3_det", rec_model_name='en_number_mobile_v2.0', context='gpu')
                img_EN = cv2.imread('src/test_ocr/EN.png')
                self.logger.info("Test ocrEN : " + self.ocrEN.ocr_for_single_line(img_EN)['text'])
            self.ocrNUM = CnOcr(det_model_name='number-densenet_lite_136-fc',rec_model_name='number-densenet_lite_136-fc')
            img_NUM = cv2.imread('src/test_ocr/NUM.png')
            self.logger.info("Test ocrNUM : " + self.ocrNUM.ocr_for_single_line(img_NUM)['text'])
            self.logger.info("OCR initialization concluded")
        except Exception as e:
            self.logger.error("OCR initialization failed")
            self.logger.error(e)

    def get_ap(self):
        img = self.latest_img_array[10:40, 560:658, :]
        t1 = time.time()
        ocr_res = self.ocr.ocr_for_single_line(img)
        t2 = time.time()
        self.logger.info("ocr_ap:" + str(t2 - t1))
        temp = ""
        for j in range(0, len(ocr_res['text'])):
            if ocr_res['text'][j] == '/':
                self.logger.info("ap:" + temp)
                return [int(ocr_res["text"][:j]), int(ocr_res["text"][j + 1:])]
        self.logger.info("ap: UNKNOWN")
        return "UNKNOWN"

    def get_pyroxene(self):
        img = self.latest_img_array[10:40, 961:1072, :]
        t1 = time.time()
        ocr_res = self.ocr.ocr_for_single_line(img)
        t2 = time.time()
        self.logger.info("ocr_pyroxene:" + str(t2 - t1))
        temp = 0
        for j in range(0, len(ocr_res['text'])):
            if not ocr_res['text'][j].isdigit():
                continue
            temp = temp * 10 + int(ocr_res['text'][j])
        return temp

    def get_creditpoints(self):
        img = self.latest_img_array[10:40, 769:896, :]
        t1 = time.time()
        ocr_res = self.ocr.ocr_for_single_line(img)
        t2 = time.time()
        self.logger.info("ocr_creditpoints:" + str(t2 - t1))
        temp = 0
        for j in range(0, len(ocr_res['text'])):
            if not ocr_res['text'][j].isdigit():
                continue
            temp = temp * 10 + int(ocr_res['text'][j])
        return temp

    def operate_dict(self, dic):
        for key in dic:
            if type(dic[key]) is dict:
                dic[key] = self.operate_dict(dic[key])
            else:
                dic[key] = self.operate_item(dic[key])
        return dic

    def is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def operate_item(self, item):
        if type(item) is int or type(item) is bool or type(item) is float:
            return item
        if type(item) is str:
            if item.isdigit():
                return int(item)
            elif self.is_float(item):
                return float(item)
            else:
                if item.count(",") == 2:
                    temp = item.split(",")
                    for j in range(0, len(temp)):
                        if temp[j].isdigit():
                            temp[j] = int(temp[j])
                    print(item, temp)
                    item = temp
                return item
        else:
            temp = []
            for i in range(0, len(item)):
                if type(item[i]) is dict:
                    temp.append(self.operate_dict(item[i]))
                else:
                    temp.append(self.operate_item(item[i]))
            return temp

    def init_all_data(self):
        self.init_config()
        print(self.config)
        self.init_server()
        self.init_package_name()
        self.init_ocr()
        self.init_rgb()
        position.init_image_data(self)
        self._init_emulator()

    def init_package_name(self):
        server = self.config['server']
        if server == '官服':
            self.package_name = 'com.RoamingStar.BlueArchive'
        elif server == 'B服':
            self.package_name = 'com.RoamingStar.BlueArchive.bilibili'
        elif server == '国际服':
            self.package_name = 'com.nexon.bluearchive'


if __name__ == '__main__':
    # # print(time.time())
    t = Main()
    t.flag_run = True
    # t.quick_method_to_main_page()
    # t.solve('scrimmage')
    # t.quick_method_to_main_page()
    # t.solve('collect_reward')
    # t.quick_method_to_main_page()
    # t.solve('group')
    # t.quick_method_to_main_page()
    # t.solve('cafe_reward')
    t.quick_method_to_main_page()
    t.solve('normal_task')
    t.quick_method_to_main_page()
    t.solve('explore_normal_task')
    # t.quick_method_to_main_page()
    # t.solve('momo_talk')
    t.thread_starter()
    path = "src/event/auto clear bright.png"
    img = t.get_screenshot_array()
    print(check_sweep_availability(img))
    return_data1 = get_x_y(img, path)
    print(return_data1)

    ocr_res = t.img_ocr(img)
    print(str(ocr_res))
    t.get_keyword_appear_time(ocr_res)
    print(str(t.return_location()))
