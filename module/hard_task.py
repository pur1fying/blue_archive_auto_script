import time
from copy import deepcopy
from core import picture
from core.color import check_sweep_availability
from core.staticUtils import isInt


def implement(self):
    if len(self.config['unfinished_hard_tasks']) != 0:
        temp = deepcopy(self.config['unfinished_hard_tasks'])
        self.logger.info("unfinished hard task list: " + str(temp))
        self.quick_method_to_main_page()
        all_task_x_coordinate = 1118
        hard_task_y_coordinates = [253, 364, 478]
        for i in range(0, len(temp)):
            to_hard_event(self, True)
            ap = self.get_ap()
            if ap == "UNKNOWN":
                self.logger.info("UNKNOWN AP")
                ap = 999
            self.logger.info("hard task " + str(temp[i]) + " begin")
            tar_region = temp[i][0]
            tar_mission = temp[i][1]
            tar_times = temp[i][2]
            if tar_times == "max":
                ap_needed = 60
            else:
                ap_needed = tar_times * 20
            self.logger.info("ap_needed : " + str(ap_needed))
            if ap_needed > ap:
                self.logger.info("INADEQUATE AP for task")
                return True
            choose_region(self, tar_region)
            if to_task_info(self, all_task_x_coordinate, hard_task_y_coordinates[tar_mission - 1],
                            True) == "normal_task_unlock-notice":
                self.logger.info("task unlocked")
                continue
            t = check_sweep_availability(self)
            if t == "sss":
                if tar_times == "max":
                    self.click(1085, 300, rate=1, wait_over=True)
                else:
                    duration = 0
                    if tar_times > 4:
                        duration = 1
                    self.click(1014, 300, count=tar_times - 1, duration=duration, wait_over=True)
                res = start_sweep(self, True)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info("hard task " + str(temp) + " finished")
                elif res == "inadequate_ap":
                    self.logger.warning("INADEQUATE AP")
                    return True
                elif res == "charge_challenge_counts":
                    self.logger.warning("Current Task Challenge Counts INSUFFICIENT")
            elif t == "pass" or t == "no-pass":
                self.logger.warning("AUTO SWEEP UNAVAILABLE")
            self.config['unfinished_hard_tasks'].pop(0)
            self.config_set.set('unfinished_hard_tasks', self.config['unfinished_hard_tasks'])
            to_hard_event(self, True)
        self.logger.info("hard task finished")
    return True

def to_hard_event(self, skip_first_screenshot=False):
    task_info_x = {
        'CN': 1087,
        'Global': 1128,
        'JP': 1128
    }
    rgb_ends = 'event_hard'
    rgb_possibles = {
        "sweep_complete": (1077, 98),
        "event_normal": (1064, 165),
        "main_page": (1198, 580),
        "start_sweep_notice": (887, 164),
        "charge_challenge_counts": (887, 161),
        "unlock_notice": (887, 161),
        "level_up": (640, 200),
    }
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (823, 261),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        "normal_task_unlock-notice": (887, 164),
        "normal_task_task-info": (task_info_x[self.server], 140),
        'normal_task_skip-sweep-complete': (643, 506),
        "buy_ap_notice": (919, 165),
        'normal_task_task-finish': (1038, 662),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fight-confirm': (1168, 659),
        'normal_task_fight-complete-confirm': (1160, 666),
        'normal_task_reward-acquired-confirm': (800, 660),
        'normal_task_mission-conclude-confirm': (1042, 671),
        'normal_task_charge-challenge-counts': (887, 161),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def to_task_info(self, x, y, skip_first_screenshot=False):
    rgb_possibles = {"event_hard": (x, y)}
    img_ends = [
        "normal_task_unlock-notice",
        "normal_task_task-info"
    ]
    return picture.co_detect(self, None, rgb_possibles, img_ends, None, skip_first_screenshot)

def readOneHardTask(task_string):
    if task_string.count('-') != 2:
        raise ValueError("[ " + task_string + " ] format error.")
    mainline_available_missions = list(range(1, 4))
    mainline_available_regions = list(range(1, 26))
    temp = task_string.split('-')
    region = temp[0]
    mission = temp[1]
    counts = temp[2]
    if not isInt(region):
        raise ValueError("[ " + task_string + " ] region : " + str(region) + " unavailable")
    region = int(region)
    if region not in mainline_available_regions:
        raise ValueError("[ " + task_string + " ] region : " + str(region) + " not support")
    if not isInt(mission):
        raise ValueError("[ " + task_string + " ] mission : " + str(mission) + " unavailable")
    mission = int(mission)
    if mission not in mainline_available_missions:
        raise ValueError("[ " + task_string + " ] mission : " + str(mission) + " not support")
    if not isInt(counts):
        if counts != "max":
            raise ValueError("[ " + task_string + " ] count : " + str(counts) + " unavailable")
    else:
        counts = int(counts)
    return region, mission, counts


def start_sweep(self, skip_first_screenshot=False):
    rgb_ends = [
        "purchase_ap_notice",
        "start_sweep_notice",
        "charge_challenge_counts"
    ]
    img_ends = [
        "purchase_ap_notice",
        "normal_task_start-sweep-notice",
        "normal_task_charge-challenge-counts",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice":
        return "inadequate_ap"
    if res == "normal_task_charge-challenge-counts":
        return "charge_challenge_counts"
    rgb_possibles = {"level_up": (640, 200)}
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    return "sweep_complete"


def choose_region(self, region):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360, count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        to_hard_event(self)
        cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
