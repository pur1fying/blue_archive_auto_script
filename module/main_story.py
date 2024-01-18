import time

import cv2

from core import color, picture


def to_main_story(self, skip_first_screenshot=False):
    rgb_possibles = {
        'main_page': (1188, 575)
    }
    img_possibles = {
        "main_page_bus": (1098, 261),
        "main_story_enter-main-story": (327, 510),
        "main_story_final-ep-feature": (149, 109),
    }
    img_ends = "main_story_menu"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def implement(self):
    self.logger.info("START pushing main story")
    self.quick_method_to_main_page()
    to_main_story(self)
    return True


def judge_acc(self):
    if color.judge_rgb_range(self.latest_img_array, 1170, 621, 200, 255, 200, 255, 200, 255) and \
        color.judge_rgb_range(self.latest_img_array, 1250, 621, 200, 255, 200, 255, 200, 255):
        return 1
    elif color.judge_rgb_range(self.latest_img_array, 1250, 621, 100, 150, 200, 255, 200, 255) and \
        color.judge_rgb_range(self.latest_img_array, 1170, 621, 100, 155, 200, 255, 200, 255):
        return 2
    elif color.judge_rgb_range(self.latest_img_array, 1250, 621, 210, 255, 180, 240, 0, 80) and \
        color.judge_rgb_range(self.latest_img_array, 1170, 621, 200, 255, 180, 240, 0, 80):
        return 3
    return 'UNKNOWN'


def judge_auto(self):
    if color.judge_rgb_range(self.latest_img_array, 1250, 677, 200, 255, 200, 255, 200, 255) and \
        color.judge_rgb_range(self.latest_img_array, 1170, 677, 200, 255, 200, 255, 200, 255):
        return 'off'
    elif color.judge_rgb_range(self.latest_img_array, 1250, 677, 200, 255, 180, 240, 0, 80) and \
        color.judge_rgb_range(self.latest_img_array, 1170, 677, 200, 255, 180, 240, 0, 80):
        return 'on'


def change_acc_auto(self):
    y = 625
    acc_phase = judge_acc(self)
    if acc_phase == 1:
        self.logger.info("CHANGE acceleration phase from 1 to 3")
        self.click(1215, y)
    elif acc_phase == 2:
        self.logger.info("CHANGE acceleration phase from 2 to 3")
        self.click(1215, y, wait=False, wait_over=True, count=2)
    elif acc_phase == 3:
        self.logger.info("ACCELERATION phase 3")
    else:
        self.logger.warning("CAN'T DETECT acceleration BUTTON")
    y = 677

    auto_phase = judge_auto(self)
    if auto_phase == 'off':
        self.logger.info("CHANGE MANUAL to auto")
        self.click(1215, y, wait=False)
    elif auto_phase == 'on':
        self.logger.info("AUTO")
    else:
        self.logger.warning("can't identify auto button")


def enter_fight(self):
    t_start = time.time()
    while time.time() <= t_start + 20:
        self.latest_img_array = self.get_screenshot_array()
        if not color.judge_rgb_range(self.latest_img_array, 897, 692, 0, 64, 161, 217, 240, 255):
            time.sleep(self.screenshot_interval)
        else:
            break


def auto_fight(self):
    enter_fight(self)
    change_acc_auto(self)
