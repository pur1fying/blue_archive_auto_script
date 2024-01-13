import time

from core import color, image
from gui.util import log

x = {
    'request-select': (658, 141, 935, 186),
    'level-list': (887, 98, 979, 123),
    'task-info': (578, 124, 702, 153),
}


def implement(self):
    self.quick_method_to_main_page()
    try:
        count = self.config["special_task_times"].split(",")
        for i in range(0, len(count)):
            if count[i] == "max":
                continue
            count[i] = int(count[i])
    except Exception as e:
        log.logger.error("special_task_times config error")
        log.logger.error(e)
        return True

    commissions_name = ["BASE DEFENSE", "ITEM RETRIEVAL"]
    self.commissions_status = [False, False]
    just_do_task = False

    for i in range(0, 2):
        if just_do_task:
            self.quick_method_to_main_page()
        if count[i] == "max" or count[i] > 0:
            self.logger.info("Start commissions task: " + commissions_name[i] + " count : " + str(count[i]))
            just_do_task = True
            to_commissions(self, i + 1, skip_first_screenshot=True)
            res = commissions_common_operation(self, i + 1, count[i])
            self.logger.info("Finish commissions task: " + commissions_name[i])
            if res == "sweep_complete" or res == "skip_sweep_complete":
                self.commissions_status[i] = True
                if count[i] == "max":
                    return True
            elif res == "purchase_ap_notice":
                self.logger.warning("INADEQUATE AP")
                return True
    self.logger.info("COMMISSIONS STATUS: " + str(self.commissions_status))
    return True


def start_sweep(self, skip_first_screenshot=False):
    if self.server == 'CN':
        possibles = {
            "special_task_task-info": (941, 411),
        }
        ends = [
            "buy_ap_notice",
            "normal_task_start-sweep-notice",
        ]
        res = image.detect(self, end=ends, possibles=possibles, skip_first_screenshot=skip_first_screenshot)
        if res == "buy_ap_notice":
            return "purchase_ap_notice"
        possibles = {
            "normal_task_start-sweep-notice": (765, 501)
        }
        ends = [
            "normal_task_skip-sweep-complete",
            "normal_task_sweep-complete",
        ]
        res = image.detect(self, end=ends, possibles=possibles, skip_first_screenshot=True,
                           pre_func=color.detect_rgb_one_time, pre_argv=(self, [[640, 200]], ['level_up'], []))
        if res == "normal_task_sweep-complete":
            return "sweep_complete"
        elif res == "normal_task_skip-sweep-complete":
            return "skip_sweep_complete"

    elif self.server == 'Global':
        ends = [
            "purchase_ap_notice",
            "start_sweep_notice",
        ]
        res = color.common_rgb_detect_method(self, [[941, 411]], ["mission_info"],
                                       ends, skip_first_screenshot=skip_first_screenshot)
        if res == "purchase_ap_notice":
            return res
        ends = [
            "skip_sweep_complete",
            "sweep_complete",
        ]
        return color.common_rgb_detect_method(self, [[765, 501]], ["start_sweep_notice"], ends, True)


def to_commissions(self, num, skip_first_screenshot=False):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (1198, 580),
            "main_page_bus": (724, 581),
            "special_task_request-select": (992, 0),
            "special_task_task-info": (1085, 141),
        }
        if num == 1:
            possibles["special_task_request-select"] = (992, 277)
        elif num == 2:
            possibles["special_task_request-select"] = (992, 406)
        image.detect(self, 'special_task_level-list', possibles, skip_first_screenshot=skip_first_screenshot)

    elif self.server == 'Global':
        click_pos = [
            [1198, 580],
            [746, 515],
            [992, 206],
            [640, 116],
            [1129, 142],
            [886, 164],
            [649, 508],

        ]
        if num == 1:
            click_pos[2][1] = 206
        elif num == 2:
            click_pos[2][1] = 309
        los = [
            "main_page",
            "campaign",
            "choose_commissions",
            "reward_acquired",
            "mission_info",
            "start_sweep_notice",
            "skip_sweep_complete",
        ]
        ends = [
            "commissions",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot=skip_first_screenshot)


