import time

from core import color, image, picture


def implement(self):
    self.quick_method_to_main_page()
    try:
        count = self.config["rewarded_task_times"]
        if type(count) is str:
            count = count.split(",")
        for i in range(0, len(count)):
            if count[i] == "max":
                continue
            count[i] = int(count[i])
    except Exception as e:
        self.logger.error("rewarded task config error")
        self.logger.error(e)
        return True

    if self.server == 'Global' or self.server == 'JP':
        buy_ticket_times = max(0, self.config['purchase_rewarded_task_ticket_times'])  # ** 购买悬赏委托券的次数
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
                if self.server == 'Global' or self.server == 'JP':
                    self.logger.info(self.rewarded_task_status)
                    return True
            elif res == "0SWEEPABLE":
                self.logger.warning("0 SWEEPABLE")

    self.logger.info(self.rewarded_task_status)
    return True


def start_sweep(self):
    rgb_ends = [
        "purchase_bounty_ticket",
        "start_sweep_notice",
    ]
    rgb_possibles = {'mission_info': (941, 411)}
    img_ends = [
        "rewarded_task_purchase-bounty-ticket",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {
        "rewarded_task_task-info": (941, 411),
    }
    res = picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)
    if res == "rewarded_task_purchase-bounty-ticket" or res == "purchase_bounty_ticket":
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


def one_detect(self, a, b):
    i = 675
    los = []
    while i > 196:
        if color.judge_rgb_range(self, 1076, i, 131, 151, 218, 238, 245, 255) and \
            color.judge_rgb_range(self, 1076, i - 30, 131, 151, 218, 238, 245, 255):
            los.append(i - 35)
            i -= 100
            continue
        else:
            i -= 1
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
    self.swipe(926, 190, 926, 650, duration=1)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    return one_detect(self, a, b)


def to_bounty(self, num, skip_first_screenshot=False):
    bounty_location_y = {
        'CN': [0, 277, 406, 554],
        'JP': [0, 206, 309, 418],
        'Global': [0, 206, 309, 418]
    }
    task_info_cross_x = {
        'CN': 1085,
        'JP': 1129,
        'Global': 1129
    }
    img_ends = "rewarded_task_level-list"
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (731, 431),
        "rewarded_task_location-select": (992, bounty_location_y[self.server][num]),
        "rewarded_task_task-info": (task_info_cross_x[self.server], 141),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles)


def to_choose_bounty(self, skip_first_screenshot=False):
    task_info_cross_x = {
        'CN': 1085,
        'JP': 1129,
        'Global': 1129
    }
    img_ends = "rewarded_task_location-select"
    img_possibles = {
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        "rewarded_task_level-list": (57, 41),
        "rewarded_task_task-info": (task_info_cross_x[self.server], 141),
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (731, 431),
        'rewarded_task_purchase-bounty-ticket-notice': (888, 163),
    }
    rgb_ends = "choose_bounty"
    rgb_possibles = {"main_page": (1198, 580)}
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles,
                      skip_first_screenshot=skip_first_screenshot)


def purchase_bounty_ticket(self, times):
    self.click(148, 101, duration=1.5, wait_over=True)
    if times == 12:  # max
        self.click(879, 346, wait_over=True)
    else:
        self.click(807, 346, count=times - 1, wait_over=True)
    rgb_ends = "choose_bounty",
    rgb_possibles = {
        "purchase_bounty_ticket": (766, 507),
        "purchase_ticket_notice": (766, 507),
        "reward_acquired": (640, 116),
    }
    img_ends = "rewarded_task_location-select"
    img_possibles = {
        "rewarded_task_purchase-bounty-ticket": (766, 507),
        "rewarded_task_purchase-bounty-ticket-notice": (766, 507),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=False)
