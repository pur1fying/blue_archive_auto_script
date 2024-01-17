import time

from core import color


def implement(self):
    self.quick_method_to_main_page()
    if self.server == 'CN':
        self.logger.info('CN is not supported')
    elif self.server == 'Global':
        global_implement(self)
    return True


def start_sweep(self):
    ends = [
        "purchase_scrimmage_ticket",
        "purchase_ap_notice",
        "start_sweep_notice",
    ]
    res = color.common_rgb_detect_method(self, [[941, 411]], ["mission_info"], ends, True)
    if res == "purchase_scrimmage_ticket" or res == "purchase_ap_notice":
        return res
    ends = [
        "skip_sweep_complete",
        "sweep_complete",
        "purchase_scrimmage_ticket",
        "purchase_ap_notice",
    ]
    return color.common_rgb_detect_method(self, [[765, 501]], ["start_sweep_notice"], ends, True)


def scrimmage_common_operation(self, a, b):
    self.latest_img_array = self.get_screenshot_array()
    line = self.latest_img_array[:, 1076, :]
    click_pos = [
        [1118, 0]
    ]
    pd_los = [
        "scrimmage"
    ]
    ends = [
        "mission_info",
    ]

    los = []
    i = 675
    while i > 196:
        if 131 <= line[i][2] <= 151 and 218 <= line[i][1] <= 238 and 245 <= line[i][0] <= 255 and \
                131 <= line[i - 30][2] <= 151 and 218 <= line[i - 30][1] <= 238 and 245 <= line[i - 30][0] <= 255:
            los.append(i - 35)
            i -= 100
        else:
            i -= 1
    print(los)
    for i in range(0, len(los)):
        click_pos[0][1] = los[i]
        color.common_rgb_detect_method(self, click_pos, pd_los, ends, True)
        t = color.check_sweep_availability(self.latest_img_array, server=self.server)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, wait=False, wait_over=True)
                time.sleep(1)
            else:
                for j in range(0, b - 1):
                    self.click(1014, 300, wait=False, wait_over=True)
                    time.sleep(1)
            res = start_sweep(self)
            if res == "sweep_complete" or res == "skip_sweep_complete":
                return "sweep_complete"
            if res == "purchase_ap_notice":
                return "inadequate_ap"
            if res == "purchase_scrimmage_ticket":
                return "inadequate_ticket"
        elif t == "no-pass" or t == "pass":
            to_scrimmage(self, a, True)

    return True


def to_scrimmage(self, num, skip_first_screenshot=False):
    click_pos = [
        [1198, 580],
        [716, 599],
        [992, 206],
        [640, 116],
        [920, 167],
        [1129, 142],
        [919, 164],
        [649, 508],
    ]
    if num == 1:
        click_pos[2][1] = 206
    elif num == 2:
        click_pos[2][1] = 309
    elif num == 3:
        click_pos[2][1] = 418
    los = [
        "main_page",
        "campaign",
        "choose_scrimmage",
        "reward_acquired",
        "purchase_scrimmage_ticket",
        "mission_info",
        "purchase_ap_notice",
        "skip_sweep_complete"
    ]
    ends = [
        "scrimmage",
    ]
    color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot)


def to_choose_scrimmage(self):
    click_pos = [
        [1198, 580],
        [716, 599],
    ]
    los = [
        "main_page",
        "campaign",
    ]
    ends = [
        "choose_scrimmage",
    ]
    color.common_rgb_detect_method(self, click_pos, los, ends, True)


def purchase_scrimmage_ticket(self, times):
    self.click(148, 101, wait=False,duration=1.5, wait_over=True)
    if times == 12:  # max
        self.click(879, 346, wait=False, wait_over=True)
    else:
        for i in range(0, times - 1):
            self.click(807, 346, wait=False, wait_over=True)
    click_pos = [
        [766, 507],
        [766, 507],
        [640, 116],
    ]
    pd_los = [
        "purchase_scrimmage_ticket",
        "purchase_ticket_notice",
        "reward_acquired",
    ]
    ends = [
        "choose_scrimmage",
    ]
    color.common_rgb_detect_method(self, click_pos, pd_los, ends)


