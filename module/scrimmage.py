import time

from core import color, picture
from module.clear_special_task_power import get_task_count


def implement(self):
    count = get_task_count(self, "scrimmage", 3)
    if not count:
        return True

    self.to_main_page()
    scrimmage_area_name = ["Trinity", "Gehenna", "Millennium"]
    buy_ticket_times = min(self.config.purchase_scrimmage_ticket_times, 12)  # ** 购买悬赏委托券的次数
    buy_ticket_times = max(buy_ticket_times, 0)
    if buy_ticket_times > 0 and self.server != "CN":
        to_choose_scrimmage(self, True)
        purchase_scrimmage_ticket(self, buy_ticket_times)

    self.scrimmage_task_status = [False, False, False]
    just_do_task = False

    for i in range(0, 3):
        if (count[i] == "max" or count[i] > 0) and not self.scrimmage_task_status[i]:
            self.logger.info("Start scrimmage task: " + scrimmage_area_name[i] + " count : " + str(count[i]))
            if just_do_task:
                to_choose_scrimmage(self, True)
            just_do_task = True
            to_scrimmage(self, i + 1, True)
            res = scrimmage_common_operation(self, i + 1, count[i])
            self.logger.info("Finish scrimmage task: " + scrimmage_area_name[i])
            if res == "sweep_complete":
                self.scrimmage_task_status[i] = True
                if count[i] == "max":
                    return True
            elif res == "inadequate_ap" or res == "inadequate_ticket":
                self.logger.info("Scrimmage task status : " + str(self.scrimmage_task_status))
                return True
    self.logger.info("Scrimmage task status : " + str(self.scrimmage_task_status))
    return True


def start_sweep(self):
    img_ends = [
        "scrimmage_purchase-scrimmage-ticket-menu",
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"scrimmage_task-info": (932, 408)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)
    if res == "scrimmage_purchase-scrimmage-ticket-menu":
        self.logger.warning("INADEQUATE TICKET")
        return "inadequate_ticket"
    if res == "purchase_ap_notice-localized" or res == "purchase_ap_notice":
        self.logger.warning("INADEQUATE AP")
        return "inadequate_ap"
    rgb_possibles = {"level_up": (640, 200)}
    img_ends = [
        "normal_task_sweep-complete",
        "normal_task_skip-sweep-complete"
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
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


def scrimmage_common_operation(self, a, b):
    los = get_los(self)
    if len(los) == 0:
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()
        los = get_los(self)
    for i in range(0, len(los)):
        rgb_possibles = {"scrimmage": (1118, los[i])}
        rgb_ends = "mission_info"
        img_possibles = {"scrimmage_level-list": (1118, los[i])}
        img_ends = "scrimmage_task-info"
        picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, True)
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
            return start_sweep(self)
        elif t == "no-pass" or t == "pass":
            to_scrimmage(self, a, True)

    return True


def to_scrimmage(self, num, skip_first_screenshot=False):
    select_scrimmage_y = [0, 206, 309, 418]
    rgb_possibles = {
        "main_page": (1198, 580),
    }
    img_ends = "scrimmage_level-list"
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (716, 599),
        "scrimmage_academy-select": (992, select_scrimmage_y[num]),
        "scrimmage_purchase-scrimmage-ticket-notice": (886, 162),
        "rewarded_task_help": (1014, 135),
        "scrimmage_task-info": (1129, 142),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_choose_scrimmage(self, skip_first_screenshot=False):
    img_ends = "scrimmage_academy-select"
    img_possibles = {
        "main_page-home-feature": (1198, 580),
        "main_page-bus": (716, 599),
        "scrimmage_level-list": (59, 45),
        "normal_task_skip-sweep-complete": (643, 506),
        "normal_task_sweep-complete": (643, 585),
        "rewarded_task_help": (1014, 135),

        "scrimmage_task-info": (1129, 142),
        "scrimmage_purchase-scrimmage-ticket": (886, 162),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)


def to_purchase_scrimmage_ticket_menu(self):
    img_possibles = {
        "rewarded_task_location-select": (148, 101),
    }
    img_ends = "rewarded_task_purchase-scrimmage-ticket-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def purchase_scrimmage_ticket(self, times):
    to_purchase_scrimmage_ticket_menu(self)
    if times == 12:  # max
        self.click(879, 346, wait_over=True)
    else:
        self.click(807, 346, count=times - 1, wait_over=True)
    rgb_possibles = {"reward_acquired": (640, 116)}
    img_ends = "scrimmage_academy-select"
    img_possibles = {
        "scrimmage_task_purchase-scrimmage-ticket-menu": (766, 507),
        "rewarded_task_purchase-scrimmage-ticket-notice": (766, 507),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=False)
