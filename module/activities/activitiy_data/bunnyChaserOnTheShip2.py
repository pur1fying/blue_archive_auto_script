import time

from core import color, picture, image
from module import main_story
from module.ExploreTasks.TaskUtils import execute_grid_task
from module.activities.activity_utils import get_stage_data, preprocess_activity_region, preprocess_activity_sweep_times


def implement(self):
    times = preprocess_activity_sweep_times(self.config.activity_sweep_times)
    region = preprocess_activity_region(self.config.activity_sweep_task_number)
    self.logger.info("activity sweep task number : " + str(region))
    self.logger.info("activity sweep times : " + str(times))
    if len(times) > 0:
        sweep(self, region, times)
    return True


def sweep(self, number, times):
    self.to_main_page()
    to_activity(self, "mission", True, True)
    ap = self.get_ap()
    sweep_one_time_ap = [0, 10, 10, 10, 12, 12, 12, 15, 15, 15]
    for i in range(0, min(len(number), len(times))):
        sweep_times = times[i]
        if type(sweep_times) is float:
            sweep_times = int(ap * sweep_times / sweep_one_time_ap[number[i]])
        click_times = sweep_times - 1
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
                    to_activity(self, "mission", True, True)
        elif res == "pass" or res == "no-pass":
            self.logger.warning("task not sss, sweep unavailable")
            continue
    return True


# 推剧情的测试完没有问题
def explore_story(self):
    self.to_main_page()
    to_activity(self, "story", True, True)
    last_target_task = 1
    total_stories = 5
    while self.flag_run:
        plot = to_story_task_info(self, last_target_task)
        if plot == "normal_task_task-info" or plot == "activity_task-info":
            res = color.check_sweep_availability(self)
        elif plot == "main_story_episode-info":
            if not color.rgb_in_range(self, 362, 322, 232, 255, 219, 255, 0, 30):
                res = "sss"
            else:
                res = "no-pass"
        while res == "sss" and last_target_task <= total_stories - 1:
            self.logger.info("Current story sss check next story")
            self.click(1168, 353, duration=1, wait_over=True)
            last_target_task += 1
            plot = picture.co_detect(self, img_ends=["normal_task_task-info", "activity_task-info",
                                                     "main_story_episode-info"])
            if plot == "normal_task_task-info" or plot == "activity_task-info":
                res = color.check_sweep_availability(self)
            elif plot == "main_story_episode-info":
                if not color.rgb_in_range(self, 362, 322, 232, 255, 219, 255, 0, 30):
                    res = "sss"
                else:
                    res = "no-pass"
        if last_target_task == total_stories and res == "sss":
            self.logger.info("All STORY SSS")
            return True
        start_story(self)
        to_activity(self, "mission", True)
        to_activity(self, "story", True, True)


def start_story(self):
    img_possibles = {
        "activity_task-info": (940, 538),
        "normal_task_task-info": (940, 538),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
        "main_story_episode-info": (629, 518),
    }
    rgb_ends = [
        "formation_edit1",
        "reward_acquired"
    ]
    res = picture.co_detect(self, rgb_ends, None, None, img_possibles, skip_first_screenshot=True)
    if res == "formation_edit1":
        start_fight(self, 1)
        main_story.auto_fight(self)
    elif res == "reward_acquired":
        pass
    return


def start_fight(self, i):
    rgb_possibles = {"formation_edit" + str(i): (1156, 659)}
    rgb_ends = "fighting_feature"
    picture.co_detect(self, rgb_ends, rgb_possibles, skip_first_screenshot=True)


def explore_mission(self):
    self.to_main_page()
    to_activity(self, "mission", True, True)
    last_target_mission = 1
    total_missions = 9
    characteristic = get_stage_data(self)["mission"]
    while last_target_mission <= total_missions and self.flag_run:
        to_mission_task_info(self, last_target_mission)
        res = color.check_sweep_availability(self)
        while res == "sss" and last_target_mission <= total_missions - 1 and self.flag_run:
            self.logger.info("Current task sss check next task")
            self.click(1168, 353, duration=1, wait_over=True)
            last_target_mission += 1
            picture.co_detect(self, img_ends=["normal_task_task-info", "activity_task-info"])
            res = color.check_sweep_availability(self)
        if last_target_mission == total_missions and res == "sss":
            self.logger.info("All MISSION SSS")
            return True
        number = self.config[characteristic[last_target_mission - 1]]
        self.logger.info("according to config, choose formation " + str(number))
        to_formation_edit_i(self, number, (940, 538), True)
        start_fight(self, number)
        main_story.auto_fight(self)
        to_activity(self, "story")
        to_activity(self, "mission", True, True)


