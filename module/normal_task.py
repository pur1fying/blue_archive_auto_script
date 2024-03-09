import time
from core import picture
from core.color import check_sweep_availability
from copy import deepcopy


def implement(self):
    if len(self.config['unfinished_normal_tasks']) != 0:
        temp = deepcopy(self.config['unfinished_normal_tasks'])
        self.logger.info("unfinished normal task list: " + str(temp))
        self.quick_method_to_main_page()
        all_task_x_coordinate = 1118
        normal_task_y_coordinates = [242, 341, 439, 537, 611]
        for i in range(0, len(temp)):
            to_normal_event(self, True)
            ap = self.get_ap()
            if ap == "UNKNOWN":
                self.logger.info("UNKNOWN AP")
                ap = 999
            self.logger.info("normal task " + str(temp[i]) + " begin")
            tar_region = temp[i][0]
            tar_mission = temp[i][1]
            tar_times = temp[i][2]
            if tar_times == "max":
                ap_needed = int(ap / 10) * 10
            else:
                ap_needed = tar_times * 10
            self.logger.info("ap_needed : " + str(ap_needed))
            if ap_needed > ap:
                self.logger.warning("INADEQUATE AP for task")
                return True
            choose_region(self, tar_region)
            self.swipe(917, 220, 917, 552, duration=0.1, post_sleep_time=1)
            if to_task_info(self, all_task_x_coordinate, normal_task_y_coordinates[tar_mission - 1]) == "unlock_notice":
                self.logger.warning("task unlocked")
                continue
            t = check_sweep_availability(self)
            if t == "sss":
                if tar_times == "max":
                    self.click(1085, 300, rate=1,  wait_over=True)
                else:
                    if tar_times > 1:
                        duration = 0
                        if tar_times > 4:
                            duration = 1
                        self.click(1014, 300, count=tar_times - 1,  duration=duration, wait_over=True)
                res = start_sweep(self, skip_first_screenshot=True)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info("common task " + str(temp[i]) + " finished")
                    if tar_times == "max":
                        return True
                elif res == "purchase_ap_notice":
                    self.logger.info("INADEQUATE AP")
                    return True
            elif t == "pass" or t == "no-pass":
                self.logger.info("AUTO SWEEP UNAVAILABLE")

            self.config['unfinished_normal_tasks'].pop(0)
            self.config_set.set('unfinished_normal_tasks', self.config['unfinished_normal_tasks'])

            to_normal_event(self, True)
        self.logger.info("common task finished")

    return True


def read_task(self, task_string):
    try:
        region = 0
        mainline_available_missions = [1, 2, 3, 4, 5]
        mainline_available_regions = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        for i in range(0, len(task_string)):
            if task_string[i].isdigit():
                region = region * 10 + int(task_string[i])
            else:
                if region not in mainline_available_regions:
                    self.logger.info("detected region " + str(region) + " unavailable")
                    return False
                mission = 0
                for j in range(i, len(task_string)):
                    if task_string[j].isdigit():
                        mission = int(task_string[j])
                        if mission not in mainline_available_missions:
                            self.logger.info("detected mission " + str(mission) + " unavailable")
                            return False
                        else:
                            counts = task_string[j + 2:]
                            if counts == "max":
                                return region, mission, "max"
                            else:
                                if int(counts) <= 0:
                                    self.logger.info("detected counts " + str(counts) + " unavailable")
                                    return False
                                return region, mission, int(counts)

                if mission == 0:
                    self.logger.info("no mission detected")
                    return False
    except Exception as e:
        self.logger.info("task string format error")
        return False

def to_normal_event(self, skip_first_screenshot=False):
    task_info_x = {
        'CN': 1087,
        'Global': 1128,
        'JP': 1128
    }
    rgb_ends = 'event_normal'
    rgb_possibles = {
        "sweep_complete":(1077, 98),
        "event_hard": (805, 165),
        "main_page": (1198, 580),
        "campaign": (823, 261),
        "mission_info": (task_info_x[self.server], 142),
        "purchase_ap_notice": (919, 168),
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
    }
    picture.co_detect(self, rgb_ends, rgb_possibles,None, img_possibles, skip_first_screenshot)


def to_task_info(self, x, y):
    rgb_ends = [
        "mission_info",
        "unlock_notice"
    ]
    rgb_possibles = {"event_normal": (x, y)}
    img_possibles = {
        "normal_task_select-area": (x, y),
    }
    img_ends = [
        "normal_task_unlock-notice",
        "normal_task_task-info"
    ]
    res = picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles)
    if res == "normal_task_unlock-notice" or res == 'unlock_notice':
        return "unlock_notice"
    return True


def start_sweep(self, skip_first_screenshot=False):
    rgb_ends = [
        "purchase_ap_notice",
        "start_sweep_notice",
    ]
    img_ends = [
        "purchase_ap_notice",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice" or res == "buy_ap_notice":
        return "inadequate_ap"
    rgb_ends = [
        "skip_sweep_complete",
        "sweep_complete"
    ]
    rgb_possibles = {"level_up": (640, 200)}
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, True)
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
            self.click(40, 360,  count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360,  count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        to_normal_event(self)
        cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
