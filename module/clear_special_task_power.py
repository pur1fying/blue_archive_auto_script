import time

from core import color, image, picture
from gui.util import log


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
        if count[i] == "max" or count[i] > 0:
            self.logger.info("Start commissions task: " + commissions_name[i] + " count : " + str(count[i]))
            if just_do_task:
                self.quick_method_to_main_page()
            just_do_task = True
            to_commissions(self, i + 1, skip_first_screenshot=True)
            res = commissions_common_operation(self, i + 1, count[i])
            self.logger.info("Finish commissions task: " + commissions_name[i])
            if res == "sweep_complete":
                self.commissions_status[i] = True
                if count[i] == "max":
                    return True
            elif res == "inadequate_ap":
                self.logger.warning("INADEQUATE AP")
                return True
            elif res == "0SWEEPABLE":
                self.logger.warning("0 SWEEPABLE COMMISSIONS")
    self.logger.info("COMMISSIONS STATUS: " + str(self.commissions_status))
    return True


def start_sweep(self, skip_first_screenshot=False):
    img_ends = [
        "puechase_ap_notice",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"special_task_task-info": (941, 411)}
    res = picture.co_detect(self, None,None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice" or res == "buy_ap_notice":
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


def to_commissions(self, num, skip_first_screenshot=False):
    commissions_y = {
        'CN': [0, 277, 406],
        'Global': [0, 206, 309],
        'JP': [0, 206, 309]
    }
    select_commissions_y = {
        'CN': 581,
        'Global': 515,
        'JP': 515
    }
    rgb_ends = "commissions"
    rgb_possibles = {
        "main_page":(1198, 580),
        "campaign":(746, select_commissions_y[self.server]),
        "choose_commissions":(992, commissions_y[self.server][num]),
        "reward_acquired":(640, 116),
        "mission_info":(1129, 142),
        "start_sweep_notice":(886, 164),
        "skip_sweep_complete":(649, 508),
    }
    img_ends = 'special_task_level-list'
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (724, select_commissions_y[self.server]),
        "special_task_request-select": (992, commissions_y[self.server][num]),
        "special_task_task-info": (1085, 141),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def one_detect(self,a,b):
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
        rgb_possibles = {"commissions":(1118, los[i])}
        rgb_ends = "mission_info"
        img_possibles = {"special_task_level-list": (1118, los[i])}
        img_ends = "special_task_task-info"
        picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
        t = color.check_sweep_availability(self.latest_img_array, server=self.server)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, duration=1, wait_over=True)
            else:
                if b > 1:
                    duration = 0
                    if b > 4:
                        duration = 1
                    self.click(1014, 300, count=b - 1, duration=duration, wait_over=True)
            return start_sweep(self, skip_first_screenshot=True)
        elif t == "no-pass" or t == "pass":
            to_commissions(self, a, skip_first_screenshot=True)

    return "0SWEEPABLE"


def commissions_common_operation(self, a, b):
    res = one_detect(self,a,b)
    if res != "0SWEEPABLE":
        return res
    self.swipe(926, 140, 926, 640, duration=1)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    res = one_detect(self,a,b)
    if res != "0SWEEPABLE":
        return res
    self.swipe(926, 188, 926, 381, duration=1)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    return one_detect(self,a,b)
