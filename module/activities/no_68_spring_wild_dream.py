import json
import time

from core import image, color, picture
from module import main_story


def implement(self):
    self.quick_method_to_main_page()
    explore_mission(self)
    if self.config["activity_sweep"]:
        sweep(self, self.config["activity_sweep_task_number"], self.config["activity_sweep_times"])
    if self.config["activity_exchange_reward"]:
        exchange_reward(self)


def sweep(self, number, times):
    to_no_69_spring_wild_dream(self, "mission", True)
    self.swipe(919, 136, 943, 720, duration=0.05)
    time.sleep(0.5)
    self.swipe(919, 136, 943, 720, duration=0.05)
    time.sleep(0.7)
    ap = self.get_ap()
    sweep_one_time_ap = [0, 10, 10, 10, 10, 12, 12, 12, 12, 15, 15, 15, 15]
    sweep_times = times
    click_times = sweep_times
    duration = 1
    if sweep_times > 50:
        sweep_times = int(ap / sweep_one_time_ap[number])
        click_times = int(sweep_times / 2) + 1
        duration = 0.3
    if sweep_times <= 0:
        self.logger.warning("inadequate ap")
        return True
    self.logger.info("Start sweep task " + str(number) + " :" + str(sweep_times) + " times")
    to_task_info(self, number)
    res = check_sweep_availability(self.latest_img_array)
    if res == "sss":
        self.click(1032, 299, count=click_times, duration=duration, wait=False, wait_over=True)
        res = start_sweep(self, True)
        if res == "inadequate_ap":
            self.logger.warning("inadequate ap")
            return True
        elif res == "sweep_complete":
            self.logger.info("sweep task" + str(number) + " finished")
            return True
    elif res == "pass" or res == "no-pass":
        self.logger.warning("task not sss, sweep unavailable")
        return True


def explore_story(self):
    to_no_69_spring_wild_dream(self, "story")


def start_fight(self, i):
    rgb_possibles = {"formation_edit" + str(i): (1156, 659)}
    rgb_ends = "fighting_feature"
    picture.co_detect(self, rgb_ends, rgb_possibles, skip_first_screenshot=True)


def explore_mission(self):
    to_no_69_spring_wild_dream(self, "mission", True)
    last_target_task = 1
    characteristic = [
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
        'pierce1',
    ]
    while last_target_task <= 12:
        self.swipe(919, 136, 943, 720, duration=0.05)
        time.sleep(0.5)
        self.swipe(919, 136, 943, 720, duration=0.05)
        time.sleep(0.7)
        to_task_info(self, last_target_task)
        res = check_sweep_availability(self.latest_img_array)
        while res == "sss" and last_target_task <= 11:
            self.logger.info("Current task sss check next task")
            self.click(1168, 353, duration=1, wait=False, wait_over=True)
            last_target_task += 1
            image.detect(self, "normal_task_task-info")
            res = check_sweep_availability(self.latest_img_array)
        if last_target_task >= 12:
            self.logger.info("All TASK SSS")
            return True
        if res == "no-pass" or res == "pass":
            number = self.config[characteristic[last_target_task - 1]]
            self.logger.info("according to characteristic, choose formation " + str(number))
            to_formation_edit_i(self, number, (940, 538), True)
            start_fight(self, number)
            main_story.auto_fight(self)
            to_no_69_spring_wild_dream(self, "story")
            to_no_69_spring_wild_dream(self, "mission", True)


def explore_challenge(self):
    to_no_69_spring_wild_dream(self, "challenge")
    if color.judge_rgb_range(self.latest_img_array, 945, 351, 200, 230, 200, 230, 200, 230):
        self.logger.warning("Challenge not open")
        return False


def to_no_69_spring_wild_dream(self, region, skip_first_screenshot=False):
    possibles = {
        "activity_enter1": (1196, 195),
        "activity_enter2": (100, 149),
        'activity_fight-success-confirm': (640, 663),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        'purchase_ap_notice': (919, 168),
        "plot_skip-plot-notice": (766, 520),
        "normal_task_help": (1017, 131),
        "normal_task_task-info": (1087, 141),
        "activity_play-guide": (1184, 152),
        'main_story_fight-confirm': (1168, 659),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fail-confirm': (643, 658),
        'normal_task_task-finish': (1038, 662),
        'normal_task_fight-confirm': (1168, 659),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        'normal_task_skip-sweep-complete': (643, 506),
        'normal_task_fight-complete-confirm': (1160, 666),
        'normal_task_reward-acquired-confirm': (800, 660),
        'normal_task_mission-conclude-confirm': (1042, 671),
        "activity_exchange-confirm": (673, 603),
    }
    ends = "activity_menu"
    image.detect(self, ends, possibles, skip_first_screenshot=skip_first_screenshot)
    if region is None:
        return True
    rgb_lo = {
        "mission": 863,
        "story": 688,
        "challenge": 1046,
    }
    click_lo = {
        "mission": 1027,
        "story": 848,
        "challenge": 1196,
    }
    while True:
        if not self.flag_run:
            return False
        if not color.judge_rgb_range(self.latest_img_array, rgb_lo[region], 121, 20, 60, 40, 70, 70, 100):
            self.click(click_lo[region], 76)
            time.sleep(self.screenshot_interval)
            self.latest_img_array = self.get_screenshot_array()
        else:
            return True


