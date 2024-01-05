import time

from core import color, image
from core.color import check_sweep_availability


def read_task(self, task_string):
    try:
        region = 0
        mainline_available_missions = [1, 2, 3]
        mainline_available_regions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                                      23, ]
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
        self.logger.info("task string format error")
        return False


def implement(self):
    self.quick_method_to_main_page()
    self.hard_task_count = []
    temp = self.config['hardPriority']
    if type(temp) == str:
        temp = temp.split(',')
    for i in range(0, len(temp)):
        if read_task(self, temp[i]):
            self.hard_task_count.append(read_task(self, temp[i]))
    self.logger.info("detected hard task list: " + str(self.hard_task_count))
    all_task_x_coordinate = 1118
    if len(self.hard_task_count) != 0:
        hard_task_y_coordinates = [253, 364, 478]
        for i in range(0, len(self.hard_task_count)):
            to_hard_event(self, True)
            ap = self.get_ap()
            if ap == "UNKNOWN":
                self.logger.info("UNKNOWN AP")
                ap = 999
            self.logger.info("hard task " + str(self.hard_task_count[i]) + " begin")
            tar_region = self.hard_task_count[i][0]
            tar_mission = self.hard_task_count[i][1]
            tar_times = self.hard_task_count[i][2]
            if tar_times == "max":
                ap_needed = 60
            else:
                ap_needed = tar_times * 20
            self.logger.info("ap_needed : " + str(ap_needed))
            if ap_needed > ap:
                self.logger.info("INADEQUATE AP for task")
                return True
            choose_region(self, tar_region)
            if to_task_info(self, all_task_x_coordinate, hard_task_y_coordinates[tar_mission - 1]) == "unlock_notice":
                self.logger.info("task unlocked")
                continue
            t = check_sweep_availability(self.latest_img_array, server=self.server)
            if t == "sss":
                if tar_times == "max":
                    self.click(1085, 300, rate=1, wait=False, wait_over=True)
                else:
                    self.click(1014, 300, count=tar_times - 1, wait=False, wait_over=True)
                res = start_sweep(self, True)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info("hard task " + str(self.hard_task_count[i]) + " finished")
                elif res == "purchase_ap_notice":
                    self.logger.warning("INADEQUATE AP")
                    return True
                elif res == "charge_challenge_counts":
                    self.logger.warning("Current Task Challenge Counts INSUFFICIENT")
            elif t == "pass" or t == "no-pass":
                self.logger.warning("AUTO SWEEP UNAVAILABLE")

            to_hard_event(self, True)
        self.logger.info("hard task finished")

    return True


def get_area_number(self):
    t1 = time.time()
    img = self.latest_img_array[182:213, 121:164, :]
    ocr_result = self.ocrEN.ocr_for_single_line(img)
    print(ocr_result)
    t2 = time.time()
    print("time2", t2 - t1)
    print("cur_num", ocr_result["text"])
    self.logger.info("cur_num" + ocr_result["text"])
    return int(ocr_result["text"])


def to_hard_event(self, skip_first_screenshot=False):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (1198, 580),
            "main_page_bus": (823, 261),
            "normal_task_sweep-complete": (643, 585),
            "normal_task_start-sweep-notice": (887, 164),
            "normal_task_unlock-notice": (887, 164),
            "normal_task_task-info": (1087, 140),
            "normal_task_charge-challenge-counts": (887, 164),
            'normal_task_skip-sweep-complete': (643, 506),
            "buy_ap_notice": (919, 165),
            'normal_task_auto-over': (1082, 599),
            'normal_task_task-finish': (1038, 662),
            'normal_task_prize-confirm': (776, 655),
            'main_story_fight-confirm': (1168, 659),
        }
        click_pos = [
            [1064, 165],
            [640, 100]
        ]
        los = [
            "event_normal",
            'level_up'
        ]
        image.detect(self, end=None, possibles=possibles, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, ["event_hard"]), skip_first_screenshot=skip_first_screenshot)
    elif self.server == 'Global':
        click_pos = [
            [1077, 98],
            [1186, 165],
            [1198, 580],
            [823, 261],
            [640, 116],
            [1129, 142],
            [919, 168],
            [887, 164],
            [887, 161],
            [887, 161],

        ]
        los = [
            "sweep_complete",
            "event_normal",
            "main_page",
            "campaign",
            "reward_acquired",
            "mission_info",
            "purchase_ap_notice",
            "start_sweep_notice",
            "charge_challenge_counts",
            "unlock_notice",
        ]
        ends = [
            "event_hard",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot)


def to_task_info(self, x, y):
    if self.server == 'CN':
        possibles = {
            "normal_task_menu": (x, y, 3),
        }
        ends = [
            "normal_task_unlock-notice",
            "normal_task_task-info"
        ]
        res = image.detect(self, end=ends, possibles=possibles)
        if res == "normal_task_task-info":
            return "mission_info"
        else:
            return "unlock_notice"
    elif self.server == 'Global':
        click_pos = [
            [x, y],
        ]
        los = [
            "event_hard"
        ]
        ends = [
            "mission_info",
            "unlock_notice"
        ]
        return color.common_rgb_detect_method(self, click_pos, los, ends)


def start_sweep(self, skip_first_screenshot=False):
    if self.server == 'CN':
        possibles = {
            "normal_task_task-info": (941, 411),
        }
        ends = [
            "buy_ap_notice",
            "normal_task_charge-challenge-counts",
            "normal_task_start-sweep-notice",
        ]
        res = image.detect(self, end=ends, possibles=possibles, skip_first_screenshot=skip_first_screenshot)
        if res == "buy_ap_notice":
            return "purchase_ap_notice"
        elif res == "normal_task_charge-challenge-counts":
            return "charge_challenge_counts"
        possibles = {
            "normal_task_start-sweep-notice": (765, 501)
        }
        ends = [
            "normal_task_skip-sweep-complete",
            "normal_task_sweep-complete",
        ]
        res = image.detect(self, end=ends, possibles=possibles, pre_func=color.detect_rgb_one_time,
                           pre_argv=(self, [[640, 200]], ['level_up'], []), skip_first_screenshot=True)
        if res == "normal_task_sweep-complete":
            return "sweep_complete"
        elif res == "normal_task_skip-sweep-complete":
            return "skip_sweep_complete"

    elif self.server == 'Global':
        ends = [
            "purchase_ap_notice",
            "charge_challenge_counts",
            "start_sweep_notice",
        ]
        res = color.common_rgb_detect_method(self, [[941, 411]], ["mission_info"],
                                             ends, skip_first_screenshot=skip_first_screenshot)
        if res == "purchase_ap_notice" or res == "charge_challenge_counts":
            return res
        ends = [
            "skip_sweep_complete",
            "sweep_complete",
        ]
        return color.common_rgb_detect_method(self, [[765, 501]], ["start_sweep_notice"], ends, True)


def choose_region(self, region):
    cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, wait=False, count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360, wait=False, count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        self.latest_img_array = self.get_screenshot_array()
        cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])
