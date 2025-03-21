import time

from core import color, picture


def implement(self):
    count = get_task_count(self, "special_task", 2)
    if not count:
        return True

    self.to_main_page()
    commissions_name = ["BASE DEFENSE", "ITEM RETRIEVAL"]
    self.commissions_status = [False, False]
    just_do_task = False

    for i in range(0, 2):
        if count[i] == "max" or count[i] > 0:
            self.logger.info("Start commissions task: " + commissions_name[i] + " count : " + str(count[i]))
            if just_do_task:
                self.to_main_page()
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
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"special_task_task-info": (941, 411)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice-localized" or res == "purchase_ap_notice":
        return "inadequate_ap"
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    rgb_possibles = {"level_up": (640, 200)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    return "sweep_complete"


def to_commissions(self, num, skip_first_screenshot=False):
    commissions_y = [0, 206, 309]
    img_ends = 'special_task_level-list'
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (724, 515),
        "special_task_request-select": (992, commissions_y[num]),
        "special_task_task-info": (1129, 141),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def get_los(self):
    i = 675
    los = []
    while i > 196:
        if color.rgb_in_range(self, 1076, i, 131, 151, 218, 238, 245, 255) and \
            color.rgb_in_range(self, 1076, i - 30, 131, 151, 218, 238, 245, 255):
            los.append(i - 35)
            i -= 100
            continue
        else:
            i -= 1
    return los


def one_detect(self, a, b):
    los = get_los(self)
    if len(los) == 0:
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()
        los = get_los(self)
    for i in range(0, len(los)):
        img_possibles = {"special_task_level-list": (1118, los[i])}
        img_ends = "special_task_task-info"
        picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)
        t = color.check_sweep_availability(self)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, wait_over=True)
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
    res = one_detect(self, a, b)
    if res != "0SWEEPABLE":
        return res
    self.swipe(926, 140, 926, 640, duration=1, post_sleep_time=1)
    self.latest_img_array = self.get_screenshot_array()
    res = one_detect(self, a, b)
    if res != "0SWEEPABLE":
        return res
    self.swipe(926, 188, 926, 381, duration=1, post_sleep_time=1)
    self.latest_img_array = self.get_screenshot_array()
    return one_detect(self, a, b)


def get_task_count(self, task_name, expected_len):
    try:
        count = self.config_set.get(task_name+"_times")
        if type(count) is str:
            count = count.split(',')
        if len(count) < expected_len:
            self.logger.warning(task_name + " Config Length Error.")
            self.logger.warning("Expected: " + str(expected_len))
            self.logger.warning("Actual  : " + str(len(count)))
            return False
        for i in range(0, len(count)):
            if count[i] == "max":
                continue
            count[i] = int(count[i])
        self.logger.info(task_name + " Sweep Times: " + str(count))
        return count
    except Exception as e:
        self.logger.error("special task config error")
        self.logger.error(e.__str__())
        return False
