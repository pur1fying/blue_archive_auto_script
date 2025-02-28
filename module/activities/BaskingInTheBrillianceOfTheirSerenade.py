import time
from core import color, picture
from module import main_story
from module.activities.activity_utils import get_stage_data


def implement(self):
    times = preprocess_activity_sweep_times(self.config["activity_sweep_times"])
    region = preprocess_activity_region(self.config["activity_sweep_task_number"])
    self.logger.info("activity sweep task number : " + str(region))
    self.logger.info("activity sweep times : " + str(times))
    if len(times) > 0:
        sweep(self, region, times)
    return True

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

def sweep(self, number, times):
    self.quick_method_to_main_page()
    to_activity(self, "mission", True, True)
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
                    to_activity(self, "mission", True, True)
        elif res == "pass" or res == "no-pass":
            self.logger.warning("task not sss, sweep unavailable")
            continue
    return True

def explore_story(self):
    self.quick_method_to_main_page()
    to_activity(self, "story", True, True)
    # 现在能到这个断点了
    last_target_task = 1
    total_stories = 10
    while self.flag_run:
        plot = to_story_task_info(self, last_target_task)
        if plot == "normal_task_task-info" or plot == "activity_task-info":
            res = color.check_sweep_availability(self)
        elif plot == "main_story_episode-info":
            if not color.is_rgb_in_range(self, 362, 322, 232, 255, 219, 255, 0, 30):
                res = "sss"
            else:
                res = "no-pass"
        while res == "sss" and last_target_task <= total_stories - 1:
            self.logger.info("Current story sss check next story")
            self.click(1168, 353, duration=1, wait_over=True)
            last_target_task += 1
            plot = picture.co_detect(self, img_ends=["normal_task_task-info","activity_task-info", "main_story_episode-info"])
            if plot == "normal_task_task-info" or plot == "activity_task-info":
                res = color.check_sweep_availability(self)
            elif plot == "main_story_episode-info":
                if not color.is_rgb_in_range(self, 362, 322, 232, 255, 219, 255, 0, 30):
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
    res = picture.co_detect(self, rgb_ends, None, None, img_possibles, skip_loading=True)
    if res == "formation_edit1":
        start_fight(self, 1)
        main_story.auto_fight(self)
    elif res == "reward_acquired":
        pass
    return

def start_fight(self, i):
    rgb_possibles = {"formation_edit" + str(i): (1156, 659)}
    rgb_ends = ["fighting_feature"]
    picture.co_detect(self, rgb_ends, rgb_possibles, skip_loading=True)

def explore_mission(self):
    self.quick_method_to_main_page()
    to_activity(self, "mission", True, True)
    last_target_mission = 1
    total_missions = 12
    characteristic = [
        'burst1',
        'mystic1',
        'burst1',
        'mystic1',
        'burst1',
        'mystic1',
        'burst1',
        'mystic1',
        'burst1',
        'mystic1',
        'burst1',
        'mystic1',
    ]
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
        "activity_task-info": (task_info_x[self.server],141),
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
        'normal_task_mission-conclude-confirm': (1042, 671),
        "activity_exchange-confirm": (673, 603),
    }
    img_ends = "activity_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_loading=skip_first_screenshot)
    # 到上面一步是进到这个界面，检测的是左上角的event 但是之前国际服没有截图所以现在截一下，截图的四个坐标可以用mumu的这个看 左上右下 ,你可以适当调整截图范围让图片意思更明了，这里play-guide就小了
   #现在能到这个断点了

    if region is None:
        return True
    #这期没有challenge 所以这里坐标又要调整一下（这里我写的很粗糙，你不用理解是干嘛的，总之就是选择这两个（之前活动是三个））
    rgb_lo = {
        "story": 683,
        "mission": 952,
        "challenge": 1046,
    }
    click_lo = {
        "story": 937,
        "mission": 1199,
        "challenge": 1196,
    }
    while self.flag_run:
        if not color.is_rgb_in_range(self, rgb_lo[region], 131, 20, 60, 40, 80, 70, 116):
            self.click(click_lo[region], 87)
            time.sleep(self.screenshot_interval)
            self.latest_img_array = self.get_screenshot_array()
        else:
            if need_swipe:
                if region == "mission":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
                elif region == "story":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
            return True


def to_story_task_info(self, number):
    lo = [0, 180, 280, 380, 480, 580, 680, 348, 448, 548, 648]
    if number >= 7:
        self.swipe(916, 667, 916, 0, duration=0.05, post_sleep_time=0.7)
    img_possibles = {'activity_menu': (1124, lo[number])}
    img_ends = [
        "activity_task-info",
        "normal_task_task-info",
        "main_story_episode-info"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_mission_task_info(self, number):
    # 这里坐标要改,每次活动数量不一样,总之就是为了滑到第number个任务
    lo = [0, 184, 308, 422, 537]
    index = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]
    if number in [5, 6, 7, 8]:
        self.swipe(916, 581, 916, 111, duration=0.5, post_sleep_time=0.7)
    if number in [9, 10, 11, 12]:
        self.swipe(943, 581, 943, 0, duration=0.1, post_sleep_time=0.7)
        self.swipe(943, 581, 943, 0, duration=0.1, post_sleep_time=0.7)
    possibles = {'activity_menu': (1124, lo[index[number - 1]])}
    ends = ["normal_task_task-info", "activity_task-info"]
    return picture.co_detect(self, None, None, ends, possibles, True)

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


























