import time
from copy import deepcopy
from core import picture
from core.color import check_sweep_availability


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


def read_task(self, task_string):
    try:
        region = 0
        mainline_available_missions = [1, 2, 3]
        mainline_available_regions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                                      23, 24, 25]
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
                                return region, mission, min(3, int(counts))

                if mission == 0:
                    self.logger.info("no mission detected")
                    return False
    except Exception as e:
        self.logger.info("task string format error " + str(e))
        return False

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
