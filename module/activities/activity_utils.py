import json
import time

from core import color, picture
from core.image import compare_image, swipe_search_target_str
from module import main_story
from module.ExploreTasks.TaskUtils import execute_grid_task


# activity config
def get_stage_data(self):
    json_path = 'src/explore_task_data/activities/' + self.current_game_activity + '.json'
    with open(json_path, 'r') as f:
        stage_data = json.load(f)
    return stage_data


def to_activity(self, region=None, skip_first_screenshot=False):
    img_possibles = {
        "main_page_get-character": (640, 360),
        "activity_enter1": (1196, 195),
        "activity_enter2": (100, 149),
        "activity_enter3": (218, 530),
        'activity_fight-success-confirm': (640, 663),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "purchase_ap_notice": (919, 168),
        'purchase_ap_notice-localized': (919, 168),
        "plot_skip-plot-notice": (766, 520),
        "activity_get-collectable-item1": (508, 505),
        "activity_get-collectable-item2": (505, 537),
        "normal_task_help": (1017, 131),
        "activity_task-info": (1128, 141),
        "normal_task_task-info": (1126, 115),
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

    img_possibles = {
        "story": {
            "activity_story-not-chosen-0": (844, 89),
            "activity_story-not-chosen-1": (936, 89),
        },
        "mission": {
            "activity_mission-not-chosen-0": (1028, 91),
            "activity_mission-not-chosen-1": (1200, 91),
        },
        "challenge": {
            "activity_challenge-not-chosen-0": (1200, 89)
        },
    }

    img_ends = {
        "story": [
            "activity_story-chosen-0",
            "activity_story-chosen-1",
        ],
        "mission": [
            "activity_mission-chosen-0",
            "activity_mission-chosen-1",
        ],
        "challenge": [
            "activity_challenge-chosen-0",
        ]
    }
    img_possibles = img_possibles[region]
    img_ends = img_ends[region]
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


# sweep
def activity_sweep(self):
    times = preprocess_activity_sweep_times(self.config.activity_sweep_times)
    number = preprocess_activity_region(self.config.activity_sweep_task_number)
    self.logger.info("activity sweep task number : " + str(number))
    self.logger.info("activity sweep times : " + str(times))
    if len(times) == 0:
        return True
    self.to_main_page()
    to_activity(self, "mission", True)
    ap = self.get_ap()
    self.stage_data = get_stage_data(self)
    sweep_one_time_ap = self.stage_data["sweep_ap_cost_mission"]
    total_mission = len(self.stage_data["mission"])
    if len(times) == 1 and times[0] == -1:
        times = [int(ap / sum(sweep_one_time_ap[num] for num in number))] * len(number)
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
        to_mission_task_info(self, number[i], total_mission)
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


def start_sweep(self, skip_first_screenshot=False):
    img_ends = [
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"activity_task-info": (941, 411)}
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


# explore activity

def explore_activity_mission(self):
    self.stage_data = get_stage_data(self)
    total_mission = len(self.stage_data["mission"])
    self.to_main_page()
    to_activity(self, "mission", True)
    last_target_task = 1
    while self.flag_run:
        plot = to_mission_task_info(self, last_target_task, total_mission)
        res = check_sweep_availability(self, plot)
        while res == "sss" and last_target_task <= total_mission - 1:
            self.logger.info("Current mission sss check next mission")
            to_activity(self, "mission", True)
            last_target_task += 1
            plot = to_mission_task_info(self, last_target_task, total_mission)
            res = check_sweep_availability(self, plot)
        if last_target_task == total_mission and res == "sss":
            self.logger.info("All MISSION SSS")
            return True
        start_story(self)
        to_activity(self, "story", True)
        to_activity(self, "mission", True)


def to_mission_task_info(self, target_index, total_mission):
    possible_strs = build_activity_task_name_list(total_mission)
    ocr_region_offsets = {
        "CN": (-384, -8, 43, 28),
        "Global_en-us": (-384, 0, 43, 36),
        "Global_zh-tw": (-384, 0, 43, 36),
        "Global_ko-kr": (-384, 0, 43, 36),
        "JP": (-384, -8, 43, 28),
    }
    p = swipe_search_target_str(
        self,
        "activity_mission-enter-task-button",
        (1060, 143, 1195, 686),
        0.8,
        possible_strs,
        target_str_index=target_index - 1,
        swipe_params=(907, 432, 907, 156, 0.1, 0.5),
        ocr_language='en-us',
        ocr_region_offsets=ocr_region_offsets[self.identifier],
        ocr_str_replace_func=None,
        max_swipe_times=10,
        ocr_candidates="0123456789",
        first_retry_dir=1
    )
    y = p[1] + 10  # move down a little bit in case click to challenge page
    possibles = {'activity_menu': (1124, y)}
    ends = "activity_task-info"
    return picture.co_detect(self, None, None, ends, possibles, True)


def explore_activity_story(self):
    self.stage_data = get_stage_data(self)
    total_story = self.stage_data["total_story"]
    self.to_main_page()
    to_activity(self, "story", True)
    last_target_task = 1
    while self.flag_run:
        plot = to_story_task_info(self, last_target_task, total_story)
        res = check_sweep_availability(self, plot)
        while res == "sss" and last_target_task <= total_story - 1:
            self.logger.info("Current story sss check next story")
            to_activity(self, "story", True)
            last_target_task += 1
            plot = to_story_task_info(self, last_target_task, total_story)
            res = check_sweep_availability(self, plot)
        if last_target_task == total_story and res == "sss":
            self.logger.info("All STORY SSS")
            return True
        start_story(self)
        to_activity(self, "mission", True)
        to_activity(self, "story", True)


def to_challenge_task_info(self, number):
    lo = [0, 178, 279, 377, 477, 564]
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = [
        "activity_task-info",
        "normal_task_task-info",
        "normal_task_SUB"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def explore_activity_challenge(self):
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
            if not execute_grid_task(self, current_task_stage_data):
                self.logger.error(f"Skipping task due to error.")
                continue
            i += 1
        main_story.auto_fight(self)
        if self.config.manual_boss:
            self.click(1235, 41)
        to_activity(self, "mission", True)
        to_activity(self, "challenge", True)


def start_story(self):
    rgb_possibles = {
        "formation_edit2": (151, 387),
        "formation_edit3": (151, 387),
        "formation_edit4": (151, 387),
    }
    img_possibles = {
        "activity_task-info": (940, 538),
        "normal_task_task-info": (940, 538),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
        "main_story_episode-info": (629, 518),
        "story-fight-success-confirm": (1117, 639, 1219, 687)
    }
    rgb_ends = [
        "formation_edit1",
        "reward_acquired"
    ]
    img_ends = [
        "activity_unit-formation",
        "activity_formation",
        "activity_self-formation",
    ]
    res = picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
    if res in ["formation_edit1", "activity_unit-formation", "activity_formation", "activity_self-formation"]:
        start_fight(self, 1)
        main_story.auto_fight(self)
    elif res == "reward_acquired":
        pass
    return


def start_fight(self, i):
    rgb_possibles = {"formation_edit" + str(i): (1156, 659)}
    rgb_ends = ["fighting_feature"]
    img_ends = [
        "normal_task_fight-confirm",
        "normal_task_fail-confirm"
    ]
    img_possibles = {
        "activity_unit-formation": (1156, 659),
        "activity_self-formation": (1156, 659),
        "activity_formation": (1156, 659),
    }
    ret = picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
    if ret != "fighting_feature":
        self.logger.info("fight end.")
    return ret


def check_sweep_availability(self, plot):
    if plot == "activity_task-info":
        if compare_image(self, "activity_task-no-goals"):
            self.logger.info("Judge Task Without Goal")
            if not color.match_rgb_feature(self, "no-goal-task_passed"):
                return "sss"
            else:
                return "no-pass"
        else:
            return color.check_sweep_availability(self)
    elif plot == "main_story_episode-info":
        if not color.rgb_in_range(self, 362, 322, 232, 255, 219, 255, 0, 30):
            return "sss"
        else:
            return "no-pass"
    return "no-pass"


def build_activity_task_name_list(total_task):
    if total_task < 10:
        return ["0" + str(i) for i in range(1, total_task + 1)]
    else:
        ret = [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09"
        ]
        for i in range(10, total_task + 1):
            ret.append(str(i))
        return ret


def to_story_task_info(self, target_index, total_story):
    possible_strs = build_activity_task_name_list(total_story)
    p = swipe_search_target_str(
        self,
        "activity_story-enter-task-button",
        (1067, 149, 1195, 686),
        0.8,
        possible_strs,
        target_str_index=target_index - 1,
        swipe_params=(907, 432, 907, 156, 0.1, 0.5),
        ocr_language='en-us',
        ocr_region_offsets=(-387, -6, 50, 28),
        ocr_str_replace_func=None,
        max_swipe_times=10,
        ocr_candidates="0123456789"
    )
    y = p[1]
    img_possibles = {'activity_menu': (1124, y)}
    img_ends = [
        "activity_task-info",
        "main_story_episode-info"
    ]
    ret = picture.co_detect(self, None, None, img_ends, img_possibles, True)
    return ret


# exchange reward
def exchange_reward(self):
    to_activity(self, "story", True)
    to_exchange(self, True)
    to_set_exchange_times_menu(self, True)
    if not compare_image(self, "activity_exchange-50-times-at-once"):
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
    return self.ocr.recognize_int(self, region[self.server], "Activity Exchange Assets")


def preprocess_activity_region(region):
    if type(region) is int:
        return [region]
    if type(region) is str:
        region = region.split(",")
        for i in range(0, len(region)):
            region[i] = int(region[i])
        return region
    if type(region) is list:
        for i in range(0, len(region)):
            if type(region[i]) is int:
                continue
            region[i] = int(region[i])
        return region


def preprocess_activity_sweep_times(times):
    if type(times) is int:
        return [times]
    if type(times) is float:
        return [times]
    if type(times) is str:
        times = times.split(",")
        for i in range(0, len(times)):
            if '.' in times[i]:
                times[i] = min(float(times[i]), 1.0)
            elif '/' in times[i]:
                temp = times[i].split("/")
                times[i] = min(int(temp[0]) / int(temp[1]), 1.0)
            else:
                times[i] = int(times[i])
        return times
    if type(times) is list:
        for i in range(0, len(times)):
            if type(times[i]) is int:
                continue
            if '.' in times[i]:
                times[i] = min(float(times[i]), 1.0)
            elif '/' in times[i]:
                temp = times[i].split("/")
                times[i] = min(int(temp[0]) / int(temp[1]), 1.0)
        return times
