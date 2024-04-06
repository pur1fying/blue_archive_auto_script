import cv2
from core.exception import ScriptError
from core.notification import notify
from core.scheduler import Scheduler
from core import position, picture
from core.utils import Logger
import time
import numpy as np
import uiautomator2 as u2
import module
import threading
import json
from multiprocessing import process
import subprocess
import psutil
import os
import win32com.client
import time

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
    'total_assault': module.total_assault.implement,
    'restart': module.restart.implement,
    'refresh_uiautomator2': module.refresh_uiautomator2.implement,
    'activity_sweep': module.sweep_activity.implement,
    'explore_activity_story': module.explore_activity_story.implement,
    'explore_activity_challenge': module.explore_activity_challenge.implement,
    'explore_activity_mission': module.explore_activity_mission.implement,
}


class Baas_thread:
    def __init__(self, config, logger_signal=None, button_signal=None, update_signal=None):
        self.activity_name = None
        self.config_set = config
        self.process_name = None
        self.emulator_strat_stat = None
        self.lnk_path = None
        self.file_path = None
        self.wait_time = None
        self.latest_screenshot_time = 0
        self.scheduler = None
        self.screenshot_interval = None
        self.flag_run = None
        self.current_game_activity = None
        self.package_name = None
        self.server = None
        self.first_start = True
        self.rgb_feature = None
        self.config_path = self.config_set.config_dir
        self.config = None
        self.ratio = None
        self.next_time = None
        self.screenshot_updated = None
        self.task_finish_to_main_page = False
        self.static_config = None
        self.ocr = None
        self.logger = Logger(logger_signal)
        self.first_start_u2 = True
        self.last_refresh_u2_time = 0
        self.latest_img_array = None
        self.total_assault_difficulty_names = ["NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME", "INSANE", "TORMENT"]
        self.button_signal = button_signal
        self.update_signal = update_signal
        self.stage_data = {}
        self.activity_name = None

    def click(self, x, y, count=1, rate=0, duration=0, wait_over=False):
        if not self.flag_run:
            return False
        click_ = threading.Thread(target=self.click_thread, args=(x, y, count, rate, duration))
        click_.start()
        if wait_over:  # wait for click to be over
            click_.join()

    def click_thread(self, x, y, count=1, rate=0, duration=0):
        xspace_needed = 5 - len(str(x))
        yspace_needed = 3 - len(str(y))
        xspace = ""
        yspace = ""
        for i in range(0, xspace_needed):
            xspace += " "
        for i in range(0, yspace_needed):
            yspace += " "
        if count == 1:

            self.logger.info("click (" + str(x) + xspace + ",  " + str(y) + yspace + ")")
        else:
            self.logger.info("click (" + str(x) + xspace + ",  " + str(y) + yspace + ") " + str(count) + " times")
        for i in range(count):
            if not self.flag_run:
                break
            if rate > 0:
                time.sleep(rate)
            noisex = np.random.uniform(-5, 5)
            noisey = np.random.uniform(-5, 5)
            click_x = x + noisex
            click_y = y + noisey
            click_x = max(0, click_x)
            click_y = max(0, click_y)
            click_x = int(min(1280, click_x) * self.ratio)
            click_y = int(min(720, click_y) * self.ratio)
            self.connection.click(click_x, click_y)
            if duration > 0:
                time.sleep(duration)

    def get_screenshot_array(self):
        if not self.flag_run:
            return False
        self.latest_screenshot_time = time.time()
        img = cv2.cvtColor(np.array(self.connection.screenshot()), cv2.COLOR_RGB2BGR)
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

    def convert_lnk_to_exe(self, lnk_path):
        """
        判断program_addrsss是否为lnk文件，如果是则转换为exe文件地址存入config文件
        """
        if lnk_path.endswith(".lnk"):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            self.config_set.config['program_address'] = shortcut.Targetpath

    def extract_filename_and_extension(self, file_path):
        """
        从文件路径中提取文件名和后缀
        """
        file_name_with_extension = os.path.basename(file_path)
        return file_name_with_extension

    def check_process_running(self, process_name):
        """
        检测指定名称的进程是否正在运行
        """
        for proc in psutil.process_iter(['pid', 'name']):
            # self.logger.debug(f"Checking if process {process_name} is running...")
            if proc.info['name'] == process_name:
                return True
        return False

    def start_check_emulator_stat(self, emulator_strat_stat, wait_time):
        if wait_time < 20:
            self.logger.warning("Wait time is too short, auto set to 20 seconds.")
            wait_time = 20
        if emulator_strat_stat:
            self.lnk_path = self.config.get("program_address")
            self.convert_lnk_to_exe(self.lnk_path)
            self.file_path = self.config.get("program_address")
            self.process_name = self.extract_filename_and_extension(self.file_path)
            if self.check_process_running(self.process_name):
                self.logger.info(f"模拟器进程 {self.process_name} 正在运行.")
                return True
            else:
                self.logger.info(f"模拟器进程 {self.process_name} 未运行，开始启动模拟器")
                subprocess.Popen(self.file_path)
                self.logger.info(f"等待模拟器启动时间 {wait_time} 秒")
                while self.flag_run:
                    time.sleep(0.01)
                    wait_time -= 0.01
                    if wait_time <= 0:
                        break
                else:
                    return False
                if self.check_process_running(self.process_name):
                    self.logger.info(f"模拟器进程 {self.process_name} 启动成功.")
                    return True
                else:
                    self.logger.info(f"模拟器进程 {self.process_name} 启动失败.")
                return False
        else:
            self.logger.info("无需启动模拟器进程.")
            return True

    def start_emulator(self):
        self.emulator_strat_stat = self.config.get("open_emulator_stat")
        self.wait_time = self.config.get("emulator_wait_time")
        if not self.start_check_emulator_stat(self.emulator_strat_stat,self.wait_time):
            raise Exception("Emulator start failed")

    def _init_emulator(self) -> bool:
        # noinspection PyBroadException
        self.logger.info("--------------Init Emulator----------------")
        try:
            self.start_emulator()
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Emulator start failed")
            return False
        try:
            self.adb_port = self.config.get('adbPort')
            self.logger.info("adb port: " + str(self.adb_port))

            if not self.adb_port or self.adb_port == '0':
                self.connection = u2.connect()
            else:
                self.connection = u2.connect(f'127.0.0.1:{self.adb_port}')
            if 'com.github.uiautomator' not in self.connection.app_list():
                self.connection.app_install('ATX.apk')
            self.connection.uiautomator.start()
            self.wait_uiautomator_start()
            self.first_start_u2 = False
            self.last_refresh_u2_time = time.time()
            temp = self.connection.window_size()
            self.logger.info("Screen Size  " + str(temp))  # 判断分辨率是否为1280x720
            width = max(temp[0], temp[1])
            self.ratio = width / 1280
            self.logger.info("Screen Size Ratio: " + str(self.ratio))
            self.logger.info("--------Emulator Init Finished----------")
            return True
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Emulator initialization failed")
            return False

    def send(self, msg, task=None):
        if msg == "start":
            if self.button_signal is not None:
                self.button_signal.emit("停止")
            self.thread_starter()
        elif msg == "stop":
            if self.button_signal is not None:
                self.button_signal.emit("启动")
            self.flag_run = False
        elif msg == "solve":
            return self.solve(task)

    def get_enable(self, activity):
        events = json.load(open('config/event.json', 'r', encoding='utf-8'))
        for event in events:
            if event['func_name'] == activity:
                return event['enabled']
        return False

    def thread_starter(self):
        try:
            self.logger.info("-------------- Start Scheduler ----------------")
            while self.flag_run:
                if self.first_start:
                    self.solve('restart')
                next_func_name = self.scheduler.heartbeat()
                self.next_time = 0
                if next_func_name:
                    if time.time() - self.last_refresh_u2_time > 10800:
                        self.solve('refresh_uiautomator2')
                    self.logger.info(f"Scheduler :  -- {next_func_name} --")
                    self.task_finish_to_main_page = True
                    if self.solve(next_func_name) and self.flag_run:
                        next_tick = self.scheduler.systole(next_func_name, self.next_time, self.server)
                        self.logger.info(str(next_func_name) + " next_time : " + str(next_tick))
                    else:
                        self.logger.error("error occurred, stop all activities")
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
        img_possibles = {
            'normal_task_fight-pause': (908, 508),
            'normal_task_retreat-notice': (768, 507),
            'main_page_quick-home': (1236, 31),
            'main_page_daily-attendance': (640, 360),
            'main_page_item-expire': (925, 119),
            'main_page_download-additional-resources': (769, 535),
            'main_page_skip-notice': (762, 507),
            'normal_task_fight-end-back-to-main-page': (511, 662),
            "main_page_enter-existing-fight": (514, 501),
            'main_page_login-feature': (640, 360),
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
            "normal_task_task-operating-feature": (1000, 660),
            'normal_task_mission-operating-task-info': (1000, 664),
            'normal_task_mission-operating-task-info-notice': (416, 595),
            'normal_task_mission-pause': (768, 501),
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
            "total_assault_reach-season-highest-record": (640, 528),
        }
        update = {
            'CN': {
                'main_page_news': (1142, 104),
                'main_page_news2': (1142, 104),
                'cafe_cafe-reward-status': (905, 159),
                'normal_task_task-info': (1084, 139),
                "rewarded_task_purchase-bounty-ticket-notice": (888, 162),
                "special_task_task-info": (1085, 141),
            },
            'JP': {
                'main_page_news': (1142, 104),
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
        img_possibles.update(**update[self.server])
        rgb_possibles = {
            'relationship_rank_up': (640, 360),
            'area_rank_up': (640, 100),
            'level_up': (640, 200),
            'reward_acquired': (640, 100),
            "fighting_feature": (1226, 51)
        }
        picture.co_detect(self, "main_page", rgb_possibles, None, img_possibles, skip_first_screenshot,
                          tentitive_click=True)

    def wait_screenshot_updated(self):
        while (not self.screenshot_updated) and self.flag_run:
            time.sleep(0.01)
        self.screenshot_updated = False

    def init_rgb(self):
        try:
            temp = 'src/rgb_feature/rgb_feature_' + self.server + '.json'
            self.rgb_feature = json.load(open(temp, 'r', encoding='utf-8'))['rgb_feature']
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def init_config(self):
        try:
            self.config = self.operate_dict(self.config_set.config)
            return True
        except Exception as e:
            self.logger.error("Config initialization failed")
            self.logger.error(e)
            return False

    def init_server(self):
        server = self.config['server']
        if server == '官服' or server == 'B服':
            self.server = 'CN'
        elif server == '国际服':
            self.server = 'Global'
        elif server == '日服':
            self.server = 'JP'
        self.package_name = self.static_config['package_name'][server]
        self.activity_name = self.static_config['activity_name'][server]
        self.current_game_activity = self.static_config['current_game_activity'][self.server]
        self.logger.info("Current Server: " + self.server)

    def swipe(self, fx, fy, tx, ty, duration=None, post_sleep_time=0):
        if not self.flag_run:
            return False
        self.logger.info(f"swipe from ( " + str(fx) + " , " + str(fy) + " ) --> ( " + str(tx) + " , " + str(ty) + " )")
        self.connection.swipe(fx * self.ratio, fy * self.ratio, tx * self.ratio, ty * self.ratio, duration)
        if post_sleep_time > 0:
            time.sleep(post_sleep_time)

    def get_ap(self):
        region = {
            'CN': [557, 10, 662, 40],
            'Global': [557, 10, 662, 40],
            'JP': [557, 10, 662, 40],
        }
        _ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global', self.ratio)
        ap = 0
        for j in range(0, len(_ocr_res)):
            if (not _ocr_res[j].isdigit()) and _ocr_res[j] != '/' and _ocr_res[j] != '.':
                return "UNKNOWN"
            if _ocr_res[j].isdigit():
                ap = ap * 10 + int(_ocr_res[j])
            elif _ocr_res[j] == '/':
                self.logger.info("AP: " + str(ap))
                return ap
        return "UNKNOWN"

    def get_pyroxene(self):
        region = {
            'CN': [961, 10, 1072, 40],
            'Global': [961, 10, 1072, 40],
            'JP': [961, 10, 1072, 40],
        }
        _ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global', self.ratio)
        temp = 0
        for j in range(0, len(_ocr_res)):
            if not _ocr_res[j].isdigit():
                continue
            temp = temp * 10 + int(_ocr_res[j])
        self.logger.info("Pyroxene: " + str(temp))
        return temp

    def get_creditpoints(self):
        region = {
            'CN': [769, 10, 896, 40],
            'Global': [769, 10, 896, 40],
            'JP': [769, 10, 896, 40],
        }
        _ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global', self.ratio)
        temp = 0
        for j in range(0, len(_ocr_res)):
            if not _ocr_res[j].isdigit():
                continue
            temp = temp * 10 + int(_ocr_res[j])
        self.logger.info("Credit Points: " + str(temp))
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
        self.flag_run = True
        self.init_config()
        self.init_server()
        self.set_screenshot_interval(self.config['screenshot_interval'])
        self.scheduler = Scheduler(self.update_signal, self.config_path)
        init_results = []
        init_results.append(self.init_rgb())
        init_results.append(position.init_image_data(self))
        init_results.append(self._init_emulator())
        for i in range(0, len(init_results)):
            if init_results[i] is False:
                self.signal_stop()
                self.logger.critical("Initialization Failed")
                return False
        self.latest_screenshot_time = 0
        self.logger.info("--------Initialization Finished----------")
        return True

    def set_screenshot_interval(self, interval):
        if interval < 0.3:
            self.logger.warning("screenshot_interval must be greater than 0.3")
            interval = 0.3
        self.logger.info("screenshot_interval set to " + str(interval))
        self.screenshot_interval = interval

    def wait_uiautomator_start(self):
        try:
            while not self.connection.uiautomator.running():
                time.sleep(0.1)
            self.latest_img_array = self.get_screenshot_array()
        except Exception as e:
            print(e)
            self.connection.uiautomator.start()
            self.wait_uiautomator_start()
