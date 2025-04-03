import time

from core import color, picture
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
    drawCard(self)
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
                    to_activity(self, "mission", True, True)
        elif res == "pass" or res == "no-pass":
            self.logger.warning("task not sss, sweep unavailable")
            continue
    return True


def explore_story(self):
    self.to_main_page()
    to_activity(self, "story", True, True)
    last_target_task = 1
    total_stories = 6
    while self.flag_run:
        plot = to_story_task_info(self, last_target_task)
        if plot == "normal_task_task-info":
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
            plot = picture.co_detect(self, img_ends=["normal_task_task-info", "main_story_episode-info"])
            if plot == "normal_task_task-info":
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
    tasks = [
        "mission1_sss",
        "mission2_sss",
        "mission3_sss",
        "mission4_sss",
        "mission5_sss",
        "mission6_sss",
        "mission7_sss",
        "mission8_sss",
        "mission9_sss",
        "mission4_task",
        "mission5_task",
        "mission6_task",
        "mission7_task",
        "mission8_task",
        "mission9_task",
    ]
    stage_data = get_stage_data(self)
    for i in range(0, len(tasks)):
        current_task_stage_data = stage_data[tasks[i]]
        data = tasks[i].split("_")
        task_number = int(data[0].replace("mission", ""))
        to_mission_task_info(self, task_number)
        need_fight = False
        if "task" in data:
            need_fight = True
        elif "sss" in data:
            res = color.check_sweep_availability(self)
            if res == "sss":
                self.logger.info("mission " + str(task_number) + " sss no need to fight")
                to_activity(self, "mission", True, True)
                continue
            elif res == "no-pass" or res == "pass":
                need_fight = True
        if need_fight:
            self.logger.info("Start mission " + str(task_number) + " fight")

            if not execute_grid_task(self, current_task_stage_data):
                self.logger.error(f"Skipping task due to error.")
                continue

            main_story.auto_fight(self)
            if self.config.manual_boss:
                self.click(1235, 41)
            to_activity(self, "challenge", True)
            to_activity(self, "mission", True, True)


def explore_challenge(self):
    self.to_main_page()
    to_activity(self, "challenge", True, True)
    tp = [
        "fight",
        "grid",
        "grid",
        "fight",
    ]
    tasks = [
        "challenge1_burst1",
        "challenge2_sss",
        "challenge2_task",
        "challenge3_burst1",
    ]
    stage_data = get_stage_data(self)
    i = 0
    while self.flag_run and i < len(tasks):
        data = tasks[i].split("_")
        task_number = int(data[0].replace("challenge", ""))
        res = to_challenge_task_info(self, task_number)
        if res == "normal_task_SUB":
            self.logger.info("-- Start SUB fight --")
            to_formation_edit_i(self, 1, [1087, 141], True)
            start_fight(self, 1)
            main_story.auto_fight(self)
        elif res == "normal_task_task-info":
            if tp[i] == "grid":
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
            elif tp[i] == "fight":
                res = color.check_sweep_availability(self)
                if res == "sss":
                    self.logger.info("Challenge " + str(task_number) + " sss no need to fight")
                    to_activity(self, "challenge", True)
                    i += 1
                    continue
                formationID = self.config[data[1]]
                to_formation_edit_i(self, formationID, (949, 540), True)
                start_fight(self, formationID)
                main_story.auto_fight(self)
        to_activity(self, "mission", True)
        to_activity(self, "challenge", True, True)


def to_activity(self, region, skip_first_screenshot=False, need_swipe=False):
    task_info = {
        'CN': (1087, 141),
        'Global': (1128, 141),
        'JP': (1126, 115)
    }
    img_possibles = {
        "activity_enter1": (1196, 195),
        "activity_enter2": (100, 149),
        "activity_enter3": (218, 530),
        'activity_fight-success-confirm': (640, 663),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        'purchase_ap_notice': (919, 168),
        'purchase_ap_notice-localized': (919, 168),
        "plot_skip-plot-notice": (766, 520),
        "normal_task_help": (1017, 131),
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
                elif region == "story":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
                elif region == "challenge":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
            return True


def to_story_task_info(self, number):
    lo = [0, 180, 280, 380, 480, 580]
    index = [0, 1, 2, 3, 4, 5, 6]
    img_possibles = {'activity_menu': (1124, lo[index[number]])}
    img_ends = [
        "normal_task_task-info",
        "main_story_episode-info"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_mission_task_info(self, number):
    lo = [0, 184, 300, 416, 527, 644]
    index = [0, 1, 2, 3, 4, 5, 2, 3, 4, 5]
    if number >= 6:
        self.swipe(943, 593, 943, 0, duration=0.05, post_sleep_time=1)
    img_possibles = {'activity_menu': (1124, lo[index[number]])}
    img_ends = "normal_task_task-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_challenge_task_info(self, number):
    lo = [0, 178, 279, 377, 477, 564]
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = [
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


def drawCard(self):
    to_activity(self, "mission", True)
    toCardStore(self)
    region = {
        'CN': (708, 168, 781, 201)
    }
    coin = self.ocr.recognize_number(self.latest_img_array, region[self.server], int, self.ratio)
    drawCnt = int(coin / 200)
    for i in range(0, drawCnt):
        reshuffleCard(self)
        chooseCardFourOfFour(self)
        res = drawCardFourOfFour(self)
        if res == "activity_draw-card-grey":
            self.logger.warning("inadequate coin")
            return
    return


def toCardStore(self):
    img_possibles = {
        "activity_menu": (517, 647),
    }
    img_ends = "activity_card-store"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def chooseCardFourOfFour(self):
    img_possibles = {
        "activity_card-one-of-four-chosen": (1166, 412, 0.9, 5),
        "activity_card-two-of-four-chosen": (1166, 412, 0.9, 5),
        "activity_card-three-of-four-chosen": (1166, 412, 0.9, 5),
    }
    img_ends = ("activity_card-four-of-four-chosen", 0.9, 5)
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def reshuffleCard(self):
    img_possibles = {
        "activity_reshuffle-card-bright": (811, 579),
    }
    img_ends = [
        "activity_card-four-of-four-not-drew",
        "activity_reshuffle-card-grey",
    ]
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def drawCardFourOfFour(self):
    img_possibles = {
        "activity_draw-card-bright": (1042, 593),
    }
    rgb_ends = "reward_acquired"
    img_ends = "activity_draw-card-grey"
    res = picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, True)
    if res == "activity_draw-card-grey":
        return "activity_draw-card-grey"
    rgb_possibles = {
        "reward_acquired": (640, 100),
    }
    img_ends = "activity_card-store"
    return picture.co_detect(self, None, rgb_possibles, img_ends, None, True)
