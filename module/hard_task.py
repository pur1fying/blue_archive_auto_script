from copy import deepcopy

from core import picture
from core.color import check_sweep_availability
from core.staticUtils import isInt
from module.normal_task import to_region, to_hard_event


def implement(self):
    if len(self.config.unfinished_hard_tasks) != 0:
        temp = deepcopy(self.config.unfinished_hard_tasks)
        self.logger.info("unfinished hard task list: " + str(temp))
        self.to_main_page()
        all_task_x_coordinate = 1118
        hard_task_y_coordinates = [253, 364, 478]
        ap = self.get_ap(True)
        for i in range(0, len(temp)):
            to_hard_event(self, True)
            self.logger.info("Hard Task " + str(temp[i]) + " Begin")
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
            to_region(self, tar_region, False)
            if to_task_info(
                    self,
                    all_task_x_coordinate,
                    hard_task_y_coordinates[tar_mission - 1],
                    True) == "normal_task_unlock-notice":
                self.logger.info("task unlocked")
                continue
            t = check_sweep_availability(self, True)
            if t == "sss":
                y = 300
                if self.server == "JP" or self.server == "Global":
                    y = 328
                if tar_times == "max":
                    self.click(1085, y, rate=1, wait_over=True)
                else:
                    duration = 0
                    if tar_times > 4:
                        duration = 1
                    self.click(1014, y, count=tar_times - 1, duration=duration, wait_over=True)
                res = start_sweep(self, True)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info("Hard task " + str(temp) + " finished")
                elif res == "inadequate_ap":
                    self.logger.warning("Inadequate AP, Quit Sweep Hard Task")
                    return True
                elif res == "charge_challenge_counts":
                    self.logger.warning("Current Task Challenge Counts Insufficient")
            elif t == "pass" or t == "no-pass":
                self.logger.warning("Current Task [ " + str(tar_region) + str(tar_mission) + " ] Sweep Unavailable")
            self.config.unfinished_hard_tasks.pop(0)
            self.config_set.set('unfinished_hard_tasks', self.config.unfinished_hard_tasks)
            to_hard_event(self, True)
        self.logger.info("Hard task All Finished")
    return True





def to_task_info(self, x, y, skip_first_screenshot=False):
    rgb_possibles = {"event_hard": (x, y)}
    img_ends = [
        "normal_task_unlock-notice",
        "normal_task_task-info"
    ]
    return picture.co_detect(self, None, rgb_possibles, img_ends, None, skip_first_screenshot)


def readOneHardTask(task_string, region):
    if task_string.count('-') != 2:
        raise ValueError("[ " + task_string + " ] format error.")
    mainline_available_missions = list(range(1, 4))
    mainline_available_regions = list(range(region[0], region[1] + 1))
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
    img_ends = [
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
        "normal_task_charge-challenge-counts",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice-localized" or res == "purchase_ap_notice":
        return "inadequate_ap"
    if res == "normal_task_charge-challenge-counts":
        return "charge_challenge_counts"
    rgb_possibles = {"level_up": (640, 200)}
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    return "sweep_complete"
