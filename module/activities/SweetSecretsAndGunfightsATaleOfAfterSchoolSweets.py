import time

from core import color, picture, image
from module import main_story
from module.ExploreTasks.TaskUtils import execute_grid_task
from module.activities.activity_utils import get_stage_data, preprocess_activity_region, \
    preprocess_activity_sweep_times, to_activity, explore_activity_story, explore_activity_mission


def implement(self):
    times = preprocess_activity_sweep_times(self.config.activity_sweep_times)
    region = preprocess_activity_region(self.config.activity_sweep_task_number)
    self.logger.info("activity sweep task number : " + str(region))
    self.logger.info("activity sweep times : " + str(times))
    if len(times) > 0:
        sweep(self, region, times)
    exchange_reward(self)
    return True


def sweep(self, number, times):
    self.to_main_page()
    to_activity(self, "mission", True)
    ap = self.get_ap()
    sweep_one_time_ap = [0, 10, 10, 10, 10, 15, 15, 15, 15, 20, 20, 20, 20]
    for i in range(0, min(len(number), len(times))):
        sweep_times = times[i]
        if type(sweep_times) is float:
            sweep_times = int(ap * sweep_times / sweep_one_time_ap[number[i]])
        click_times = sweep_times
        duration = 1
        if sweep_times > 50:
            sweep_times = int(ap / sweep_one_time_ap[number[i]])
            click_times = int(sweep_times / 2) + 1
            duration = 0.3
        if sweep_times <= 0:
            self.logger.warning("inadequate ap")
            continue
        self.logger.info("Start sweep task " + str(number[i]) + " :" + str(sweep_times) + " times")
        to_mission_task_info(self, number[i])
        res = color.check_sweep_availability(self)
        if res == "sss":
            self.click(1032, 299, count=click_times, duration=duration, wait_over=True)
            res = start_sweep(self, True)
            if res == "inadequate_ap":
                self.logger.warning("inadequate ap")
                return True
            elif res == "sweep_complete":
                self.logger.info("Current sweep task " + str(number[i]) + " :" + str(sweep_times) + " times complete")
                if i != len(number) - 1:
                    to_activity(self, "mission", True)
        elif res == "pass" or res == "no-pass":
            self.logger.warning("task not sss, sweep unavailable")
            continue
    return True


def explore_story(self):
    explore_activity_story(self)

def explore_mission(self):
    explore_activity_mission(self)


def explore_challenge(self):
    self.to_main_page()
    to_activity(self, "challenge", True)
    tasks = [
        "challenge2_sss",
        "challenge2_task",
        "challenge4_sss",
        "challenge4_task"
    ]
    stage_data = get_stage_data(self)
    for i in range(0, len(tasks)):
        data = tasks[i].split("_")
        task_number = int(data[0].replace("challenge", ""))
        to_challenge_task_info(self, task_number)
        current_task_stage_data = stage_data[tasks[i]]
        need_fight = False
        if "task" in data:
            need_fight = True
        elif "sss" in data:
            res = color.check_sweep_availability(self)
            if res == "sss":
                self.logger.info("Challenge " + str(task_number) + " sss no need to fight")
                to_activity(self, "challenge", True)
                i += 1
                continue
            elif res == "no-pass" or res == "pass":
                need_fight = True
        if need_fight:
            execute_grid_task(self, current_task_stage_data)
            i += 1
        main_story.auto_fight(self)
        if self.config.manual_boss:
            self.click(1235, 41)
        to_activity(self, "mission", True)
        to_activity(self, "challenge", True)


def to_mission_task_info(self, number):
    lo = [0, 200, 315, 425, 545, 665]
    index = [1, 2, 3, 4, 5, 4, 5, 1, 2, 3, 4, 5]
    if number in [6, 7]:
        self.u2_swipe(916, 456, 916, 180, duration=0.5, post_sleep_time=0.7)
    if number in [8, 9, 10, 11, 12]:
        self.u2_swipe(943, 670, 943, 170, duration=0.1, post_sleep_time=0.7)
        self.u2_swipe(943, 670, 943, 170, duration=0.1, post_sleep_time=0.7)
    possibles = {'activity_menu': (1124, lo[index[number - 1]])}
    ends = ["normal_task_task-info", "activity_task-info"]
    return picture.co_detect(self, None, None, ends, possibles, True)


def to_challenge_task_info(self, number):
    lo = [0, 178, 279, 377, 477, 564]
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = [
        "activity_task-info",
        "normal_task_task-info",
        "normal_task_SUB"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)





def start_sweep(self, skip_first_screenshot=False):
    img_ends = [
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice-localized" or res == "purchase_ap_notice":
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


def exchange_reward(self):
    to_activity(self, "story", True)
    to_exchange(self, True)
    to_set_exchange_times_menu(self, True)
    if not image.compare_image(self, "activity_exchange-50-times-at-once"):
        self.logger.info("set exchange times to 50 times at once")
        self.click(778, 320, wait_over=True)
    img_possibles = {"activity_set-exchange-times-menu": (772, 482)}
    img_ends = "activity_exchange-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    while 1:
        while color.is_rgb_in_range(self, 314, 684, 235, 255, 223, 243, 65, 85):
            self.click(453, 651, wait_over=True, duration=0.5)
            time.sleep(0.5)
            continue_exchange(self)
            to_exchange(self, True)
        if color.is_rgb_in_range(self, 45, 684, 185, 225, 185, 225, 185, 225):
            if get_exchange_assets(self) >= 6:
                self.logger.info("refresh exchange times")
                refresh_exchange_times(self)
                continue
            else:
                self.logger.info("exchange complete")
                return True


def refresh_exchange_times(self):
    img_possibles = {"activity_exchange-menu": (1155, 114)}
    img_ends = "activity_refresh-exchange-times-notice"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    img_possibles = {"activity_refresh-exchange-times-notice": (768, 500)}
    img_ends = "activity_exchange-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_exchange(self, skip_first_screenshot=False):
    img_possibles = {
        "activity_menu": (279, 639),
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
    picture.co_detect(self, None, None, img_ends, img_possibles, True, tentative_click=True, max_fail_cnt=5)


def get_exchange_assets(self):
    region = {
        "CN": (710, 98, 805, 130),
        "JP": (710, 98, 805, 130),
        "Global": (710, 98, 805, 130),
    }
    return self.ocr.recognize_number(self.latest_img_array, region[self.server], int, self.ratio)
