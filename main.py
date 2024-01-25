import json
import threading
import time

import numpy as np
import uiautomator2 as u2
import concurrent.futures
import module
from core.utils import *
from core.exception import ScriptError
from core.notification import notify
from core.scheduler import Scheduler
from core import position, color, image
from gui.util.config_set import ConfigSet
from core.ocr import ocr

func_dict = {
    'group': module.group.implement,
    'momo_talk': module.momo_talk.implement,
    'common_shop': module.common_shop.implement,
    'cafe_reward': module.cafe_reward.implement,
    'lesson': module.lesson.implement,
    'rewarded_task': module.rewarded_task.implement,
    'arena': module.arena.implement,
    'create': module.create.implement,
    'explore_normal_task': module.explore_normal_task.implement,
    'explore_hard_task': module.explore_hard_task.implement,
    'mail': module.mail.implement,
    'main_story': module.main_story.implement,
    'group_story': module.group_story.implement,
    'mini_story': module.mini_story.implement,
    'scrimmage': module.scrimmage.implement,
    'collect_reward': module.collect_reward.implement,
    'normal_task': module.normal_task.implement,
    'hard_task': module.hard_task.implement,
    'clear_special_task_power': module.clear_special_task_power.implement,
    'de_clothes': module.de_clothes.implement,
    'tactical_challenge_shop': module.tactical_challenge_shop.implement,
    'collect_daily_power': module.collect_reward.implement,
    'total_force_fight': module.total_force_fight.implement,
    'restart': module.restart.implement,
    'refresh_uiautomator2': module.refresh_uiautomator2.implement,
    'no_227_kinosaki_spa': module.no_227_kinosaki_spa.implement,
    'no_68_spring_wild_dream': module.no_68_spring_wild_dream.implement,
}


