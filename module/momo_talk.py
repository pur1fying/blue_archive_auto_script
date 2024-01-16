import time
import numpy as np
from core import color, image


def implement(self, need_check_mode=True):
    self.quick_method_to_main_page()
    to_momotalk2(self, True)
    if need_check_mode:
        check_mode(self)
    main_to_momotalk = True
    while 1:
        color.wait_loading(self)
        location_y = 210
        red_dot = np.array([25, 71, 251])
        location_x = 637
        dy = 18
        unread_location = []
        while location_y <= 630:
            if np.array_equal(self.latest_img_array[location_y][location_x], red_dot) and \
                np.array_equal(self.latest_img_array[location_y + dy][location_x], red_dot):
                unread_location.append([location_x, location_y + dy / 2])
                location_y += 60
            else:
                location_y += 1
        length = len(unread_location)
        self.logger.info("find  " + str(length) + "  unread message")
        if length == 0:
            if main_to_momotalk:
                self.logger.info("momo_talk task finished")
                self.click(1124, 117, wait=False)
                return True
            else:
                self.logger.info("restart momo_talk task")
                self.quick_method_to_main_page()
                return implement(self, need_check_mode=False)
        else:
            for i in range(0, len(unread_location)):
                self.click(unread_location[i][0], unread_location[i][1], wait_over=True, wait=False)
                time.sleep(0.5)
                common_solve_affection_story_method(self)
        main_to_momotalk = False
        self.click(170, 197, wait=False, duration=0.2, wait_over=True)
        self.click(170, 270, wait=False, duration=0.2, wait_over=True)


def check_mode(self):
    mode_confirm_y = {
        'CN': 365,
        'Global': 426,
        'JP': 426,
    }
    mode_unread_x = {
        'CN': 444,
        'Global': 563,
        'JP': 555,
    }
    if self.server == 'CN' or self.server == 'JP':
        if image.compare_image(self, "momo_talk_newest", threshold=3):
            self.logger.info("change NEWEST to UNREAD mode")
            self.click(514, 177, wait=False, duration=0.3, wait_over=True)
            self.click(mode_unread_x[self.server], 297, wait=False, duration=0.3, wait_over=True)
            self.click(461, mode_confirm_y[self.server], wait=False, duration=0.3, wait_over=True)
        elif image.compare_image(self, "momo_talk_unread", threshold=3):
            self.logger.info("UNREAD mode")
        else:
            self.logger.info("can't detect mode button")
            return False
        self.latest_img_array = self.get_screenshot_array()
        if image.compare_image(self, "momo_talk_up", threshold=3):
            self.logger.info("change UP to DOWN")
            self.click(634, 169, duration=0.2, wait=False, wait_over=True)
        elif image.compare_image(self, "momo_talk_down", threshold=3):
            self.logger.info("DOWN mode")
        else:
            self.logger.info("can't detect up/down button")
            return False
        return True
    elif self.server == 'Global':
        if color.judge_rgb_range(self.latest_img_array, 487, 177, 50, 150, 50, 150, 50, 150) and \
            color.judge_rgb_range(self.latest_img_array, 486, 183, 245, 255, 245, 255, 245, 255):
            self.logger.info("change NEWEST to UNREAD mode")
            self.click(514, 177, wait=False, duration=0.3, wait_over=True)
            self.click(mode_unread_x[self.server], 297, wait=False, duration=0.3, wait_over=True)
            self.click(461, mode_confirm_y[self.server], wait=False, duration=0.3, wait_over=True)
        elif color.judge_rgb_range(self.latest_img_array, 486, 183, 50, 150, 50, 150, 50, 150) and \
            color.judge_rgb_range(self.latest_img_array, 487, 177, 245, 255, 245, 255, 245, 255):
            self.logger.info("UNREAD mode")
        else:
            self.logger.info("can't detect mode button")
            return False


def to_momotalk2(self, skip_first_screenshot=False):
    click_pos = [
        [166, 150],
        [170, 278],
        [640, 100],
    ]
    los = [
        "main_page",
        "momotalk1",
        "reward_acquired",
    ]
    ends = ["momotalk2"]
    color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot)


