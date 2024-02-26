import time
from core import color, image, picture


def implement(self, need_check_mode=True):
    self.quick_method_to_main_page()
    to_momotalk2(self, True)
    if need_check_mode:
        check_mode(self)
        time.sleep(0.5)
        self.latest_img_array = self.get_screenshot_array()
    main_to_momotalk = True
    while 1:
        color.wait_loading(self)
        y = 210
        dy = 18
        unread_location = []
        while y <= 630:
            if color.judge_rgb_range(self, 637, y, 250, 252, 70, 72, 24, 26):
                unread_location.append([637, int(y + dy / 2)])
                y += 60
            else:
                y += 1
        length = len(unread_location)
        self.logger.info("find  " + str(length) + "  unread message")
        if length == 0:
            if main_to_momotalk:
                self.logger.info("momo_talk task finished")
                return True
            else:
                self.logger.info("restart momo_talk task")
                self.quick_method_to_main_page()
                return implement(self, need_check_mode=False)
        else:
            for i in range(0, len(unread_location)):
                self.click(unread_location[i][0], unread_location[i][1], wait_over=True, duration=0.5)
                common_solve_affection_story_method(self)
        main_to_momotalk = False
        self.click(170, 197, duration=0.2, wait_over=True)
        self.click(170, 270, duration=0.2, wait_over=True)


def check_mode(self):
    if image.compare_image(self, "momo_talk_newest", need_log=False):
        self.logger.info("change NEWEST to UNREAD mode")
        self.click(514, 177, duration=0.3, wait_over=True)
        self.click(562, 297, duration=0.3, wait_over=True)
        self.click(461, 426, duration=0.3, wait_over=True)
    elif image.compare_image(self, "momo_talk_unread", need_log=False):
        self.logger.info("UNREAD mode")
    else:
        self.logger.info("can't detect mode button")
    self.latest_img_array = self.get_screenshot_array()
    if image.compare_image(self, "momo_talk_up", need_log=False):
        self.logger.info("change UP to DOWN")
        self.click(634, 169, duration=0.2, wait_over=True)
    elif image.compare_image(self, "momo_talk_down", need_log=False):
        self.logger.info("DOWN mode")
    else:
        self.logger.info("can't detect up/down button")
    return True


def to_momotalk2(self, skip_first_screenshot=False):
    rgb_possibles = {
        "main_page": (166, 150),
        "momotalk1": (170, 278),
        "reward_acquired": (640, 100),
    }
    rgb_ends = "momotalk2"
    return picture.co_detect(self, rgb_ends, rgb_possibles, skip_first_screenshot=skip_first_screenshot)


def common_solve_affection_story_method(self):
    self.latest_img_array = self.get_screenshot_array()
    res = get_reply_position(self)
    if res[0] == 'end':
        self.swipe(924, 330, 924, 230, duration=0.1)
        self.click(924, 330)
    start_time = time.time()
    while time.time() <= start_time + 10:
        self.latest_img_array = self.get_screenshot_array()
        res = get_reply_position(self)
        if res[0] == 'reply':
            if res[1] >= 625:
                self.logger.info("swipe upward")
                self.connection.swipe(924, 330, 924, 230, duration=0.1)
                self.click(924, 330)
            else:
                self.logger.info("reply")
                self.click(826, res[1])
            start_time = time.time()
        elif res[0] == 'affection':
            self.logger.info("ENTER affection story")
            self.click(826, res[1])
            time.sleep(0.5)
            common_skip_plot_method(self)
            rgb_end = "reward_acquired"
            picture.co_detect(self, rgb_end)
            to_momotalk2(self, True)
            return
        time.sleep(self.screenshot_interval)
    self.logger.info("current conversation over")


def get_reply_position(self):
    i = 657
    while i > 156:
        if color.judge_rgb_range(self, 786, i, 29, 49, 143, 163, 219, 239, True, 1) and \
            color.judge_rgb_range(self, 786, i + 10, 29, 49, 143, 163, 219, 239, True, 1):
            return 'reply', i + 65
        elif color.judge_rgb_range(self, 862, i, 245, 255, 227, 247, 230, 250) and \
            color.judge_rgb_range(self, 862, i + 10, 245, 255, 125, 155, 145, 175):
            return 'affection', min(625, i + 30)
        else:
            i -= 1
    return 'end', 0


def pd_menu_bright(self):
    if color.judge_rgb_range(self, 1165, 45, 230, 255, 230, 255, 230, 255) and \
        color.judge_rgb_range(self, 1252, 45, 230, 255, 230, 255, 230, 255):
        return True
    return False


def pd_skip_plot_button(self):
    if color.judge_rgb_range(self, 1189, 120, 34, 54, 59, 79, 90, 110) and \
        color.judge_rgb_range(self, 1128, 104, 34, 54, 59, 79, 90, 110) and \
        color.judge_rgb_range(self, 1125, 120, 245, 255, 245, 255, 245, 255) and \
        color.judge_rgb_range(self, 1207, 120, 245, 255, 245, 255, 245, 255):
        return True
    return False


def pd_confirm_button(self):
    if color.judge_rgb_range(self, 691, 552, 110, 130, 210, 230, 245, 255) and \
        color.judge_rgb_range(self, 848, 525, 110, 130, 210, 230, 245, 255):
        return True
    return False


def pd_enter_button(self):
    if color.judge_rgb_range(self, 817, 582, 110, 130, 210, 230, 245, 255) and \
        color.judge_rgb_range(self, 761, 418, 35, 55, 66, 86, 104, 124) and \
        color.judge_rgb_range(self, 1034, 582, 110, 130, 210, 230, 245, 255):
        return True
    return False


def common_skip_plot_method(self):
    while self.flag_run:
        color.wait_loading(self)
        if pd_enter_button(self):
            self.logger.info("Begin Relationship Story")
            self.click(920, 556, duration=4, wait_over=True)
        elif pd_confirm_button(self):
            self.logger.info("find CONFIRM button")
            self.click(766, 520, wait_over=True)
            return True
        else:
            if pd_menu_bright(self):
                self.logger.info("find MENU button")
                self.click(1205, 34, duration=0.1, wait_over=True)
            elif pd_skip_plot_button(self):
                self.logger.info("find SKIP PLOT button")
                self.click(1213, 116, duration=0.1, wait_over=True)