class Main:
    def __init__(self, logger_signal=None, button_signal=None, update_signal=None):
        self.activity_name = None
        self.img_cnt = 0
        self.latest_screenshot_time = 0
        self.scheduler = None
        self.screenshot_interval = None
        self.flag_run = None
        self.current_game_activity = None
        self.static_config = None
        self.main_activity = None
        self.package_name = None
        self.server = None
        self.first_start = True
        self.rgb_feature = None
        self.ocr = None
        self.config = None
        self.next_time = None
        self.screenshot_updated = None
        self.ocrCN, self.ocrNUM, self.ocrEN = [None] * 3
        self.common_task_count = []
        self.hard_task_count = []
        self.common_task_status = []
        self.hard_task_status = []
        self.task_finish_to_main_page = False
        self.logger = Logger(logger_signal)
        self.first_start_u2 = True
        self.last_start_u2_time = 0
        # self.logger = logging.getLogger("logger_name")
        # formatter = logging.Formatter("%(levelname)8s |%(asctime)20s | %(message)s ")
        # handler1 = logging.StreamHandler(stream=sys.stdout)
        # handler1.setFormatter(formatter)
        # self.logger.setLevel(logging.INFO)
        # self.logger.addHandler(handler1)

        # self.loggerBox = logger_signal
        self.total_force_fight_difficulty_name = ["HARDCORE", "VERYHARD", "EXTREME", "NORMAL", "HARD"]  # 当期总力战难度
        self.total_force_fight_difficulty_name_ordered = ["NORMAL", "HARD", "VERYHARD", "HARDCORE",
                                                          "EXTREME"]  # 当期总力战难度
        self.total_force_fight_difficulty_name_dict = {"NORMAL": 0, "HARD": 1, "VERYHARD": 2, "HARDCORE": 3,
                                                       "EXTREME": 4}
        self.total_force_fight_name = "chesed"  # 当期总力战名字
        self.latest_img_array = None
        self.button_signal = button_signal
        self.update_signal = update_signal
        self.stage_data = {}

        # start_debugger()

    def click(self, x, y, wait=True, count=1, rate=0, duration=0, wait_over=False):
        if not self.flag_run:
            return False
        if wait:
            color.wait_loading(self)
        click_ = threading.Thread(target=self.click_thread, args=(x, y, count, rate, duration))
        click_.start()
        if wait_over:  # wait for click to be over
            click_.join()

    def click_thread(self, x, y, count=1, rate=0, duration=0):
        if count == 1:
            self.logger.info("click (" + str(x) + " ," + str(y) + ")")
        else:
            self.logger.info("click (" + str(x) + " ," + str(y) + ") " + str(count) + " times")
        for i in range(count):
            if rate > 0:
                time.sleep(rate)
            noisex = int(np.random.uniform(-5, 5))
            noisey = int(np.random.uniform(-5, 5))
            click_x = x + noisex
            click_y = y + noisey
            click_x = max(0, click_x)
            click_y = max(0, click_y)
            click_x = min(1280, click_x)
            click_y = min(720, click_y)
            self.connection.click(click_x, click_y)
            if duration > 0:
                time.sleep(duration)

    def get_screenshot_array(self):
        if not self.flag_run:
            return False
        self.latest_screenshot_time = time.time()
        img = cv2.cvtColor(np.array(self.connection.screenshot()), cv2.COLOR_RGB2BGR)
        self.img_cnt += 1
        # cv2.imwrite("D:\\github\\bass\\blue_archive_auto_script\\test\\" + str(self.img_cnt) + ".png", img)
        return img

    def screenshot_worker_thread(self):
        self.latest_img_array = self.get_screenshot_array()
        self.screenshot_updated = True

    def signal_stop(self):
        self.flag_run = False
        if self.button_signal is not None:
            self.button_signal.emit("启动")

    def init_emulator(self):
        self._init_emulator()

    def _init_emulator(self) -> bool:
        # noinspection PyBroadException
        self.logger.info("--------------Init Emulator----------------")
        try:
            self.adb_port = self.config.get('adbPort')
            self.logger.info("adb port: " + str(self.adb_port))

            if not self.adb_port or self.adb_port == '0':
                self.connection = u2.connect()
            else:
                self.connection = u2.connect(f'127.0.0.1:{self.adb_port}')
            if 'com.github.uiautomator' not in self.connection.app_list():
                self.connection.app_install('ATX.apk')
            self.first_start_u2 = False
            self.last_start_u2_time = time.time()
            temp = self.connection.window_size()
            self.logger.info("Screen Size  " + str(temp))  # 判断分辨率是否为1280x720
            if (temp[0] == 1280 and temp[1] == 720) or (temp[1] == 1280 and temp[0] == 720):
                self.logger.info("Screen Size Fitted")
            else:
                self.logger.critical("Screen Size unfitted, Please set the screen size to 1280x720")
                return False
            self.logger.info("--------Emulator Init Finished----------")
            return True
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Emulator initialization failed")
            return False

    def send(self, msg):
        if msg == "start":
            if self.button_signal is not None:
                self.button_signal.emit("停止")
            self.thread_starter()
        elif msg == "stop":
            if self.button_signal is not None:
                self.button_signal.emit("启动")
            self.flag_run = False

    def get_enable(self, activity):
        events = json.load(open('config/event.json', 'r', encoding='utf-8'))
        for event in events:
            if event['func_name'] == activity:
                return event['enabled']
        return False

    def thread_starter(self):  # 主程序，完成用户指定任务
        try:
            self.logger.line()
            self.logger.info("start activities")
            while self.flag_run:
                if self.first_start:
                    self.solve('restart')
                next_func_name = self.scheduler.heartbeat()
                self.next_time = 0
                if next_func_name:
                    self.logger.info(f"current activity: {next_func_name}")
                    self.task_finish_to_main_page = True
                    if self.solve(next_func_name):
                        next_tick = self.scheduler.systole(next_func_name, self.next_time, self.server)
                        next_tick.replace(microsecond=0)
                        self.logger.info(str(next_func_name) + " next_time : " + str(next_tick))
                    else:
                        self.logger.error("error occurred, stop all activities")
                        self.quick_method_to_main_page()
                        self.signal_stop()
                else:
                    if self.task_finish_to_main_page:
                        self.logger.info("all activities finished, return to main page")
                        self.quick_method_to_main_page()
                        self.task_finish_to_main_page = False
                    time.sleep(1)
        except Exception as e:
            notify(title='', body='任务已停止')
            self.logger.info("error occurred, stop all activities")
            self.logger.error(e)
            self.signal_stop()

    def solve(self, activity) -> bool:
        try:
            return func_dict[activity](self)
        except Exception as e:
            self.logger.error(e)
            threading.Thread(target=self.simple_error, args=(e.__str__(),)).start()
            return False

    def simple_error(self, info: str):
        raise ScriptError(message=info, context=self)

    def quick_method_to_main_page(self, skip_first_screenshot=False):
        possibles = {
            'main_page_quick-home': (1236, 31),
            'normal_task_fight-end-back-to-main-page': (511, 662),
            "main_page_enter-existing-fight": (514, 501),
            'main_page_login-feature': (640, 360),
            'main_page_news': (1142, 104),
            'main_page_relationship-rank-up': (640, 360),
            'main_page_full-notice': (887, 165),
            'normal_task_fight-confirm': (1168, 659),
            'normal_task_task-finish': (1038, 662),
            'normal_task_prize-confirm': (776, 655),
            'normal_task_fail-confirm': (643, 658),
            'normal_task_fight-task-info': (420, 592),
            "normal_task_sweep-complete": (643, 585),
            "normal_task_start-sweep-notice": (887, 164),
            "normal_task_unlock-notice": (887, 164),
            'normal_task_skip-sweep-complete': (643, 506),
            "normal_task_charge-challenge-counts": (887, 164),
            "purchase_ap_notice": (919, 165),
            'normal_task_mission-operating-task-info': (1000, 664),
            'normal_task_mission-operating-task-info-notice': (416, 595),
            'normal_task_mission-pause': (768, 501, 3),
            'normal_task_task-begin-without-further-editing-notice': (888, 163),
            'normal_task_task-operating-round-over-notice': (888, 163),
            'momo_talk_momotalk-peach': (1123, 122),
            'cafe_students-arrived': (922, 189),
            'cafe_quick-home': (1236, 31),
            'group_sign-up-reward': (920, 159),
            'cafe_invitation-ticket': (835, 97),
            'lesson_lesson-information': (964, 117),
            'lesson_all-locations': (1138, 117),
            'lesson_lesson-report': (642, 556),
            'arena_battle-win': (640, 530),
            'arena_battle-lost': (640, 468),
            'arena_season-record': (640, 538),
            'arena_best-record': (640, 538),
            'arena_opponent-info': (1012, 98),
            'plot_menu': (1202, 37),
            'plot_skip-plot-button': (1208, 116),
            'plot_skip-plot-notice': (770, 519),
            'activity_fight-success-confirm': (640, 663),
        }
        update = {
            'CN': {
                'cafe_cafe-reward-status': (905, 159),
                'normal_task_task-info': (1084, 139),
                "rewarded_task_purchase-bounty-ticket-notice": (888, 162),
                "special_task_task-info": (1085, 141),
            },
            'JP': {
                "cafe_cafe-reward-status": (985, 147),
                'normal_task_task-info': (1126, 141),
                "rewarded_task_purchase-bounty-ticket-notice": (919, 165),
                "special_task_task-info": (1126, 141),
                'main_page_attendance-reward': (642, 489),
            },
            'Global': {
                'main_page_news': (1227, 56),
                "special_task_task-info": (1126, 141),
                'cafe_cafe-reward-status': (905, 159),
                'normal_task_task-info': (1126, 139),
                'main_page_login-store': (883, 162),
                'main_page_insufficient-inventory-space': (912, 140),
            }
        }
        possibles.update(**update[self.server])
        fail_cnt = 0
        click_pos = [
            [1236, 31],
            [640, 360],
            [640, 100],
            [640, 200],
        ]
        los = [
            "home",
            'relationship_rank_up',
            'area_rank_up',
            'level_up'
        ]
        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                color.wait_loading(self)
            res = color.detect_rgb_one_time(self, [], [], ['main_page'])
            if res == ('end', 'main_page'):
                break
            res = color.detect_rgb_one_time(self, click_pos, los, [])
            if res == ('click', True):
                continue
            # region 资源图片可能会出现的位置
            for asset, obj in possibles.items():
                if image.compare_image(self, asset, 3, need_loading=False, image=self.latest_img_array,
                                       need_log=False):
                    self.logger.info("find " + asset)
                    self.click(obj[0], obj[1], False)
                    self.latest_screenshot_time = time.time()
                    fail_cnt = 0
                    break
            else:
                fail_cnt += 1
                if fail_cnt > 10:
                    self.logger.info("tentative clicks")
                    self.click(1236, 31, False)
                    self.latest_screenshot_time = time.time()
                    fail_cnt = 0
        return True

    def wait_screenshot_updated(self):
        while not self.screenshot_updated:
            time.sleep(0.01)
        self.screenshot_updated = False

    def init_rgb(self):
        try:
            self.logger.info("Start initializing rgb_feature")
            temp = 'src/rgb_feature/rgb_feature_' + self.server + '.json'
            self.rgb_feature = json.load(open(temp, 'r', encoding='utf-8'))['rgb_feature']
            self.logger.info("Successfully initialized rgb_feature")
            return True
        except Exception as e:
            self.logger.error("rgb_feature initialization failed")
            self.logger.error(e)
            return False

    def init_config(self):
        try:
            self.logger.info("Start Reading Config")
            t = ConfigSet()
            self.config = self.operate_dict(t.config)
            self.static_config = self.operate_dict(t.static_config)
            self.main_activity = self.config['activity_list']
            self.logger.info("SUCCESS")
            return True
        except Exception as e:
            self.logger.error("Config initialization failed")
            self.logger.error(e)
            return False

    def init_server(self):
        self.logger.info("Start Detecting Server")
        server = self.config['server']
        if server == '官服' or server == 'B服':
            self.server = 'CN'
        elif server == '国际服':
            self.server = 'Global'
        elif server == '日服':
            self.server = 'JP'
        self.current_game_activity = self.static_config['current_game_activity'][self.server]
        self.logger.info("Current Server: " + self.server)

    def swipe(self, fx, fy, tx, ty, duration=None):
        if not self.flag_run:
            return False
        self.logger.info(f"swipe {fx} {fy} {tx} {ty}")
        if duration is None:
            self.connection.swipe(fx, fy, tx, ty)
        else:
            self.connection.swipe(fx, fy, tx, ty, duration=duration)

    def init_ocr(self):
        try:
            self.logger.info("Start initializing OCR")
            self.ocr = ocr.Baas_ocr(logger=self.logger, ocr_needed=['CN', 'Global', 'NUM', 'JP'])
            self.logger.info("OCR initialization concluded")
            return True
        except Exception as e:
            self.logger.error("OCR initialization failed")
            self.logger.error(e)
            return False

    def get_ap(self):
        region = {
            'CN': [557, 10, 662, 40],
            'Global': [557, 10, 662, 40],
            'JP': [557, 10, 662, 40],
        }
        _ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global')
        ap = 0
        for j in range(0, len(_ocr_res)):
            if (not _ocr_res[j].isdigit()) and _ocr_res[j] != '/' and _ocr_res[j] != '.':
                return "UNKNOWN"
            if _ocr_res[j].isdigit():
                ap = ap * 10 + int(_ocr_res[j])
            elif _ocr_res[j] == '/':
                return ap
        return "UNKNOWN"

    def get_pyroxene(self):
        region = {
            'CN': [961, 10, 1072, 40],
            'Global': [961, 10, 1072, 40],
            'JP': [961, 10, 1072, 40],
        }
        _ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global')
        temp = 0
        for j in range(0, len(_ocr_res)):
            if not _ocr_res[j].isdigit():
                continue
            temp = temp * 10 + int(_ocr_res[j])
        return temp

    def get_creditpoints(self):
        region = {
            'CN': [769, 10, 896, 40],
            'Global': [769, 10, 896, 40],
            'JP': [769, 10, 896, 40],
        }
        _ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global')
        temp = 0
        for j in range(0, len(_ocr_res)):
            if not _ocr_res[j].isdigit():
                continue
            temp = temp * 10 + int(_ocr_res[j])
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
        if type(item) is int or type(item) is bool or type(item) is float or item is None:
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
        self.logger.info("--------Initialing All Data----------")
        self.init_config()
        self.init_server()
        self.init_package_activity_name()
        init_results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            init_results.append(executor.submit(self.init_ocr))
            init_results.append(executor.submit(self.init_rgb))
            init_results.append(executor.submit(position.init_image_data, self))
            init_results.append(executor.submit(self._init_emulator))
        for i in range(0, len(init_results)):
            if init_results[i].result() is False:
                self.signal_stop()
                self.logger.critical("Initialization Failed")
                return False
        self.set_screenshot_interval(self.config['screenshot_interval'])
        self.latest_screenshot_time = 0
        self.scheduler = Scheduler(self.update_signal)
        self.logger.info("--------Initialization Finished----------")
        return True

    def init_package_activity_name(self):
        server = self.config['server']
        self.package_name = self.static_config['package_name'][server]
        self.activity_name = self.static_config['activity_name'][server]
        return True

    def set_screenshot_interval(self, interval):
        if interval < 0.3:
            self.logger.warning("screenshot_interval must be greater than 0.3")
            interval = 0.3
        self.logger.info("screenshot_interval set to " + str(interval))
        self.screenshot_interval = interval


if __name__ == '__main__':
    # # print(time.time())
    t = Main()
    # t.thread_starter()
    t.flag_run = True
    t.init_all_data()
    t.solve('explore_normal_task')
