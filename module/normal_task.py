from copy import deepcopy
from core import picture, Baas_thread
from core.color import check_sweep_availability
from core.staticUtils import isInt


def implement(self):
    if len(self.config.unfinished_normal_tasks) != 0:
        temp = deepcopy(self.config.unfinished_normal_tasks)
        self.logger.info("unfinished normal task list: " + str(temp))
        self.to_main_page()
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
            one_time_ap = 10
            if tar_region == "tutorial":
                one_time_ap = 1
            if tar_times == "max":
                ap_needed = int(ap / one_time_ap) * one_time_ap
            else:
                ap_needed = tar_times * one_time_ap
            self.logger.info("ap_needed : " + str(ap_needed))
            if ap_needed > ap:
                self.logger.warning("INADEQUATE AP for task")
                return True
            if tar_region == "tutorial":
                tutorial_region = [0, 1, 1, 1, 2, 3, 3]
                to_region(self, tutorial_region[tar_mission], True)
                import importlib
                module_name = "module.mainline.tutorial" + str(tar_mission)
                module = importlib.import_module(module_name)
                module.sweep(self, tar_times)
                continue
            to_region(self, tar_region, True)
            self.swipe(917, 220, 917, 552, duration=0.1, post_sleep_time=1)
            if to_task_info(self, all_task_x_coordinate, normal_task_y_coordinates[tar_mission - 1]) == "unlock_notice":
                self.logger.warning("task unlocked")
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
                res = start_sweep(self, skip_first_screenshot=True)
                if res:
                    self.logger.info("common task " + str(temp[i]) + " finished")
                    if tar_times == "max":
                        return True
                else:
                    self.logger.info("Inadequate AP, Quit Sweep Normal Task")
                    return True
            elif t == "pass" or t == "no-pass":
                self.logger.info("AUTO SWEEP UNAVAILABLE")

            self.config.unfinished_normal_tasks.pop(0)
            self.config_set.set('unfinished_normal_tasks', self.config.unfinished_normal_tasks)

            to_normal_event(self, True)
        self.logger.info("common task finished")

    return True


def readOneNormalTask(task_string, region):
    if task_string.count('-') != 2:
        raise ValueError("[ " + task_string + " ] format error.")
    mainline_available_missions = list(range(1, 6))
    mainline_available_regions = list(range(5, region[1] + 1))
    mainline_available_regions.append("tutorial")
    temp = task_string.split('-')
    region = temp[0]
    mission = temp[1]
    counts = temp[2]
    if not isInt(region):
        if region != "tutorial":
            raise ValueError("[ " + task_string + " ] region : " + str(region) + " unavailable")
    else:
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


def to_normal_event(self: Baas_thread, skip_first_screenshot=False):
    rgb_ends = ['event_normal']
    rgb_reactions = {
        "event_hard": (805, 165),
        "main_page": (1198, 580),
        "level_up": (640, 200),
    }
    img_reactions = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (823, 261),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        "normal_task_unlock-notice": (887, 164),
        "normal_task_task-info": (1128, 130),
        'normal_task_skip-sweep-complete': (643, 506),
        "purchase_ap_notice-localized": (919, 165),
        "purchase_ap_notice": (919, 165),
        'normal_task_task-finish': (1038, 662),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fight-confirm': (1168, 659),
        'normal_task_fight-complete-confirm': (1160, 666),
        'normal_task_reward-acquired-confirm': (800, 660),
    }
    img_reactions.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, rgb_ends, rgb_reactions, None, img_reactions, skip_first_screenshot)


def to_hard_event(self, skip_first_screenshot=False):
    rgb_ends = ['event_hard']
    rgb_reactions = {
        "event_normal": (1064, 165),
        "main_page": (1198, 580),
        "level_up": (640, 200),
    }
    img_reactions = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (823, 261),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        "normal_task_unlock-notice": (887, 164),
        "normal_task_task-info": (1128, 130),
        'normal_task_skip-sweep-complete': (643, 506),
        "purchase_ap_notice": (919, 165),
        "purchase_ap_notice-localized": (919, 165),
        'normal_task_task-finish': (1038, 662),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fight-confirm': (1168, 659),
        'normal_task_fight-complete-confirm': (1160, 666),
        'normal_task_reward-acquired-confirm': (800, 660),
        'normal_task_charge-challenge-counts': (887, 161),
        "normal_task_task-A-info": (1128, 130)
    }
    img_reactions.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, rgb_ends, rgb_reactions, None, img_reactions, skip_first_screenshot)


def to_task_info(self, x, y):
    rgb_possibles = {"event_normal": (x, y)}
    img_ends = [
        "normal_task_unlock-notice",
        "normal_task_task-info"
    ]
    res = picture.co_detect(self, None, rgb_possibles, img_ends, None, True)
    if res == "normal_task_unlock-notice" or res == 'unlock_notice':
        return "unlock_notice"
    return True


def start_sweep(self, skip_first_screenshot=False):
    img_ends = [
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice-localized" or res == "purchase_ap_notice":
        return False
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
    return True


def to_region(self, region, isNormal: bool):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    curRegion = self.ocr.recognize_int(self, square[self.server], "Region Num")
    self.logger.info("Current Region : " + str(curRegion))
    while curRegion != region and self.flag_run:
        if curRegion > region:
            self.click(40, 360, count=curRegion - region, rate=0.1, wait_over=True, duration=0.5)
        else:
            self.click(1245, 360, count=region - curRegion, rate=0.1, wait_over=True, duration=0.5)
        # TODO 检测是否是未解锁区域
        if isNormal:
            to_normal_event(self)
        else:
            to_hard_event(self)
        curRegion = self.ocr.recognize_int(self, square[self.server], "Region Num")
        self.logger.info("Current Region : " + str(curRegion))
    return True