def to_task_info(self, number):
    lo = [0, 184, 308, 422, 537, 645]
    index = [1, 2, 3, 4, 5, 4, 5, 1, 2, 3, 4, 5]
    if number in [6, 7]:
        self.swipe(916, 483, 916, 219, duration=0.5)
        time.sleep(0.7)
    if number in [8, 9, 10, 11, 12]:
        self.swipe(943, 698, 943, 0, duration=0.1)
        time.sleep(0.7)
    possibles = {'activity_menu': (1124, lo[index[number - 1]])}
    ends = "normal_task_task-info"
    image.detect(self, ends, possibles)


def check_sweep_availability(img):
    if color.judge_rgb_range(img, 211, 369, 192, 212, 192, 212, 192, 212) and \
        color.judge_rgb_range(img, 211, 402, 192, 212, 192, 212, 192, 212) and \
        color.judge_rgb_range(img, 211, 436, 192, 212, 192, 212, 192, 212):
        return "no-pass"
    if color.judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) and \
        color.judge_rgb_range(img, 211, 404, 225, 255, 200, 255, 20, 60) and \
        color.judge_rgb_range(img, 211, 434, 225, 255, 200, 255, 20, 60):
        return "sss"
    if color.judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) or \
        color.judge_rgb_range(img, 211, 404, 225, 255, 200, 255, 20, 60) or \
        color.judge_rgb_range(img, 211, 434, 225, 255, 200, 255, 20, 60):
        return "pass"


def to_formation_edit_i(self, i, lo, skip_first_screenshot=False):
    loy = [195, 275, 354, 423]
    y = loy[i - 1]
    rgb_ends = "formation_edit" + str(i)
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_possibles.pop("formation_edit" + str(i))
    img_possibles = {"normal_task_task-info": (lo[0], lo[1])}
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def start_sweep(self, skip_first_screenshot=False):
    rgb_ends = [
        "purchase_ap_notice",
        "start_sweep_notice",
    ]
    rgb_possibles = {
        "mission_info": (941, 411),
    }
    img_ends = [
        "purchase_ap_notice",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice" or res == "buy_ap_notice":
        return "inadequate_ap"
    rgb_ends = [
        "skip_sweep_complete",
        "sweep_complete"
    ]
    rgb_possibles = {"start_sweep_notice": (765, 501)}
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    return "sweep_complete"


def to_exchange(self, skip_first_screenshot=False):
    img_possibles = {
        "activity_menu": (230, 639),
        "activity_set-exchange-times-menu": (935, 195),
        "activity_exchange-confirm": (673, 603),
    }
    img_ends = "activity_exchange-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_set_exchange_times_menu(self, skip_first_screenshot=False):
    img_possibles = {"activity_exchange-menu": (122, 105)}
    img_ends = "activity_set-exchange-times-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def continue_exchange(self):
    img_possibles = {"activity_continue-exchange": (931, 600)}
    img_ends = "activity_continue-exchange-grey"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def exchange_reward(self):
    to_no_69_spring_wild_dream(self, None, True)
    to_exchange(self, True)
    if not self.config["activity_exchange_50_times_at_once"]:
        to_set_exchange_times_menu(self, True)
        self.config["activity_exchange_50_times_at_once"] = True
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        if not image.compare_image(self, "activity_exchange-50-times-at-once", 3):
            self.logger.info("set exchange times to 50 times at once")
            self.click(778, 320, wait_over=True)
            img_possibles = {"activity_set-exchange-times-menu": (772, 482)}
            img_ends = "activity_exchange-menu"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
    while 1:
        while color.judge_rgb_range(self.latest_img_array, 314, 684, 235, 255, 223, 243, 65, 85):
            self.click(453, 651, wait=False, wait_over=True)
            time.sleep(0.5)
            continue_exchange(self)
            to_exchange(self, True)
        while color.judge_rgb_range(self.latest_img_array, 479, 681, 109, 129, 211, 231, 235, 255):
            self.click(453, 651, wait=False, wait_over=True)
            time.sleep(0.5)
            continue_exchange(self)
            to_exchange(self, True)
        if image.compare_image(self, "activity_refresh-exchange-times-grey", 3):
            self.logger.info("exchange complete")
            return True
        if image.compare_image(self, "activity_refresh-exchange-times-bright", 3):
            refresh_exchange_times(self)


def refresh_exchange_times(self):
    img_possibles = {"activity_exchange-menu": (1155, 114)}
    img_ends = "activity_refresh-exchange-times-notice"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    img_possibles = {"activity_refresh-exchange-times-notice": (768, 500)}
    img_ends = "activity_exchange-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
