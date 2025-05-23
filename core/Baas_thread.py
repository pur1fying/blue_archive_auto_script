import copy
import json
import os
import subprocess
import threading
import time
import traceback
from dataclasses import fields
from datetime import datetime
from core.utils import Logger
import cv2
import numpy as np
import psutil
import requests

import module.ExploreTasks.explore_task
from core.device import emulator_manager
from core import position, picture
from core.config.config_set import ConfigSet
from core.device.Control import Control
from core.device.Screenshot import Screenshot
from core.device.connection import Connection
from core.device.uiautomator2_client import BAAS_U2_Initer, __atx_agent_version__
from core.device.uiautomator2_client import U2Client
from core.exception import RequestHumanTakeOver, FunctionCallTimeout, PackageIncorrect, LogTraceback
from core.notification import notify, toast
from core.pushkit import push
from core.scheduler import Scheduler
from core.utils import Logger
from core.device.emulator_manager import process_api

func_dict = {
    'group': module.group.implement,
    'momo_talk': module.momo_talk.implement,
    'common_shop': module.common_shop.implement,
    'cafe_reward': module.cafe_reward.implement,
    'no1_cafe_invite': module.no1_cafe_invite.implement,
    'no2_cafe_invite': module.no2_cafe_invite.implement,
    'lesson': module.lesson.implement,
    'rewarded_task': module.rewarded_task.implement,
    'arena': module.arena.implement,
    'create': module.create.implement,
    'explore_normal_task': module.ExploreTasks.explore_task.explore_normal_task,
    'explore_hard_task': module.ExploreTasks.explore_task.explore_hard_task,
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
    'dailyGameActivity': module.dailyGameActivity.implement,
    'friend': module.friend.implement,
    'joint_firing_drill': module.joint_firing_drill.implement,
}


