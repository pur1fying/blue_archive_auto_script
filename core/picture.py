import time
import typing

import cv2

from core import color, image, Baas_thread
from core.color import match_rgb_feature
from core.exception import RequestHumanTakeOver, FunctionCallTimeout, PackageIncorrect
from module.main_story import set_acc_and_auto


def co_detect(self: Baas_thread, rgb_ends: typing.Union[list[str], str] = None, rgb_reactions: dict = None,
              img_ends: typing.Union[list, str, tuple] = None, img_reactions: dict = None,
              skip_first_screenshot=False,
              tentative_click=False, tentative_x=1238, tentative_y=45, max_fail_cnt=10,
              pop_ups_rgb_reactions: dict = None, pop_ups_img_reactions: dict = None,
              time_out=600, check_pkg_interval=20):
    """
        Detects specific RGB or image features on the screen and performs actions based on the detection.

        Args:
            self: The BAAS thread.
            rgb_ends (list, optional): RGB features that indicate the end of detection.
            rgb_reactions (dict, optional): Possible RGB features and their corresponding click positions.
            img_ends (list or str or tuple, optional): Image features that indicate the end of detection.
            img_reactions (dict, optional): Possible image features and their corresponding click positions.
            skip_first_screenshot (bool, optional): Whether to skip the first screenshot to save time.
            tentative_click (bool, optional): Whether to perform tentative clicks if detection fails.
            tentative_x (int, optional): X-coordinate for tentative clicks.
            tentative_y (int, optional): Y-coordinate for tentative clicks.
            max_fail_cnt (int, optional): The count of recognition failures before performing a tentative click.
            pop_ups_rgb_reactions (dict, optional): Possible RGB features for pop-ups and their corresponding click positions.
            pop_ups_img_reactions (dict, optional): Possible image features for pop-ups and their corresponding click positions.
            time_out (int, optional): Timeout(second(s)) for the detection process.
            check_pkg_interval (int, optional): Interval(second(s)) for checking the current package.

        Raises:
            FunctionCallTimeout: If the detection process times out.
            PackageIncorrect: If the current package is incorrect.
            RequestHumanTakeOver: If the detection process is stopped manually.

        Returns:
            str: The name of the detected end feature.
    """

    # Initialize variables
    fail_cnt = 0
    self.last_click_time = 0
    self.last_click_position = (0, 0)
    self.last_click_name = ""
    start_time = time.time()
    feature_last_appear_time = start_time
    last_check_pkg_time = start_time

    # Convert single RGB or image features to lists
    if type(rgb_ends) is not list:
        rgb_ends = [rgb_ends]
    if type(img_ends) is not list:
        img_ends = [img_ends]

    while self.flag_run:
        current_time = time.time()
        if skip_first_screenshot:
            skip_first_screenshot = False
        else:
            self.update_screenshot_array()
        # time out check
        if current_time - start_time > time_out:
            raise FunctionCallTimeout("Co_detect function timeout reached.")

        # package check
        if (current_time - feature_last_appear_time > check_pkg_interval
            and current_time - last_check_pkg_time > check_pkg_interval):
            last_check_pkg_time = current_time
            pkgName = self.connection.get_current_package()
            self.logger.info(f"Current package name: {pkgName}")
            if pkgName != self.package_name:
                raise PackageIncorrect(pkgName)

        # loading check
        color.wait_loading(self)

        # exit the stage if any end feature is matched
        for rgb_feature in rgb_ends:
            if rgb_feature is None:
                continue
            if color.match_rgb_feature(self, rgb_feature):
                self.logger.info("Stage ended with matched RGB feature: " + rgb_feature)
                return rgb_feature
        for img_feature in img_ends:
            if img_feature is None:
                continue
            if match_img_feature(self, img_feature):
                self.logger.info('Stage ended with matched img feature: ' + str(img_feature))
                return img_feature

        # click if match reaction rules
        matched = False
        if rgb_reactions is not None:
            for rgb_feature, click in rgb_reactions.items():
                if match_rgb_feature(self, rgb_feature):
                    matched = True
                    feature_last_appear_time = current_time
                    if (current_time - self.last_click_time <= 2
                        and self.last_click_position[0] == click[0] and self.last_click_position[1] == click[1]
                        and self.last_click_name == rgb_feature):
                        # avoid duplicated clicks

                        break
                    self.logger.info(f"RGB feature: {rgb_feature} -> Click @ ({click[0]},{click[1]})")
                    if click[0] >= 0 and click[1] >= 0:
                        self.last_click_time = current_time
                        self.click(click[0], click[1])
                        self.last_click_position = (click[0], click[1])
                        self.last_click_name = rgb_feature
                    break
        if not matched and img_reactions is not None:
            for img_feature, click in img_reactions.items():
                threshold = 0.8 if len(click) < 3 else click[2]
                rgb_diff = 20 if len(click) < 4 else click[3]
                if match_img_feature(self, img_feature, threshold, rgb_diff):
                    matched = True
                    feature_last_appear_time = current_time
                    if (time.time() - self.last_click_time <= 2
                        and self.last_click_position[0] == click[0] and self.last_click_position[1] == click[1]
                        and self.last_click_name == img_feature):
                        break
                    self.logger.info(f"Image feature: {img_feature} -> Click @ ({click[0]},{click[1]})")
                    if click[0] >= 0 and click[1] >= 0:
                        self.last_click_time = feature_last_appear_time
                        self.click(click[0], click[1])
                        self.last_click_position = (click[0], click[1])
                        self.last_click_name = img_feature
                    break
        if not matched and not deal_with_pop_ups(self, pop_ups_rgb_reactions, pop_ups_img_reactions):
            if tentative_click:
                fail_cnt += 1
                if fail_cnt > max_fail_cnt:
                    self.logger.info(
                        f"Performing tentative click @ ({tentative_x},{tentative_y}) due to recognition failure.")
                    self.click(tentative_x, tentative_y)

                    # if recognition failed for too many times, then preform a tentative click and take a break.
                    time.sleep(self.screenshot_interval * 5)
                    # fail_cnt = 0
        if matched:
            fail_cnt = 0

    if not self.flag_run:
        raise RequestHumanTakeOver("Request Human Take Over.")


