from module.activities.activity_utils import get_stage_data
import time
from core import image, color, picture
from module import main_story
from module.ExploreTasks.TaskUtils import execute_grid_task


def implement(self):
    self.quick_method_to_main_page()
    region = self.config["activity_sweep_task_number"]
    times = self.config["activity_sweep_times"]
    if times > 0:
        return sweep(self, region, times)
    else:
        return True


def sweep(self, number, times):
    to_activity(self, "mission", True)
    self.swipe(919, 136, 943, 720, duration=0.05, post_sleep_time=0.5)
    ap = self.get_ap()
    sweep_one_time_ap = [0, 10, 10, 15, 15, 15, 15]

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
    to_mission_task_info(self, number)
    res = check_sweep_availability(self)
    if res == "sss":
        self.click(1032, 299, count=click_times, duration=duration, wait_over=True)
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
    self.quick_method_to_main_page()
    to_activity(self, "story", True)
    last_target_task = 1
    total_stories = 10
    while self.flag_run:
        self.swipe(919, 136, 943, 720, duration=0.05, post_sleep_time=0.5)
        to_story_task_info(self, last_target_task)
        res = check_sweep_availability(self)
        while res == "sss" and last_target_task <= total_stories - 1:
            self.logger.info("Current story sss check next story")
            self.click(1168, 353, duration=1, wait_over=True)
            last_target_task += 1
            picture.co_detect(self, img_ends="normal_task_task-info")
            res = check_sweep_availability(self)
        if res == "no-pass" or res == "pass":
            start_story(self)
            to_activity(self, "mission", True)
            to_activity(self, "story", True)
        if last_target_task == total_stories:
            self.logger.info("All STORY SSS")
            return True


def start_story(self):
    img_possibles = {
        "normal_task_task-info": (940, 538),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
    }
    rgb_ends = [
        "formation_edit1",
        "activity_menu",
    ]
    res = picture.co_detect(self, rgb_ends, None, None, img_possibles, skip_loading=True)
    if res == "formation_edit1":
        start_fight(self, 1)
        main_story.auto_fight(self)
    elif res == "activity_menu":
        pass
    return


def start_fight(self, i):
    rgb_possibles = {"formation_edit" + str(i): (1156, 659)}
    rgb_ends = "fighting_feature"
    picture.co_detect(self, rgb_ends, rgb_possibles, skip_loading=True)


def explore_mission(self):
    self.quick_method_to_main_page()
    to_activity(self, "mission", True)
    last_target_mission = 1
    total_missions = 6
    characteristic = [
        'mystic1',
        'pierce1',
        'mystic1',
        'mystic1',
        'pierce1',
        'mystic1',
    ]
    while last_target_mission <= total_missions:
        self.swipe(919, 136, 943, 720, duration=0.05, post_sleep_time=0.5)
        to_mission_task_info(self, last_target_mission)
        res = check_sweep_availability(self)
        while res == "sss" and last_target_mission <= total_missions - 1:
            self.logger.info("Current task sss check next task")
            self.click(1168, 353, duration=1, wait_over=True)
            last_target_mission += 1
            image.detect(self, "normal_task_task-info")
            res = check_sweep_availability(self)
        if res == "no-pass" or res == "pass":
            number = self.config[characteristic[last_target_mission - 1]]
            self.logger.info("according to config, choose formation " + str(number))
            to_formation_edit_i(self, number, (940, 538), True)
            start_fight(self, number)
            main_story.auto_fight(self)
            to_activity(self, "story")
            to_activity(self, "mission", True)
        if last_target_mission == total_missions:
            self.logger.info("All MISSION SSS")
            return True


def explore_challenge(self):
    self.quick_method_to_main_page()
    to_activity(self, "challenge")
    tasks = [
        "challenge2_sss",
        "challenge2_task"
    ]
    stage_data = get_stage_data(self)
    for i in range(0, len(tasks)):
        current_task_stage_data = stage_data[tasks[i]]
        data = tasks[i].split("_")
        task_number = int(data[0].replace("challenge", ""))
        to_challenge_task_info(self, task_number)
        need_fight = False
        if "task" in data:
            need_fight = True
        elif "sss" in data:
            res = check_sweep_availability(self)
            if res == "sss":
                self.logger.info("Challenge " + str(task_number) + " sss no need to fight")
                continue
            elif res == "no-pass" or res == "pass":
                need_fight = True
        if need_fight:
            execute_grid_task(self, current_task_stage_data)
            main_story.auto_fight(self)
            if self.config['manual_boss']:
                self.click(1235, 41)
            to_activity(self, "mission", True)
            to_activity(self, "challenge", True)


def to_activity(self, region, skip_first_screenshot=False):
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
    img_ends = "activity_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_loading=skip_first_screenshot)
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
        if not color.is_rgb_in_range(self, rgb_lo[region], 121, 20, 60, 40, 70, 70, 100):
            self.click(click_lo[region], 76)
            time.sleep(self.screenshot_interval)
            self.latest_img_array = self.get_screenshot_array()
        else:
            return True


def to_story_task_info(self, number):
    lo = [0, 184, 277, 375, 480, 574]
    index = [0, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    if number in [6, 7, 8, 9, 10]:
        self.swipe(943, 593, 943, 0, duration=0.1, post_sleep_time=0.7)
    img_possibles = {'activity_menu': (1124, lo[index[number]])}
    img_ends = "normal_task_task-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_mission_task_info(self, number):
    lo = [0, 184, 300, 416, 527]
    index = [0, 1, 2, 3, 4, 3, 4]
    if number in [5, 6]:
        self.swipe(943, 593, 943, 0, duration=0.1, post_sleep_time=0.7)
    img_possibles = {'activity_menu': (1124, lo[index[number]])}
    img_ends = "normal_task_task-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_challenge_task_info(self, number):
    lo = [0, 178, 279, 377]
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = "normal_task_task-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def check_sweep_availability(self):
    if color.is_rgb_in_range(self, 211, 369, 192, 212, 192, 212, 192, 212) and \
        color.is_rgb_in_range(self, 211, 402, 192, 212, 192, 212, 192, 212) and \
        color.is_rgb_in_range(self, 211, 436, 192, 212, 192, 212, 192, 212):
        return "no-pass"
    if color.is_rgb_in_range(self, 211, 368, 225, 255, 200, 255, 20, 60) and \
        color.is_rgb_in_range(self, 211, 404, 225, 255, 200, 255, 20, 60) and \
        color.is_rgb_in_range(self, 211, 434, 225, 255, 200, 255, 20, 60):
        return "sss"
    if color.is_rgb_in_range(self, 211, 368, 225, 255, 200, 255, 20, 60) or \
        color.is_rgb_in_range(self, 211, 404, 225, 255, 200, 255, 20, 60) or \
        color.is_rgb_in_range(self, 211, 434, 225, 255, 200, 255, 20, 60):
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