# 挑战这里还没改动
def explore_challenge(self):
    self.to_main_page()
    to_activity(self, "challenge", True, True)
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
            if not execute_grid_task(self, current_task_stage_data):
                self.logger.error(f"Skipping task due to error.")
                continue
            i += 1
        main_story.auto_fight(self)
        if self.config.manual_boss:
            self.click(1235, 41)
        to_activity(self, "mission", True)
        to_activity(self, "challenge", True)


def to_activity(self, region, skip_first_screenshot=False, need_swipe=False):
    task_info = {
        'CN': (1087, 141),
        'Global': (1128, 141),
        'JP': (1126, 115)
    }
    task_info_x = {
        'CN': 1087,
        'Global': 1128,
        'JP': 1126
    }
    img_possibles = {
        "activity_enter1": (1196, 195),
        "activity_enter2": (100, 149),
        "activity_enter3": (218, 530),
        'activity_fight-success-confirm': (640, 663),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "purchase_ap_notice": (919, 168),
        'purchase_ap_notice-localized': (919, 168),
        "plot_skip-plot-notice": (766, 520),
        "normal_task_help": (1017, 131),
        "activity_task-info": (task_info_x[self.server], 141),
        "normal_task_task-info": task_info[self.server],
        "activity_play-guide": (1184, 152),
        'main_story_fight-confirm': (1168, 659),
        "main_story_episode-info": (917, 161),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fail-confirm': (643, 658),
        'normal_task_task-finish': (1038, 662),
        'normal_task_fight-confirm': (1168, 659),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        'normal_task_skip-sweep-complete': (643, 506),
        'normal_task_fight-complete-confirm': (1160, 666),
        'normal_task_reward-acquired-confirm': (800, 660),
        "activity_exchange-confirm": (673, 603),
    }
    img_ends = "activity_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)
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
    while self.flag_run:
        if not color.rgb_in_range(self, rgb_lo[region], 114, 20, 60, 40, 80, 70, 116):
            self.click(click_lo[region], 87)
            time.sleep(self.screenshot_interval)
            self.latest_img_array = self.get_screenshot_array()
        else:
            if need_swipe:
                if region == "mission":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
            return True


def to_story_task_info(self, number):
    lo = [0, 180, 280, 380, 480, 580, 680]
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = [
        "activity_task-info",
        "normal_task_task-info",
        "main_story_episode-info"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_mission_task_info(self, number):
    lo = [0, 184, 308, 422, 537, 645]
    index = [1, 2, 3, 4, 5, 2, 3, 4, 5]
    if number in [6, 7, 8, 9]:
        self.u2_swipe(943, 698, 943, 0, duration=0.05, post_sleep_time=0.7)
        self.u2_swipe(943, 698, 943, 0, duration=0.05, post_sleep_time=0.7)
    possibles = {'activity_menu': (1124, lo[index[number - 1]])}
    ends = "normal_task_task-info"
    image.detect(self, ends, possibles)


def to_challenge_task_info(self, number):
    lo = [0, 178, 279, 377, 477, 564]
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = [
        "activity_task-info",
        "normal_task_task-info",
        "normal_task_SUB"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_formation_edit_i(self, i, lo=(0, 0), skip_first_screenshot=False):
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
    img_possibles = {
        "activity_task-info": (lo[0], lo[1]),
        "normal_task_task-info": (lo[0], lo[1]),
        "normal_task_SUB": (647, 517)
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


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
        while color.rgb_in_range(self, 314, 684, 235, 255, 223, 243, 65, 85):
            self.click(453, 651, wait_over=True, duration=0.5)
            time.sleep(0.5)
            continue_exchange(self)
            to_exchange(self, True)
        if color.rgb_in_range(self, 45, 684, 185, 225, 185, 225, 185, 225):
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