def common_solve_affection_story_method(self):
    self.latest_img_array = self.get_screenshot_array()
    res = get_reply_position(self.latest_img_array)
    if res[0] == 'end':
        self.swipe(924, 330, 924, 230, duration=0.1)
        self.click(924, 330, wait=False)
    start_time = time.time()
    while time.time() <= start_time + 10:
        img = self.get_screenshot_array()
        res = get_reply_position(img)
        if res[0] == 'reply':
            if res[1] >= 625:
                self.logger.info("swipe upward")
                self.connection.swipe(924, 330, 924, 230, duration=0.1)
                self.click(924, 330, wait=False)
            else:
                self.logger.info("reply")
                self.click(826, res[1], wait=False)
            start_time = time.time()
        elif res[0] == 'affection':
            self.logger.info("ENTER affection story")
            self.click(826, res[1], wait=False)
            time.sleep(0.5)
            common_skip_plot_method(self)
            to_momotalk2(self)
            return
        time.sleep(self.screenshot_interval)
    self.logger.info("current conversation over")


def get_reply_position(img):
    i = 156
    while i < 657:
        if color.judge_rgb_range(img, 786, i, 29, 49, 143, 163, 219, 239) and \
            color.judge_rgb_range(img, 786, i + 10, 29, 49, 143, 163, 219, 239):
            return 'reply', i + 65
        elif color.judge_rgb_range(img, 862, i, 245, 255, 227, 247, 230, 250) and \
            color.judge_rgb_range(img, 862, i + 10, 245, 255, 125, 155, 145, 175):
            return 'affection', min(625, i + 30)
        else:
            i += 1
    return 'end', 0


def pd_menu_bright(img_array):
    if color.judge_rgb_range(img_array, 1165, 45, 230, 255, 230, 255, 230, 255) and \
        color.judge_rgb_range(img_array, 1252, 45, 230, 255, 230, 255, 230, 255):
        return True
    return False


def pd_skip_plot_button(img_array):
    if color.judge_rgb_range(img_array, 1189, 120, 34, 54, 59, 79, 90, 110) and \
        color.judge_rgb_range(img_array, 1128, 104, 34, 54, 59, 79, 90, 110) and \
        color.judge_rgb_range(img_array, 1125, 120, 245, 255, 245, 255, 245, 255) and \
        color.judge_rgb_range(img_array, 1207, 120, 245, 255, 245, 255, 245, 255):
        return True
    return False


def pd_confirm_button(img_array):
    if color.judge_rgb_range(img_array, 691, 552, 110, 130, 210, 230, 245, 255) and \
        color.judge_rgb_range(img_array, 848, 525, 110, 130, 210, 230, 245, 255):
        return True
    return False


def pd_enter_button(img_array):
    if color.judge_rgb_range(img_array, 817, 582, 110, 130, 210, 230, 245, 255) and \
        color.judge_rgb_range(img_array, 761, 418, 35, 55, 66, 86, 104, 124) and \
        color.judge_rgb_range(img_array, 1034, 582, 110, 130, 210, 230, 245, 255):
        return True
    return False


def common_skip_plot_method(self):
    fail_cnt = 0
    while fail_cnt <= 20 / self.screenshot_interval:
        color.wait_loading(self)
        if pd_enter_button(self.latest_img_array):
            self.logger.info("Begin Relationship Story")
            self.click(920, 556, wait=False, duration=4, wait_over=True)
        elif pd_confirm_button(self.latest_img_array):
            self.logger.info("find CONFIRM button")
            self.click(766, 520, wait=False, wait_over=True)
            return True
        else:
            fail_cnt += 1
            if pd_menu_bright(self.latest_img_array):
                self.logger.info("find MENU button")
                self.click(1205, 34, wait=False, duration=0.1, wait_over=True)
            elif pd_skip_plot_button(self.latest_img_array):
                self.logger.info("find SKIP PLOT button")
                self.click(1213, 116, wait=False, duration=0.1, wait_over=True)
            else:
                self.logger.info("Didn't find confirm button, fail count: " + str(fail_cnt))
    self.logger.error("skip plot fail")
    return False