class Baas_thread:

    def __init__(self, config, logger_signal=None, button_signal=None, update_signal=None, exit_signal=None):
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        self.project_dir = os.path.dirname(self.project_dir)
        self.u2_client = None
        self.u2 = None
        self.dailyGameActivity = None
        self.config_set = config
        self.process_name = None
        self.emulator_start_stat = None
        self.lnk_path = None
        self.file_path = None
        self.wait_time = None
        self.serial = None
        self.scheduler = None
        self.screenshot_interval = None
        self.flag_run = None
        self.ocr_language = None
        self.identifier = None
        self.current_game_activity = None
        self.package_name = None
        self.server = None
        self.rgb_feature = None
        self.config_path = self.config_set.config_dir
        self.config = None
        self.ratio = None
        self.next_time = 0
        self.task_finish_to_main_page = False
        self.static_config = ConfigSet.static_config
        self.ocr = None
        self.logger = Logger(logger_signal)
        self.last_refresh_u2_time = 0
        self.latest_img_array = None
        self.total_assault_difficulty_names = ["NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME", "INSANE", "TORMENT"]
        self.button_signal = button_signal
        self.update_signal = update_signal
        self.exit_signal = exit_signal
        self.stage_data = {}
        self.activity_name = None
        self.control = None
        self.screenshot = None
        self.ocr_img_pass_method = None
        self.shared_memory_name = None

    def set_ocr(self, ocr):
        self.ocr = ocr
        if self.ocr.client.config.server_is_remote:
            self.ocr_img_pass_method = 1
        else:
            self.ocr_img_pass_method = 0
            self.shared_memory_name = os.path.basename(self.config_set.config_dir)

    def get_logger(self):
        return self.logger

    def get_config(self):
        return self.config_set

    def click(self, x, y, count=1, rate=0, duration=0, wait_over=False):
        if not self.flag_run:
            raise RequestHumanTakeOver
        if self.control.method == "nemu":
            self.click_thread(x, y, count, rate, duration)
            return
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
            self.logger.info(f"Click @ ({x},{y})")
            pass
        else:
            self.logger.info(f"Click {count} times @ ({x},{y})")
        for i in range(count):
            if not self.flag_run:
                break
            if rate > 0:
                time.sleep(rate)
            click_x = max(0, x + np.random.uniform(-5, 5))
            click_y = max(0, y + np.random.uniform(-5, 5))
            click_x = int(min(1280, click_x) * self.ratio)
            click_y = int(min(720, click_y) * self.ratio)
            self.control.click(click_x, click_y)
            if duration > 0:
                time.sleep(duration)

    def u2_get_screenshot(self):
        return cv2.cvtColor(np.array(self.u2.screenshot()), cv2.COLOR_RGB2BGR)

    def get_screenshot_array(self):
        if not self.flag_run:
            raise RequestHumanTakeOver
        return self.screenshot.screenshot()

    def update_screenshot_array(self):
        self.latest_img_array = self.get_screenshot_array()

    def signal_stop(self):
        self.flag_run = False
        if self.button_signal is not None:
            self.button_signal.emit("启动")

    def init_emulator(self):
        return self._init_emulator()

    def convert_lnk_to_exe(self, lnk_path):
        """
        判断program_addrsss是否为lnk文件，如果是则转换为exe文件地址存入config文件
        """
        if lnk_path.endswith(".lnk"):
            try:
                import win32com.client
            except ImportError:
                self.logger.warning("It seems the platform is not Windows,"
                                    " skipping the shortcut conversion.")
                return

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            self.config_set.program_address = shortcut.Targetpath

    def extract_filename_and_extension(self):
        """
        从可能包含启动参数的路径中提取文件名和扩展名
        """
        # 预定义特定的文件扩展名列表
        specific_extensions = [".exe", ".lnk"]

        # 找到最后一个文件扩展名的位置
        last_extension_pos = -1
        for ext in specific_extensions:
            pos = self.file_path.lower().rfind(ext)
            if pos > last_extension_pos:
                last_extension_pos = pos

        if last_extension_pos == -1:
            # 如果没有找到文件扩展名，返回整个输入
            return self.file_path.strip()

        # 从文件扩展名的位置往前找到完整路径
        end_of_path = last_extension_pos + len(specific_extensions[0])  # 加上扩展名的长度
        actual_path = self.file_path[:end_of_path]

        # 获取文件名和扩展名
        file_name_with_extension = os.path.basename(actual_path)

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
        if emulator_strat_stat:
            self.logger.info(f"-- BAAS Check Emulator Start --")
            if self.config.emulatorIsMultiInstance:
                name = self.config.multiEmulatorName
                num = self.config.emulatorMultiInstanceNumber
                self.logger.info(f"-- Start Multi Emulator --")
                self.logger.info(f"EmulatorName: {name}")
                self.logger.info(f"MultiInstanceNumber: {num}")
                emulator_manager.start_simulator_classic(name, num)
                self.logger.info(f" Start wait {wait_time} seconds for emulator to start. ")
                while self.flag_run:
                    time.sleep(0.01)
                    wait_time -= 0.01
                    if wait_time <= 0:
                        break
                else:
                    return False
                return True
            else:
                self.file_path = self.config.program_address
                self.process_name = self.extract_filename_and_extension()
                if self.check_process_running(self.process_name):
                    self.logger.info(f"-- Emulator Process {self.process_name} is running --")
                    return True
                else:
                    self.logger.warning(f"-- Emulator Process {self.process_name} is not running, start Emulator --")
                    process_api.start(self.file_path)
                    self.logger.info(f" Start wait {wait_time} seconds for emulator to start. ")
                    while self.flag_run:
                        time.sleep(0.01)
                        wait_time -= 0.01
                        if wait_time <= 0:
                            break
                    else:
                        return False
                    if self.check_process_running(self.process_name):
                        self.logger.info(f"Emulator Process {self.process_name} started SUCCESSFULLY")
                        return True
                    else:
                        self.logger.warning(f"Emulator Process {self.process_name} start FAIL")
                    return False
        return True

    def start_emulator(self):
        self.emulator_start_stat = self.config.open_emulator_stat
        self.wait_time = self.config.emulator_wait_time
        if not self.start_check_emulator_stat(self.emulator_start_stat, self.wait_time):
            raise Exception("Emulator start failed")

    def _init_emulator(self) -> bool:
        self.logger.info("--------------Init Emulator----------------")
        try:
            self.start_emulator()
        except Exception as e:
            self.logger.error(e.__str__())
            self.logger.error("Emulator start failed")
            return False
        try:
            self.connection = Connection(self)
            self.serial = self.connection.get_serial()
            self.server = self.connection.get_server()
            self.package_name = self.connection.get_package_name()
            self.current_game_activity = self.static_config.current_game_activity[self.server]
            self.activity_name = self.connection.get_activity_name()
            self.screenshot = Screenshot(self)

            self.control = Control(self)
            self.set_screenshot_interval(self.config.screenshot_interval)

            self.check_resolution()
            self.ocr_language = self.get_ocr_language()
            self.identifier = self.server
            if self.server == "Global":
                self.identifier += "_" + self.ocr_language
                # dynamic init Global server ocr language
                self.ocr.init_baas_model(self)
                self.ocr.test_models([self.ocr_language], self.logger)
            self.logger.info("--------Emulator Init Finished----------")
            return True
        except Exception as e:
            self.logger.error(e.__str__())
            self.logger.error("Emulator initialization failed")
            return False

    def get_ocr_language(self) -> str:
        self.logger.info("Get OCR Language.")
        lang = None
        if self.server == "CN":
            lang = "zh-cn"
        elif self.server == "Global":
            basic_path = self.u2._adb_device.shell(f"echo $EXTERNAL_STORAGE").strip()
            src = "/".join([
                basic_path,
                "Android",
                "data",
                self.package_name,
                "files",
                "DeviceOption"
            ])
            print(src)
            dst = os.path.basename(self.config_set.config_dir) + "_DeviceOption.json"
            # remove dst existing file
            if os.path.exists(dst):
                os.remove(dst)
            sync = self.u2._adb_device.sync
            src_file_info = sync.stat(src)
            is_src_file = src_file_info.mode & 32768 != 0

            if is_src_file:
                sync.pull_file(src, dst)
            else:
                raise Exception("Global Server DeviceOption File not exist.")
            supported_language_convert_dict = {
                "Kr": "ko-kr",
                "En": "en-us",
                "Tw": "zh-tw",
            }
            with open(dst, "r") as f:
                data = json.load(f)
                game_lan = data["Language"]
                if game_lan in supported_language_convert_dict:
                    lang = supported_language_convert_dict[game_lan]
                else:
                    raise Exception("Global Server Invalid Language : " + game_lan + ".")
        elif self.server == "JP":
            lang = "ja-jp"
        self.logger.info("Ocr Language : " + lang)
        return lang

    def check_atx(self):
        self.logger.info("--------------Check ATX install ----------------")
        _d = self.u2._wait_for_device()
        if not _d:
            raise RuntimeError("USB device %s is offline " + self.serial)
        self.logger.info("Device [ " + self.serial + " ] is online.")

        version_url = self.u2.path2url("/version")
        try:
            version = requests.get(version_url, timeout=3).text
            if version != __atx_agent_version__:
                raise EnvironmentError("atx-agent need upgrade")
        except (requests.RequestException, EnvironmentError):
            self.set_up_atx_agent()
        self.wait_uiautomator_start()
        self.logger.info("Uiautomator2 service started.")

    def set_up_atx_agent(self):
        init = BAAS_U2_Initer(self.u2._adb_device, self.logger)
        init.install()

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

    def thread_starter(self):
        """
            Solving tasks given by the scheduler.
            Features:
            1.Never stop until user push the "stop" button on ui, or an unmanageable error occurs.
            2.task solve order is fully controlled by the scheduler (core/scheduler.py).
        """
        try:
            self.logger.info("-------------- Start Scheduler ----------------")
            self.solve('restart')  # check package and go to main_page
            while self.flag_run:
                nextTask = self.scheduler.heartbeat()  # get next task
                if nextTask:
                    self.task_finish_to_main_page = True
                    self.daily_config_refresh()
                    if time.time() - self.last_refresh_u2_time > 10800:
                        self.solve('refresh_uiautomator2')
                    self.genScheduleLog(nextTask)

                    task_with_log_info = []
                    for task in nextTask['pre_task']:
                        task_with_log_info.append((task, 'pre_task'))
                    task_with_log_info.append((nextTask['current_task'], 'current_task'))
                    for task in nextTask['post_task']:
                        task_with_log_info.append((task, 'post_task'))

                    currentTaskNextTime = 0
                    for task, task_type in task_with_log_info:
                        if not self.flag_run:
                            break
                        flg = False
                        self.logger.info(f"{task_type}: [ {task} ] start")
                        if task_type == 'current_task':
                            flg = True
                            self.next_time = 0
                        if not self.solve(task):
                            self.signal_stop()
                            notify(title='', body='任务已停止')
                            return
                        if flg:
                            currentTaskNextTime = self.next_time

                    if self.flag_run:
                        next_tick = self.scheduler.systole(nextTask['current_task'], currentTaskNextTime)
                        self.logger.info(nextTask['current_task'] + " next_time : " + str(next_tick))
                    else:
                        self.logger.info("BAAS Exited, Reason : Human Take Over")
                        self.signal_stop()
                else:
                    if self.task_finish_to_main_page:
                        self.logger.info("all activities finished, return to main page")
                        push(self.logger, self.config)
                        self.to_main_page()
                        self.main_page_update_data()
                        self.task_finish_to_main_page = False
                    self.scheduler.update_valid_task_queue()
                    time.sleep(1)
                    if self.flag_run:  # allow user to stop script before then action
                        self.handle_then()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            return

    def genScheduleLog(self, task):
        self.logger.info("Scheduler : {")
        self.logger.info("                pre_task         : " + str(task["pre_task"]))
        self.logger.info("                current_task     : " + str(task["current_task"]))
        self.logger.info("                post_task        : " + str(task["post_task"]))
        self.logger.info("            }")

    def update_create_priority(self):
        for phase in range(1, 4):
            cfg_key_name = 'createPriority_phase' + str(phase)
            current_priority = self.config_set.get(cfg_key_name)
            res = []
            default_priority = self.static_config.create_default_priority[self.config_set.server_mode][
                "phase" + str(phase)]
            for i in range(0, len(current_priority)):
                if current_priority[i] in default_priority:
                    res.append(current_priority[i])
            for j in range(0, len(default_priority)):
                if default_priority[j] not in res:
                    res.append(default_priority[j])
            self.config_set.set(cfg_key_name, res)

    def solve(self, activity) -> bool:
        """
            execute the task by call the corresponding function in func_dict
        """
        for i in range(0, 3):
            if i != 0:
                self.logger.info("Retry Task " + activity + " " + str(i))
            try:
                return func_dict[activity](self)
            except FunctionCallTimeout:
                if not self.deal_with_func_call_timeout():
                    self.push_and_log_error_msg("Function Call Timeout",
                                                "Failed to Restart Game when function call timeout")
                    return False
            except PackageIncorrect as e:
                pkg = e.message
                if not self.deal_with_package_incorrect(pkg):
                    self.push_and_log_error_msg("Package Incorrect", "Failed to Restart Game when package incorrect")
                    return False
            except Exception:
                if self.flag_run:
                    self.push_and_log_error_msg("Script Error Occurred", traceback.format_exc())
                    return False
                return True  # Human take over

    def deal_with_package_incorrect(self, curr_pkg):
        """
            1. no exception
        """
        self.logger.info("Handle package incorrect")
        self.logger.warning("Package incorrect")
        self.logger.warning("Expected: " + self.package_name)
        self.logger.warning("Get     : " + curr_pkg)
        self.logger.warning("Restarting game")
        for i in range(0, 3):
            if i != 0:  # skip first time check
                package = self.connection.get_current_package()
                if package == self.package_name:
                    self.logger.info("current app is target app, close the game and call task restart")
                    self.connection.close_current_app(package)
            try:
                func_dict['restart'](self)
                return True
            except RequestHumanTakeOver:
                return False
            except Exception as e:
                pass
        return False

    def deal_with_func_call_timeout(self):
        """
            deal with co_detect function time out with following logic
            1.current app is target app --> close the game and call task restart
            2.current app is not target app --> call task restart
            3.this func will not raise exception
        """
        self.logger.info("Handle function call timeout")
        package = self.connection.get_current_package()
        if package != self.package_name:
            self.deal_with_package_incorrect(package)
        else:
            for i in range(0, 3):
                self.logger.info("current app is target app, close the game and call task restart")
                self.connection.close_current_app(package)
            try:
                func_dict['restart'](self)
                return True
            except Exception as e:
                pass
        return False

    def push_and_log_error_msg(self, title, message):
        push(self.logger, self.config, title)
        LogTraceback(title, message, self)

    def to_main_page(self, skip_first_screenshot=False):
        img_reactions = {
            # 'normal_task_fight-pause': (908, 508),
            # 'normal_task_retreat-notice': (768, 507),
            'main_page_game-download-resource-notice': (761, 504),
            'main_page_game-download-resource-notice2': (761, 504),
            'main_page_game-download-resource-notice3': (761, 504),
            "main_page_privacy-policy": (772, 501),
            'main_page_quick-home': (1236, 31),
            'main_page_daily-attendance': (640, 360),
            'main_page_item-expire': (925, 119),
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
            "purchase_ap_notice-localized": (919, 165),
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
            'lesson_purchase-lesson-ticket-menu': (921, 169),
            'rewarded_task_purchase-bounty-ticket-menu': (921, 165),
            'scrimmage_purchase-scrimmage-ticket-menu': (921, 162),
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
            "total_assault_total-assault-info": (1165, 107),
            "cafe_cafe-reward-status": (985, 147),
        }
        update = {
            'CN': {
                'main_page_news': (1142, 104),
                'main_page_news2': (1142, 104),
                'normal_task_task-info': (1126, 115),
                "special_task_task-info": (1085, 141),
                "main_page_net-work-unstable": (753, 500),
                'main_page_fail-to-load-game-resources': (740, 437),
            },
            'JP': {
                'main_page_news': (1142, 104),
                'normal_task_task-info': (1126, 115),
                "special_task_task-info": (1126, 141),
                'main_page_attendance-reward': (642, 489),
                'main_page_download-additional-resources': (769, 535),
            },
            'Global': {
                'main_page_news': (1227, 56),
                "special_task_task-info": (1126, 141),
                'normal_task_task-info': (1126, 139),
                'main_page_login-store': (883, 162),
                'main_page_insufficient-inventory-space': (912, 140),
                'main_page_Failed-to-convert-errorResponse': (641, 511),
            }
        }
        img_reactions.update(**update[self.server])
        rgb_possibles = {
            'relationship_rank_up': (640, 360),
            'area_rank_up': (640, 100),
            'level_up': (640, 200),
            'reward_acquired': (640, 100),
            # "fighting_feature": (1226, 51)
        }
        picture.co_detect(self, ["main_page"], rgb_possibles, None, img_reactions, skip_first_screenshot,
                          tentative_click=True)

    def init_image_resource(self):
        return position.init_image_data(self)

    def init_rgb(self):
        try:
            fileName = self.project_dir + '/src/rgb_feature/' + self.identifier + '.json'
            self.rgb_feature = json.load(open(fileName, 'r', encoding='utf-8'))['rgb_feature']
            return True
        except Exception as e:
            self.logger.error(e.__str__())
            self.logger.error("Rgb_Feature initialization failed")
            return False

    def init_config(self):
        try:
            self.update_create_priority()
            self.config = copy.deepcopy(self.config_set.config)
            for field in fields(self.config):
                value = getattr(self.config, field.name)
                if type(value) is not str:
                    continue
                if value.isdigit():
                    setattr(self.config, field.name, int(value))
                elif self.is_float(value):
                    setattr(self.config, field.name, float(value))
            return True
        except Exception as e:
            self.logger.error("Config initialization failed")
            self.logger.error(e.__str__())
            return False

    def swipe(self, fx, fy, tx, ty, duration=None, post_sleep_time=0):
        if not self.flag_run:
            raise RequestHumanTakeOver
        self.logger.info(f"swipe from ( " + str(fx) + " , " + str(fy) + " ) --> ( " + str(tx) + " , " + str(ty) + " )")
        self.control.swipe(fx * self.ratio, fy * self.ratio, tx * self.ratio, ty * self.ratio, duration)
        if post_sleep_time > 0:
            time.sleep(post_sleep_time)

    def u2_swipe(self, fx, fy, tx, ty, duration=None, post_sleep_time=0):
        if not self.flag_run:
            raise RequestHumanTakeOver
        self.logger.info(f"swipe from ( " + str(fx) + " , " + str(fy) + " ) --> ( " + str(tx) + " , " + str(ty) + " )")
        self.u2.swipe(fx * self.ratio, fy * self.ratio, tx * self.ratio, ty * self.ratio, duration)
        if post_sleep_time > 0:
            time.sleep(post_sleep_time)

    def get_ap(self, is_main_page=False):
        if is_main_page:
            region = {
                'CN': (512, 25, 609, 52),
                'Global': (512, 25, 609, 52),
                'JP': (485, 23, 586, 54)
            }
            region = region[self.server]
        else:
            region = {
                'CN': (557, 10, 662, 40),
                'Global': (557, 10, 662, 40),
                'JP': (530, 10, 642, 40)
            }
            region = region[self.server]
        ocr_res = self.ocr.get_region_res(
            self,
            region,
            "en-us",
            "AP",
            "0123456789/"
        )
        _max = -1
        if '/' in ocr_res:
            ocr_res = ocr_res.split('/')
            _max = ocr_res[1]
            ocr_res = ocr_res[0]
        try:
            ocr_res = int(ocr_res)
            _max = int(_max)
            data = {
                "count": ocr_res,
                "max": _max,
                "time": time.time()
            }
            self.config_set.set("ap", data)

            return ocr_res
        except ValueError:
            self.logger.warning("Failed to get AP.")
            return 999

    def get_pyroxene(self, is_main_page=False):
        if is_main_page:
            region = (871, 25, 967, 52)
        else:
            region = (961, 10, 1072, 40)
        ocr_res = self.ocr.get_region_res(
            self,
            region,
            "en-us",
            "Pyroxene",
            "0123456789,",
            0.2
        )
        ret = 0
        for j in range(0, len(ocr_res)):
            if not ocr_res[j].isdigit():
                continue
            ret = ret * 10 + int(ocr_res[j])
        data = {
            "count": ret,
            "time": time.time()
        }
        self.config_set.set("pyroxene", data)
        return ret

    def get_creditpoints(self, is_main_page=False):
        if is_main_page:
            region = (699, 25, 819, 52)
        else:
            region = (769, 10, 896, 40)
        ocr_res = self.ocr.get_region_res(
            self,
            region,
            "en-us",
            "Credit Points",
            "0123456789,",
            0.2
        )
        ret = 0
        for j in range(0, len(ocr_res)):
            if not ocr_res[j].isdigit():
                continue
            ret = ret * 10 + int(ocr_res[j])
        data = {
            "count": ret,
            "time": time.time()
        }
        self.config_set.set("creditpoints", data)
        return ret

    @staticmethod
    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def init_all_data(self):
        self.logger.info("--------Initializing All Data----------")
        self.flag_run = True
        init_funcs = [
            self.init_config,
            self.init_emulator,
            self.init_image_resource,
            self.init_rgb
        ]
        self.scheduler = Scheduler(self.update_signal, self.config_path)
        for (func) in init_funcs:
            if not func():
                self.logger.critical("Initialization Failed")
                self.flag_run = False
                return False

        self.logger.info("--------Initialization Finished----------")
        return True

    def set_screenshot_interval(self, interval):
        self.screenshot_interval = self.screenshot.set_screenshot_interval(interval)

    def wait_uiautomator_start(self):
        for i in range(0, 10):
            try:
                self.u2.uiautomator.start()
                while not self.u2.uiautomator.running():
                    time.sleep(0.1)
                self.latest_img_array = cv2.cvtColor(np.array(self.u2.screenshot()), cv2.COLOR_RGB2BGR)
                return
            except Exception as e:
                print(e)
                self.u2.uiautomator.start()

    def daily_config_refresh(self):
        now = datetime.now()
        hour = now.hour
        last_refresh = datetime.fromtimestamp(self.config.last_refresh_config_time)
        last_refresh_hour = last_refresh.hour
        daily_reset = 4 - (self.server == 'JP' or self.server == 'Global')
        if now.day == last_refresh.day and now.year == last_refresh.year and now.month == last_refresh.month and \
                ((hour < daily_reset and last_refresh_hour < daily_reset) or (
                        hour >= daily_reset and last_refresh_hour >= daily_reset)):
            return
        else:
            self.config.last_refresh_config_time = time.time()
            self.config_set.set("last_refresh_config_time", time.time())
            self.refresh_create_time()
            self.refresh_common_tasks()
            self.refresh_hard_tasks()
            self.logger.info("daily config refreshed")

    def refresh_create_time(self):
        self.config.alreadyCreateTime = 0
        self.config_set.set("alreadyCreateTime", 0)
        self.config_set.config.alreadyCreateTime = 0

    def refresh_common_tasks(self):
        from module.normal_task import readOneNormalTask
        temp = self.config.mainlinePriority
        self.config.unfinished_normal_tasks = []
        if type(temp) is str:
            temp = temp.split(',')
        for i in range(0, len(temp)):
            try:
                self.config.unfinished_normal_tasks.append(
                    readOneNormalTask(temp[i], self.static_config.explore_normal_task_region_range))
            except Exception as e:
                self.logger.error(e.__str__())
        self.config_set.set("unfinished_normal_tasks", self.config.unfinished_normal_tasks)

    def refresh_hard_tasks(self):
        from module.hard_task import readOneHardTask
        self.config.unfinished_hard_tasks = []
        temp = self.config.hardPriority
        if type(temp) is str:
            temp = temp.split(',')
        for i in range(0, len(temp)):
            try:
                self.config.unfinished_hard_tasks.append(
                    readOneHardTask(temp[i], self.static_config.explore_hard_task_region_range))
            except Exception as e:
                self.logger.error(e.__str__())
        self.config_set.set("unfinished_hard_tasks", self.config.unfinished_hard_tasks)

    def handle_then(self):
        action = self.config_set.config.then
        if action == '无动作' or not self.scheduler.is_wait_long():  # Do Nothing
            return
        elif action == '退出 Baas':  # Exit Baas
            self.exit_baas()
        elif action == '退出 模拟器':  # Exit Emulator
            self.exit_emulator()
        elif action == '退出 Baas 和 模拟器':  # Exit Baas and Emulator
            self.exit_emulator()
            self.exit_baas()
        elif action == '关机':  # Shutdown
            self.shutdown()
        self.signal_stop()  # avoid rerunning then action in case of error

    def exit_emulator(self):
        self.logger.info(f"-- BAAS Exit Emulator --")
        if self.config.emulatorIsMultiInstance:
            name = self.config.multiEmulatorName
            num = self.config.emulatorMultiInstanceNumber
            self.logger.info(f"-- Exit Multi Emulator --")
            self.logger.info(f"EmulatorName         : {name}")
            self.logger.info(f"MultiInstanceNumber  : {num}")
            emulator_manager.stop_simulator_classic(name, num)
        else:
            self.file_path = self.config.program_address
            if not process_api.terminate(self.file_path):
                self.logger.error("Emulator exit failed")
                return False
        return True

    def exit_baas(self):
        if self.exit_signal is not None:
            self.exit_signal.emit(0)

    def shutdown(self):
        try:
            self.start_shutdown()
            answer = toast(title='BAAS: Cancel Shutdown?',
                           body='All tasks have been completed: shutting down. Do you want to cancel?',
                           button='Cancel',
                           duration='long'
                           )
            # cancel button pressed
            if answer == {'arguments': 'http:Cancel', 'user_input': {}}:
                self.cancel_shutdown()
        except:
            self.logger.error("Failed to shutdown. It may be due to a lack of administrator privileges.")

    def start_shutdown(self):
        self.logger.info("Running shutdown")
        subprocess.run(["shutdown", "-s", "-t", "60"])

    def cancel_shutdown(self):
        self.logger.info("Shutdown cancelled")
        subprocess.run(["shutdown", "-a"])

    def check_resolution(self):
        self.u2_client = U2Client.get_instance(self.serial)
        self.u2 = self.u2_client.get_connection()
        self.check_atx()
        self.last_refresh_u2_time = time.time()
        temp = self.resolution_uiautomator2()
        self.logger.info("Screen Size  " + str(temp))
        if temp[0] != 1280 or temp[1] != 720:
            self.logger.warning("Screen Size is not 1280x720, we recommend you to use 1280x720.")
        if self.ocr_img_pass_method == 0:
            self.ocr.create_shared_memory(self, temp[0] * temp[1] * 3)
        width = temp[0]
        self.ratio = width / 1280
        self.logger.info("Screen Size Ratio: " + str(self.ratio))

    def resolution_uiautomator2(self):
        for i in range(0, 3):
            try:
                info = self.u2.http.get('/info').json()
                w, h = info['display']['width'], info['display']['height']
                if w < h:
                    w, h = h, w
                return w, h
            except Exception as e:
                print(e)
                time.sleep(1)

    def main_page_update_data(self):
        self.get_ap(True)
        self.get_creditpoints(True)
        self.get_pyroxene(True)


if __name__ == '__main__':
    print(os.path.exists(
        "D:\\github\\bass\\blue_archive_auto_script\\src\\atx_app\\atx-agent_0.10.1_linux_386\\atx-agent"))
    # "D:\\github\\bass\\blue_archive_auto_script\\src\\atx_app\\atx-agent_0.10.0_linux_386\\atx-agent"
    import uiautomator2

    u2 = uiautomator2.connect("127.0.0.1:16512")
    from core.utils import Logger

    logger = Logger(None)
    init = BAAS_U2_Initer(u2._adb_device, logger)
    init.uninstall()
