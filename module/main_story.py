import time

import cv2

from core import color, picture, image


def to_main_story(self, skip_first_screenshot=False):
    rgb_possibles = {
        'main_page': (1188, 575)
    }
    img_possibles = {
        "main_page_bus": (1098, 261),
        "main_story_enter-main-story": (327, 510),
        "main_story_episode5": (149, 109),
        "main_story_select-episode": (60, 36),
    }
    img_ends = "main_story_menu"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_select_episode(self, res, skip_first_screenshot):
    img_possibles = {"main_story_menu": res}
    img_ends = [
        "main_story_episode-cleared-feature",
        "main_story_plot-index",
        "main_story_plot-not-open",
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_episode_info(self, pos, skip_first_screenshot=False):
    img_possibles = {"main_story_select-episode": (pos[0] + 466, pos[1])}
    img_ends = "main_story_episode-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def implement(self):
    self.logger.info("START pushing main story")
    self.quick_method_to_main_page()
    max_episode = 5
    if self.server == 'CN':
        max_episode = 3
    for i in range(1, max_episode + 1):
        if i != 5:
            self.logger.info("-- Pushing Episode " + str(i) + " --")
        else:
            self.logger.info("-- Pushing Finial Episode --")
        to_main_story(self, True)
        to_episode(self, i)
        episode_status = check_episode(self)
        while episode_status != "ALL_CLEAR":
            res = to_select_episode(self, episode_status, skip_first_screenshot=True)
            while res == "main_story_plot-index":
                possible_pos = [[728, 257], [668, 362]]
                for pos in possible_pos:
                    if check_current_plot_status(self.latest_img_array, pos) == "UNCLEAR":
                        to_episode_info(self, pos, True)
                        res = clear_current_plot(self, True)
                        break
                else:
                    res = to_select_episode(self, episode_status, False)
            to_main_story(self, True)
            to_episode(self, i)
            episode_status = check_episode(self)
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
        self.click(1215, y, wait=False, wait_over=True, count=2)
    elif acc_phase == 2:
        self.logger.info("CHANGE acceleration phase from 2 to 3")
        self.click(1215, y)
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


def check_episode(self):
    position1 = [982, 282]
    position2 = [833, 537]
    k = (position2[1] - position1[1]) / (position2[0] - position1[0])
    b = position1[1] - k * position1[0]
    for i in range(833, 982):
        y = int(k * i + b)
        if color.judge_rgb_range(self.latest_img_array, i, y, 250, 255, 177, 200, 0, 80):
            return i + 155, y + 17
    return "ALL_CLEAR"


def to_episode(self, num):
    episode_position = [0, [305, 255], [526, 449], [892, 255], [597, 449], [850, 630]]
    if num in [1, 2, 3, 4]:
        self.swipe(14, 364, 654, 364, 0.1)
        time.sleep(0.7)
    if num == 4:
        self.swipe(654, 364, 14, 364, 0.1)
        time.sleep(0.7)
    img_possibles = {"main_story_menu": episode_position[num]}
    img_ends = "main_story_episode" + str(num)
    picture.co_detect(self, None, None, img_ends, img_possibles)
    time.sleep(0.3)
    self.latest_img_array = self.get_screenshot_array()
    return True


def check_plot_cleared(self):
    if image.compare_image(self, 'main_story_episode-cleared-feature', need_log=False):
        self.logger.info("PLOT CLEARED")
        return True
    elif image.compare_image(self, 'main_story_plot-index', need_log=False):
        self.logger.info("PLOT UNCLEARED")
        return False
    else:
        self.logger.warning("CAN'T DETECT PLOT STATUS")
        return "UNKNOWN"


def check_current_plot_status(img, position):
    if color.judge_rgb_range(img, position[0], position[1], 245, 255, 214, 234, 0, 40):
        return "CLEAR"
    if color.judge_rgb_range(img, position[0], position[1], 170, 196, 178, 199, 178, 199):
        return "UNLOCK"
    if color.judge_rgb_range(img, position[0], position[1], 197, 207, 200, 210, 200, 210):
        return "UNCLEAR"


def clear_current_plot(self, skip_first_screenshot=False):
    rgb_possibles = {
        'reward_acquired': (640, 100),
    }
    img_possibles = {
        "main_story_episode-info": (650, 511),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519),
    }
    img_ends = [
        "main_story_episode-cleared-feature",
        "main_story_plot-index",
        "main_story_plot-not-open",
        "plot_formation",
        "plot_self-formation"
    ]
    res = picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    if res == "plot_formation" or res == "plot_self-formation":
        rgb_ends = "fighting_feature"
        img_possibles = {"plot_formation": (1157, 651)}
        if res == "plot_self-formation":
            auto_choose_formation(self, True)
            img_possibles = {"plot_self-formation": (1157, 651)}
        picture.co_detect(self, rgb_ends, None, None, img_possibles, True)
        auto_fight(self)
        rgb_possibles = {'reward_acquired': (640, 100)}
        img_possibles = {
            "main_story_episode-info": (650, 511),
            'plot_menu': (1202, 37),
            'plot_skip-plot-button': (1208, 116),
            'plot_skip-plot-notice': (770, 519),
            'normal_task_fight-confirm': (1168, 659),
            'normal_task_fail-confirm': (643, 658),
        }
        img_ends = [
            "main_story_episode-cleared-feature",
            "main_story_plot-index",
            "main_story_plot-not-open",
        ]
        return picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    return res


def auto_choose_formation(self, skip_first_screenshot=False):
    self.logger.info("AUTO choose formation")
    img_possibles = {"plot_self-formation": (1180, 183)}
    img_ends = "plot_change-unit-formation"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
    self.click(649, 596, wait_over=True, wait=False)
    img_possibles = {"plot_change-unit-formation": (1130, 586)}
    img_ends = "plot_self-formation"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
