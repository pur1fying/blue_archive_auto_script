import time

from core import color, picture
from module.clear_special_task_power import get_task_count


def implement(self):
    count = get_task_count(self, "rewarded_task", 3)
    if not count:
        return True

    self.to_main_page()
    buy_ticket_times = max(0, self.config.purchase_rewarded_task_ticket_times)
    buy_ticket_times = min(buy_ticket_times, 12)
    if buy_ticket_times > 0:
        to_choose_bounty(self, True)
        purchase_bounty_ticket(self, buy_ticket_times)

    bounty_name = ["OVERPASS", "DESSERT RAILWAY", "CLASSROOM"]
    self.rewarded_task_status = [False, False, False]
    just_do_task = False

    for i in range(0, 3):
        if just_do_task:
            to_choose_bounty(self, True)
        if count[i] == "max" or count[i] > 0:
            self.logger.info("Start bounty task: " + bounty_name[i] + " count : " + str(count[i]))
            just_do_task = True
            to_bounty(self, i + 1, True)
            res = bounty_common_operation(self, i + 1, count[i])
            self.logger.info("Finish bounty task: " + bounty_name[i])
            if res == "sweep_complete":
                self.rewarded_task_status[i] = True
                if count[i] == "max":
                    return True
            elif res == "inadequate_ticket":
                self.logger.warning("INADEQUATE TICKET")
                self.logger.info("Rewarded task status : " + self.rewarded_task_status.__str__())
                return True
            elif res == "0SWEEPABLE":
                self.logger.warning("0 SWEEPABLE")

    self.logger.info("Rewarded Task Status : " + self.rewarded_task_status.__str__())
    get_bounty_coin(self)
    return True


def get_bounty_coin(self):
    to_bounty(self, 1, True)
    region = (148, 581, 376, 614)
    ocr_res = self.ocr.get_region_res(
        self,
        region,
        "en-us",
        "Bounty Coin",
        "0123456789,",
        0.2
    )
    ret = 0
    for j in range(0, len(ocr_res)):
        if not ocr_res[j].isdigit():
            continue
        ret = ret * 10 + int(ocr_res[j])
    data = {
        "count": ocr_res,
        "time": time.time()
    }
    self.config_set.set("bounty_coin", data)
    return


def start_sweep(self):
    img_ends = [
        "rewarded_task_purchase-bounty-ticket-menu",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {
        "rewarded_task_task-info": (941, 411),
    }
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)
    if res == "rewarded_task_purchase-bounty-ticket-menu":
        return "inadequate_ticket"
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    rgb_possibles = {"start_sweep_notice": (765, 501)}
    rgb_ends = [
        "skip_sweep_complete",
        "sweep_complete",
    ]
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
    return "sweep_complete"


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
        rgb_ends = ["mission_info"]
        rgb_possibles = {"bounty": (1118, los[i])}
        img_ends = ["rewarded_task_task-info"]
        img_possibles = {"rewarded_task_level-list": (1118, los[i])}
        picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
        t = color.check_sweep_availability(self)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, duration=1, wait_over=True)
            else:
                if b > 1:
                    duration = 0
                    if b > 4:
                        duration = 1
                    self.click(1014, 300, count=b - 1, duration=duration, wait_over=True)
            return start_sweep(self)
        elif t == "no-pass" or t == "pass":
            to_bounty(self, a, True)
    return "0SWEEPABLE"


def bounty_common_operation(self, a, b):
    res = one_detect(self, a, b)
    if res != "0SWEEPABLE":
        return res
    self.swipe(926, 190, 926, 650, duration=1, post_sleep_time=1)
    self.update_screenshot_array()
    return one_detect(self, a, b)


def to_bounty(self, num, skip_first_screenshot=False):
    bounty_location_y = [0, 206, 309, 418]
    img_ends = "rewarded_task_level-list"
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (731, 431),
        "rewarded_task_location-select": (992, bounty_location_y[num]),
        "rewarded_task_task-info": (1129, 141),
        "rewarded_task_help": (1014, 135),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164)
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)


def to_choose_bounty(self, skip_first_screenshot=False):
    img_ends = "rewarded_task_location-select"
    img_possibles = {
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        "rewarded_task_level-list": (57, 41),
        "rewarded_task_task-info": (1129, 141),
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (731, 431),
        "rewarded_task_help": (1014, 135),
        "rewarded_task_purchase-bounty-ticket-notice": (888, 163),
    }
    rgb_ends = "choose_bounty"
    rgb_possibles = {"main_page": (1198, 580)}
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles,
                      skip_first_screenshot=skip_first_screenshot)


def to_purchase_bounty_ticket_menu(self):
    img_possibles = {
        "rewarded_task_location-select": (148, 101),
    }
    img_ends = "rewarded_task_purchase-bounty-ticket-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def purchase_bounty_ticket(self, times):
    to_purchase_bounty_ticket_menu(self)
    if times == 12:  # max
        self.click(879, 346, wait_over=True)
    else:
        self.click(807, 346, count=times - 1, wait_over=True)
    img_ends = "rewarded_task_location-select"
    img_possibles = {
        "rewarded_task_purchase-bounty-ticket-menu": (766, 507),
        "rewarded_task_purchase-bounty-ticket-notice": (766, 507),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=False)