def global_implement(self):
    scrimmage_area_name = ["Trinity", "Gehenna", "Millennium"]
    buy_ticket_times = min(self.config['purchase_scrimmage_ticket_times'], 12)  # ** 购买悬赏委托券的次数

    if buy_ticket_times > 0:
        to_choose_scrimmage(self)
        purchase_scrimmage_ticket(self, buy_ticket_times)

    count = self.config['scrimmage_times']

    self.scrimmage_task_status = [False, False, False]
    just_do_task = False

    for i in range(0, 3):
        if just_do_task:
            self.quick_method_to_main_page()
        if (count[i] == "max" or count[i] > 0) and not self.scrimmage_task_status[i]:
            self.logger.info("Start scrimmage task: " + scrimmage_area_name[i] + " count : " + str(count[i]))
            just_do_task = True
            to_scrimmage(self, i + 1, True)
            res = scrimmage_common_operation(self, i + 1, count[i])
            self.logger.info("Finish scrimmage task: " + scrimmage_area_name[i])
            if res == "sweep_complete":
                self.scrimmage_task_status[i] = True
                if count[i] == "max":
                    return True,
            elif res == "inadequate_ap" or res == "inadequate_ticket":
                self.logger.info(str(self.scrimmage_task_status))
                return True
    self.logger.info(str(self.scrimmage_task_status))
    return True
<<<<<<< Updated upstream
=======


def start_sweep(self):
    img_ends = [
        "scrimmage_purchase-scrimmage-ticket",
        "purchase_ap_notice",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"scrimmage_task-info": (932, 408)}
    res = picture.co_detect(self, None,None, img_ends, img_possibles, skip_first_screenshot=True)
    if res == "scrimmage_purchase-scrimmage-ticket":
        self.logger.warning("INADEQUATE TICKET")
        return "inadequate_ticket"
    if res == "purchase_ap-notice":
        self.logger.warning("INADEQUATE AP")
        return "inadequate_ap"
    img_ends = [
        "normal_task_sweep-complete",
        "normal_task_skip-sweep-complete"
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, None,None, img_ends, img_possibles, skip_first_screenshot=True)
    return "sweep_complete"


def scrimmage_common_operation(self, a, b):
    self.latest_img_array = self.get_screenshot_array()
    line = self.latest_img_array[:, 1076, :]
    los = []
    i = 675
    while i > 196:
        if 131 <= line[i][2] <= 151 and 218 <= line[i][1] <= 238 and 245 <= line[i][0] <= 255 and \
            131 <= line[i - 30][2] <= 151 and 218 <= line[i - 30][1] <= 238 and 245 <= line[i - 30][0] <= 255:
            los.append(i - 35)
            i -= 100
        else:
            i -= 1
    for i in range(0, len(los)):
        img_possibles = {'scrimmage_level-list': (1118, los[i])}
        img_ends = "scrimmage_task-info"
        picture.co_detect(self, None,None, img_ends, img_possibles, True)
        t = color.check_sweep_availability(self.latest_img_array, server=self.server)
        if t == "sss":
            if b == "max":
                self.click(1085, 300, wait=False, wait_over=True)
            else:
                for j in range(0, b - 1):
                    self.click(1014, 300, wait=False, wait_over=True)
                    time.sleep(1)
            return start_sweep(self)
        elif t == "no-pass" or t == "pass":
            to_scrimmage(self, a, True)

    return True


def to_scrimmage(self, num, skip_first_screenshot=False):
    select_scrimmage_y = {
        'CN': [0, 206, 309, 418],
        'JP': [0, 206, 309, 418],
        'Global': [0, 206, 309, 418],
    }
    rgb_ends = "scrimmage"
    rgb_possibles = {
        "main_page": (1198, 580),
        "reward_acquired": (640, 116),
    }
    img_ends = "scrimmage_level-list"
    img_possibles = {
        "main_page_home-feature": (1198, 580),
        "main_page_bus": (716, 599),
        "scrimmage_task_purchase-scrimmage-ticket": (766, 507),
        "scrimmage_academy-select": (992, select_scrimmage_y[self.server][num]),
        "rewarded_task_purchase-scrimmage-ticket-notice": (766, 507),
        "scrimmage_task-info": (1129, 142),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_choose_scrimmage(self):
    rgb_ends = "choose_scrimmage"
    rgb_possibles = {"main_page": (1198, 580)}
    img_ends = "scrimmage_academy-select"
    img_possibles = {
        "main_page-home-feature": (1198, 580),
        "main_page-bus": (716, 599),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles)


def purchase_scrimmage_ticket(self, times):
    self.click(148, 101, wait=False, duration=1.5, wait_over=True)
    if times == 12:  # max
        self.click(879, 346, wait=False, wait_over=True)
    else:
        self.click(807, 346, wait=False, count=times - 1, wait_over=True)
    rgb_ends = "choose_scrimmage",
    rgb_possibles = {
        "purchase_scrimmage_ticket": (766, 507),
        "purchase_ticket_notice": (766, 507),
        "reward_acquired": (640, 116),
    }
    img_ends = "scrimmage_academy-select"
    img_possibles = {
        "scrimmage_task_purchase-scrimmage-ticket": (766, 507),
        "rewarded_task_purchase-scrimmage-ticket-notice": (766, 507),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=False)
>>>>>>> Stashed changes
