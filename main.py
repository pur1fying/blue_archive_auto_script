import json
import threading
import time

import numpy as np
import uiautomator2 as u2
from cnocr import CnOcr
import concurrent.futures
import module
from core.utils import *
from core.exception import ScriptError
from core.notification import notify
from core.scheduler import Scheduler
from core import position, color, image
from gui.util.config_set import ConfigSet

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
    'main_story': module.main_story.start,
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
}


class Main:
    def __init__(self, logger_signal=None, button_signal=None, update_signal=None):
        self.img_cnt = 0
        self.latest_screenshot_time = None
        self.scheduler = None
        self.screenshot_interval = None
        self.flag_run = None
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
        if not self.init_all_data():
            return
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
        for i in range(count):
            self.logger.info(f"click ({x} ,{y})")
            if rate > 0:
                time.sleep(rate)
            noisex = int(np.random.uniform(-5, 5))
            noisey = int(np.random.uniform(-5, 5))
            x = x + noisex
            y = y + noisey
            x = max(0, x)
            y = max(0, y)
            x = min(1280, x)
            y = min(720, y)
            self.connection.click(x, y)
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
        if self.server == "CN":
            possibles = {
                'main_page_quick-home': (1236, 31),
                'main_page_login-feature': (640, 360),
                'main_page_news': (1142, 104),
                'main_page_relationship-rank-up': (640, 360),
                'main_page_full-notice': (887, 165),
                'main_story_fight-confirm': (1168, 659),
                'normal_task_task-finish': (1038, 662),
                'normal_task_prize-confirm': (776, 655),
                'normal_task_fail-confirm': (643, 658),
                'normal_task_fight-task-info': (420, 592),
                "normal_task_sweep-complete": (643, 585),
                "normal_task_start-sweep-notice": (887, 164),
                "normal_task_unlock-notice": (887, 164),
                'normal_task_skip-sweep-complete': (643, 506),
                "normal_task_charge-challenge-counts": (887, 164),
                "buy_ap_notice": (919, 165),
                'normal_task_mission-operating-task-info': (1000, 664),
                'normal_task_task-info': (1084, 139),
                'normal_task_mission-operating-task-info-notice': (416, 595),
                'normal_task_mission-pause': (768, 501, 3),
                'normal_task_task-begin-without-further-editing-notice': (888, 163),
                'normal_task_task-operating-round-over-notice': (888, 163),
                'momo_talk_momotalk-peach': (1123, 122),
                'cafe_students-arrived': (922, 189),
                'group_sign-up-reward': (920, 159),
                'cafe_cafe-reward-status': (905, 159),
                'cafe_invitation-ticket': (835, 97),
                'lesson_lesson-information': (964, 117),
                'lesson_all-locations': (1138, 117),
                'lesson_lesson-report': (642, 556),
                "special_task_task-info": (1085, 141),
                "rewarded_task_purchase-ticket-notice": (888, 162),
                'arena_battle-win': (640, 530),
                'arena_battle-lost': (640, 468),
                'arena_season-record': (640, 538),
                'arena_best-record': (640, 538),
                'plot_menu': (1202, 37),
                'plot_skip-plot-button': (1208, 116),
                'plot_skip-plot-notice': (770, 519),
                'activity_story-fight-success-confirm': (638, 674)
            }
            fail_cnt = 0
            click_pos = [
                [640, 100],
                [1236, 31],
                [640, 360],
                [640, 100],
                [640, 200]
            ]
            los = [
                "reward_acquired",
                "home",
                'relationship_rank_up',
                'area_rank_up',
                'level_up'
            ]
            while True:
                color.wait_loading(self, skip_first_screenshot)
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
            possibles = {
                'normal_task_fight-complete-confirm': (1160, 666),
                'normal_task_reward-acquired-confirm': (800, 660),
                'normal_task_task-operating-mission-info': (397, 592),
                'normal_task_mission-operating-feature': (995, 668),
                'normal_task_quit-mission-info': (772, 511),
                'normal_task_mission-conclude-confirm': (1042, 671),
                'normal_task_obtain-present': (640,519),
            }
            fail_cnt = 0
            while True:
                color.wait_loading(self, skip_first_screenshot)
                res = color.detect_rgb_one_time(self, [], [], ends)
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
                    time.sleep(self.screenshot_interval)
                    fail_cnt += 1
                    if fail_cnt > 10:
                        self.logger.info("tentative clicks")
                        self.click(1228, 41, False)
                        time.sleep(self.screenshot_interval)
                        fail_cnt = 0
            return True

    def wait_screenshot_updated(self):
        while not self.screenshot_updated:
            time.sleep(0.01)

    def init_rgb(self):
        try:
            self.logger.info("Start initializing rgb_feature")
            if self.server == 'CN':
                self.rgb_feature = json.load(open('src/rgb_feature/rgb_feature_CN.json'))['rgb_feature']
            elif self.server == 'Global':
                self.rgb_feature = json.load(open('src/rgb_feature/rgb_feature_Global.json'))['rgb_feature']
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
            if self.server == 'CN':
                if not self.ocrCN:
                    self.ocrCN = CnOcr(det_model_name='ch_PP-OCRv3_det',
                                       det_model_fp='src/ocr_models/ch_PP-OCRv3_det_infer.onnx',
                                       rec_model_name='densenet_lite_114-fc',
                                       rec_model_fp='src/ocr_models/cn_densenet_lite_136.onnx')
                    img_CN = cv2.imread('src/test_ocr/CN.png')
                    self.logger.info("Test ocrCN : " + self.ocrCN.ocr_for_single_line(img_CN)['text'])
            elif self.server == 'Global':
                if not self.ocrEN:
                    self.ocrEN = CnOcr(det_model_name="en_PP-OCRv3_det",
                                       det_model_fp='src/ocr_models/en_PP-OCRv3_det_infer.onnx',
                                       rec_model_name='en_number_mobile_v2.0',
                                       rec_model_fp='src/ocr_models/en_number_mobile_v2.0_rec_infer.onnx', )
                    img_EN = cv2.imread('src/test_ocr/EN.png')
                    self.logger.info("Test ocrEN : " + self.ocrEN.ocr_for_single_line(img_EN)['text'])
            if not self.ocrNUM:
                self.ocrNUM = CnOcr(det_model_name='en_PP-OCRv3_det',
                                    det_model_fp='src/ocr_models/en_PP-OCRv3_det_infer.onnx',
                                    rec_model_name='number-densenet_lite_136-fc',
                                    rec_model_fp='src/ocr_models/number-densenet_lite_136.onnx')

                img_NUM = cv2.imread('src/test_ocr/NUM.png')
                self.logger.info("Test ocrNUM : " + self.ocrNUM.ocr_for_single_line(img_NUM)['text'])
            self.logger.info("OCR initialization concluded")
            return True
        except Exception as e:
            self.logger.error("OCR initialization failed")
            self.logger.error(e)
            return False

    def get_ap(self):
        try:
            _img = self.latest_img_array[10:40, 560:658, :]
            t1 = time.time()
            if self.server == 'CN':
                _ocr_res = self.ocrCN.ocr_for_single_line(_img)
            elif self.server == 'Global':
                _ocr_res = self.ocrEN.ocr_for_single_line(_img)
            else:
                self.logger.error("Unknown Server Error")
                return "UNKNOWN"
            t2 = time.time()
            self.logger.info("ocr_ap: " + str(t2 - t1)[0:5] + " " + _ocr_res["text"])
            ap = 0
            for j in range(0, len(_ocr_res['text'])):
                if (not _ocr_res['text'][j].isdigit()) and _ocr_res['text'][j] != '/' and _ocr_res['text'][j] != '.':
                    return "UNKNOWN"
                if _ocr_res['text'][j].isdigit():
                    ap = ap * 10 + int(_ocr_res['text'][j])
                elif _ocr_res['text'][j] == '/':
                    return ap
            return "UNKNOWN"
        except Exception as e:
            self.logger.error(e)
            return "UNKNOWN"

    def get_pyroxene(self):
        _img = self.latest_img_array[10:40, 961:1072, :]
        t1 = time.time()
        if self.server == 'CN':
            _ocr_res = self.ocrCN.ocr_for_single_line(_img)
        elif self.server == 'Global':
            _ocr_res = self.ocrEN.ocr_for_single_line(_img)
        else:
            self.logger.error("Unknown Server Error")
            return "UNKNOWN"
        t2 = time.time()
        self.logger.info("ocr_pyroxene:" + str(t2 - t1)[0:5] + " " + _ocr_res["text"])
        temp = 0

        for j in range(0, len(_ocr_res['text'])):
            if not _ocr_res['text'][j].isdigit():
                continue
            temp = temp * 10 + int(_ocr_res['text'][j])
        return temp

    def get_creditpoints(self):
        _img = self.latest_img_array[10:40, 769:896, :]
        t1 = time.time()
        if self.server == 'CN':
            _ocr_res = self.ocrCN.ocr_for_single_line(_img)
        elif self.server == 'Global':
            _ocr_res = self.ocrEN.ocr_for_single_line(_img)
        else:
            self.logger.error("Unknown Server Error")
            return "UNKNOWN"
        t2 = time.time()
        self.logger.info("ocr_creditpoints:" + str(t2 - t1)[0:5] + " " + _ocr_res["text"])
        temp = 0
        for j in range(0, len(_ocr_res['text'])):
            if not _ocr_res['text'][j].isdigit():
                continue
            temp = temp * 10 + int(_ocr_res['text'][j])
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
        self.init_package_name()
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

    def init_package_name(self):
        server = self.config['server']
        if server == '官服':
            self.package_name = 'com.RoamingStar.BlueArchive'
        elif server == 'B服':
            self.package_name = 'com.RoamingStar.BlueArchive.bilibili'
        elif server == '国际服':
            self.package_name = 'com.nexon.bluearchive'
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
    # t.thread_starter()
    t.solve('explore_hard_task')
    t.solve('tactical_challenge_shop')
    t.solve('de_clothes')
    t.solve('common_shop')
    t.quick_method_to_main_page()
    # t.solve('tactical_challenge_shop')
    # t.quick_method_to_main_page()
    # t.solve('arena')
    # t.quick_method_to_main_page()
    # t.solve("rewarded_task")
    # t.quick_method_to_main_page()
    # t.solve('clear_special_task_power')
    # t.quick_method_to_main_page()
    # t.solve('lesson')
    # t.quick_method_to_main_page()
    # t.solve('scrimmage')
    # t.quick_method_to_main_page()
    # t.solve('collect_reward')
    # t.quick_method_to_main_page()
    # t.solve('group')
    # t.quick_method_to_main_page()
    # t.solve('cafe_reward')
    # t.quick_method_to_main_page()
    # t.solve('normal_task')
    # t.quick_method_to_main_page()
    # t.solve('mail')
    # t.quick_method_to_main_page()
    # t.solve('hard_task')
    # t.quick_method_to_main_page()

    t.solve('explore_hard_task')
    t.quick_method_to_main_page()
    t.solve('momo_talk')
    t.thread_starter()
    path = "src/event/auto clear bright.png"
    img = t.get_screenshot_array()
    print(check_sweep_availability(img))
    return_data1 = get_x_y(img, path)
    print(return_data1)

    ocr_res = t.img_ocr(img)
    print(str(ocr_res))
