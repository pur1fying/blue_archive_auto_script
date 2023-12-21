from gui.util import log
import time
from core import color, image

x = {
    'location-select': (658, 141, 935, 186),
    'purchase-ticket-notice': (557, 297, 692, 330)
}


def implement(self):
    try:
        count = self.config["rewarded_task_times"]
        if type(count) is str:
            count = count.split(",")
        for i in range(0, len(count)):
            if count[i] == "max":
                continue
            count[i] = int(count[i])
    except Exception as e:
        log.logger.error("rewarded task config error")
        log.logger.error(e)
        return True

    if self.server == 'Global':
        buy_ticket_times = min(0, self.config['purchase_bounty_ticket_times'])  # ** 购买悬赏委托券的次数
        if buy_ticket_times > 0:
            to_choose_bounty(self)
            purchase_bounty_ticket(self, buy_ticket_times)

    bounty_name = ["OVERPASS", "DESSERT RAILWAY", "CLASSROOM"]
    self.rewarded_task_status = [False, False, False]
    just_do_task = False

    for i in range(0, 3):
        if just_do_task:
            self.quick_method_to_main_page()
        if count[i] == "max" or count[i] > 0:
            self.logger.info("Start bounty task: " + bounty_name[i] + " count : " + str(count[i]))
            just_do_task = True
            to_bounty(self, i + 1)
            res = bounty_common_operation(self, i + 1, count[i])
            self.logger.info("Finish bounty task: " + bounty_name[i])
            if res == "sweep_complete":
                self.rewarded_task_status[i] = True
                if count[i] == "max":
                    return True
            elif res == "inadequate_ticket":
                self.logger.info("INADEQUATE TICKET")
                if self.server == 'Global':
                    self.logger.info(self.rewarded_task_status)
                    return True

    self.logger.info(self.rewarded_task_status)
    return True


def start_sweep(self):
    if self.server == 'CN':
        possibles = {
            "special_task_task-info": (941, 411),
            "normal_task_start-sweep-notice": (765, 501)
        }
        ends = [
            "normal_task_skip-sweep-complete",
            "normal_task_sweep-complete",
            "buy_ap_notice",
            "rewarded_task_purchase-ticket-notice",
        ]
        res = image.detect(self, end=ends, possibles=possibles)
        if res == "normal_task_sweep-complete":
            return "sweep_complete"
        elif res == "normal_task_skip-sweep-complete":
            return "skip_sweep_complete"
        elif res == "rewarded_task_purchase-ticket-notice":
            return "purchase_bounty_ticket"
    elif self.server == 'Global':
        click_pos = [
            [941, 411],
            [765, 501]
        ]
        pd_los = [
            "mission_info",
            "start_sweep_notice"
        ]
        ends = [
            "skip_sweep_complete",
            "sweep_complete",
            "purchase_bounty_ticket",
        ]
        return color.common_rgb_detect_method(self, click_pos, pd_los, ends)


def bounty_common_operation(self, a, b):
    click_pos = [
        [1118, 0]
    ]
    pd_los = [
        "bounty"
    ]
    ends = [
        "mission_info",
    ]
    possibles = {
        "special_task_level-list": (1118, 0)
    }
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
    print(los)
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
                self.click(1085, 300, duration=1)
            else:
                self.click(1014, 300, count=b - 1, duration=1)
            res = start_sweep(self)
            if res == "sweep_complete" or res == "skip_sweep_complete":
                return "sweep_complete"
            if res == "purchase_bounty_ticket":
                return "inadequate_ticket"
        elif t == "no-pass" or t == "pass":
            to_bounty(self, a)

    self.swipe(926, 190, 926, 650, duration=1)
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
    print(los)
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
                self.click(1085, 300, duration=1)
            else:
                self.click(1014, 300, count=b - 1, duration=1)
            res = start_sweep(self)
            if res == "sweep_complete" or res == "skip_sweep_complete":
                return "sweep_complete"
            if res == "purchase_bounty_ticket":
                return "inadequate_ticket"
        elif t == "no-pass" or t == "pass":
            to_bounty(self, a)

    return True


def to_bounty(self, num):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (1198, 580),
            "main_page_bus": (731, 477),
            "rewarded_task_location-select": (992, 0),
            "special_task_task-info": (1085, 141),
        }
        if num == 1:
            possibles["rewarded_task_location-select"] = (992, 277)
        elif num == 2:
            possibles["rewarded_task_location-select"] = (992, 406)
        elif num == 3:
            possibles["rewarded_task_location-select"] = (992, 554)
        image.detect(self, 'special_task_level-list', possibles)
    elif self.server == 'Global':
        click_pos = [
            [1198, 580],
            [746, 423],
            [992, 206],
            [640, 116],
            [920, 167],
            [1129, 142],
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
            "choose_bounty",
            "reward_acquired",
            "purchase_bounty_ticket",
            "mission_info",
            "skip_sweep_complete",
        ]
        ends = [
            "bounty",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)


def to_choose_bounty(self):
    click_pos = [
        [1198, 580],
        [746, 423],
    ]
    los = [
        "main_page",
        "campaign",
    ]
    ends = [
        "choose_bounty",
    ]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def purchase_bounty_ticket(self, times):
    self.click(148, 101, rate=1.5)
    if times == 12:  # max
        self.click(879, 346)
    else:
        self.click(807, 346, wait=False, count=times - 1)
    click_pos = [
        [766, 507],
        [766, 507],
        [640, 116],
    ]
    pd_los = [
        "purchase_bounty_ticket",
        "purchase_ticket_notice",
        "reward_acquired",
    ]
    ends = [
        "choose_bounty",
    ]
    color.common_rgb_detect_method(self, click_pos, pd_los, ends)