def deal_with_pop_ups(self, pop_ups_rgb_reactions: dict = None, pop_ups_img_reactions: dict = None):
    common_pop_ups = {
        "reward_acquired": (640, 100),
        "relationship_rank_up": (640, 100),
        "level_up": (640, 200)
    }
    if pop_ups_rgb_reactions is not None:
        common_pop_ups.update(pop_ups_rgb_reactions)
    for rgb_feature, click in common_pop_ups.items():
        if color.match_rgb_feature(self, rgb_feature):
            self.logger.info("Found pop-ups RGB feature: " + rgb_feature)
            if rgb_feature == "fighting_feature":
                self.logger.info("Detected battle entry. Waiting for auto-battle to complete.")
                set_acc_and_auto(self)
                common_task_img_reactions = {
                    "normal_task_mission-operating-task-info-notice": (995, 101),
                    "normal_task_end-turn": (890, 162),
                    "normal_task_teleport-notice": (886, 162),
                    'normal_task_present': (640, 519),
                    "normal_task_fight-confirm": (1171, 670),
                }
                img_ends = "normal_task_task-operating-feature"
                co_detect(self, None, None, img_ends, common_task_img_reactions, True)
                self.set_screenshot_interval(1)
            if click[0] >= 0 and click[1] >= 0:
                self.click(click[0], click[1])
                self.last_click_time = time.time()
                self.last_click_position = (click[0], click[1])
                self.last_click_name = rgb_feature
                return True, rgb_feature
    common_task_img_reactions = {
        'CN': {
            'main_page_net-work-unstable': (767, 501),
        },
        'JP': {

        },
        'Global': {
            'main_page_login-store': (883, 162),
            'main_page_net-work-unstable': (767, 501),
            'main_page_store-service-unavailable': (640, 500),
            'main_page_request-failed-notice': (640, 513),
        }
    }
    common_task_img_reactions = common_task_img_reactions[self.server]
    if pop_ups_img_reactions is not None:
        common_task_img_reactions.update(pop_ups_img_reactions)
    for rgb_feature, click in common_task_img_reactions.items():
        if image.compare_image(self, rgb_feature):
            self.logger.info("find " + rgb_feature)
            if rgb_feature == "activity_choose-buff":
                choose_buff(self)
            if click[0] >= 0 and click[1] >= 0:
                self.click(click[0], click[1])
                self.last_click_time = time.time()
                self.last_click_position = (click[0], click[1])
                self.last_click_name = rgb_feature
                return True, rgb_feature
    return False


def choose_buff(self):
    self.logger.info("Choose Buff")
    img_possibles = {
        "activity_buff-one-of-three": (628, 467),
        "activity_buff-two-of-three": (628, 467),
    }
    img_ends = "activity_buff-three-of-three"
    co_detect(self, None, None, img_ends, img_possibles, True)


def match_img_feature(
        self: Baas_thread,
        img_feature: typing.Union[tuple, str],
        threshold: float = 0.8,
        rgb_diff: int = 20
) -> bool:
    if type(img_feature) is tuple:
        image_name = img_feature[0]
        length = len(img_feature)
        if length >= 2:
            threshold = img_feature[1]
        if length >= 3:
            rgb_diff = img_feature[2]
    else:
        image_name = img_feature
    return image.compare_image(self, image_name, threshold, rgb_diff)



def match_any_img_feature(self: Baas_thread, featureList: list[typing.Union[tuple, str]]) -> bool:
    for img_feature in featureList:
        if match_img_feature(self, img_feature):
            return True
    return False


# pop-ups that only appear once
GAME_ONE_TIME_POP_UPS = {
    'CN': {
        'main_page_news': (1142, 104),
        'main_page_news2': (1142, 104),
        'main_page_item-expire': (925, 119),
        'main_page_renewal-month-card': (927, 109),
    },
    'JP': {
        'main_page_news': (1142, 104),
    },
    'Global': {
        'main_page_news': (1227, 56),
        'main_page_item-expired-notice': (922, 159),
        'main_page_item-expiring-notice': (931, 132),
        'main_page_Failed-to-convert-errorResponse': (641, 511)
    }
}
