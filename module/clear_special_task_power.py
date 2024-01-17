import time

from core import color, image, picture
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
            if just_do_task:
                to_request_select(self, True)
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

    img_ends = [
        "purchase_ap_notice",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"special_task_task-info": (941, 411)}
    res = picture.co_detect(self, None,None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice":
        return "inadequate_ap"
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, None,None, img_ends, img_possibles, skip_first_screenshot)
    return "sweep_complete"


def commissions_common_operation(self, a, b):
    res = one_detect(self, a, b)
    self.swipe(926, 188, 926, 381, duration=1)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    return one_detect(self,a,b)


def to_request_select(self, skip_first_screenshot=False):
    task_info_cross_x = {
        'CN': 1085,
        'JP': 1129,
        'Global': 1129
    }
    img_ends = "special_task_request-select"
    img_possibles = {
        'special_task_level-list': (57, 41),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_skip-sweep-complete": (643, 471),
        "special_task_task-info": (task_info_cross_x[self.server], 141),
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (731, 431),
    }
    rgb_possibles = {"main_page": (1198, 580)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles,
                      skip_first_screenshot=skip_first_screenshot)