def commissions_common_operation(self, a, b):
    click_pos = [
        [1118, 0]
    ]
    pd_los = [
        "commissions"
    ]
    ends = [
        "mission_info",
    ]
    possibles = {
        "special_task_level-list": (1118, 0)
    }
    i = 675
    line = self.latest_img_array[:, 1076, :]
    los = []
    while i > 196:
        if 131 <= line[i][2] <= 151 and 218 <= line[i][1] <= 238 and 245 <= line[i][0] <= 255 and \
            131 <= line[i - 30][2] <= 151 and 218 <= line[i - 30][1] <= 238 and 245 <= line[i - 30][0] <= 255:
            los.append(i - 35)
            i -= 100
        else:
            i -= 1
    for i in range(0, len(los)):
        if self.server == 'CN':
            possibles["special_task_level-list"] = (1118, los[i])
            image.detect(self, 'special_task_task-info', possibles)
        elif self.server == 'Global':
            click_pos[0][1] = los[i]
            color.common_rgb_detect_method(self, click_pos, pd_los, ends)
        t = color.check_sweep_availability(self.latest_img_array, server=self.server)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, duration=1, wait_over=True)
            else:
                self.click(1014, 300, count=b - 1, duration=1, wait_over=True)
            return start_sweep(self, skip_first_screenshot=True)
        elif t == "no-pass" or t == "pass":
            to_commissions(self, a, skip_first_screenshot=True)

    self.swipe(926, 140, 926, 640, duration=1)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    i = 675
    line = self.latest_img_array[:, 1076, :]
    los = []
    while i > 196:
        if 131 <= line[i][2] <= 151 and 218 <= line[i][1] <= 238 and 245 <= line[i][0] <= 255 and \
            131 <= line[i - 30][2] <= 151 and 218 <= line[i - 30][1] <= 238 and 245 <= line[i - 30][0] <= 255:
            los.append(i - 35)
            i -= 100
        else:
            i -= 1
    for i in range(0, len(los)):
        if self.server == 'CN':
            possibles["special_task_level-list"] = (1118, los[i])
            image.detect(self, 'special_task_task-info', possibles, skip_first_screenshot=True)
        elif self.server == 'Global':
            click_pos[0][1] = los[i]
            color.common_rgb_detect_method(self, click_pos, pd_los, ends, skip_first_screenshot=True)
        t = color.check_sweep_availability(self.latest_img_array, server=self.server)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, duration=1, wait_over=True)
            else:
                self.click(1014, 300, count=b - 1, duration=1, wait_over=True)
            return start_sweep(self, skip_first_screenshot=True)
        elif t == "no-pass" or t == "pass":
            to_commissions(self, a, skip_first_screenshot=True)

    self.swipe(926, 188, 926, 381, duration=1)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    line = self.latest_img_array[:, 1076, :]
    i = 675
    los = []
    while i > 196:
        if 131 <= line[i][2] <= 151 and 218 <= line[i][1] <= 238 and 245 <= line[i][0] <= 255 and \
            131 <= line[i - 30][2] <= 151 and 218 <= line[i - 30][1] <= 238 and 245 <= line[i - 30][0] <= 255:
            los.append(i - 35)
            i -= 100
        else:
            i -= 1
    for i in range(0, len(los)):
        if self.server == 'CN':
            possibles["special_task_level-list"] = (1118, los[i])
            image.detect(self, 'special_task_task-info', possibles, skip_first_screenshot=True)
        elif self.server == 'Global':
            click_pos[0][1] = los[i]
            color.common_rgb_detect_method(self, click_pos, pd_los, ends, skip_first_screenshot=True)
        t = color.check_sweep_availability(self.latest_img_array, server=self.server)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, duration=1, wait_over=True)
            else:
                self.click(1014, 300, count=b - 1, duration=1, wait_over=True)
            return start_sweep(self, skip_first_screenshot=True)
        elif t == "no-pass" or t == "pass":
            to_commissions(self, a, skip_first_screenshot=True)
    return True
