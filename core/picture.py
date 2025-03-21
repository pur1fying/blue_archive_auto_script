import time
from core import color, image
from module.main_story import change_acc_auto
from core.exception import RequestHumanTakeOver, FunctionCallTimeout, PackageIncorrect


def co_detect(self, rgb_ends=None, rgb_possibles=None, img_ends=None, img_possibles=None, skip_first_screenshot=False,
              tentative_click=False, tentative_x=1238, tentative_y=45, max_fail_cnt=10, rgb_pop_ups=None,
              img_pop_ups=None, time_out=600, check_pkg_interval=20):
    """
        Detects specific RGB or image features on the screen and performs actions based on the detection.

        Args:
            self: The BAAS thread.
            rgb_ends (list or str, optional): RGB features that indicate the end of detection.
            rgb_possibles (dict, optional): Possible RGB features and their corresponding click positions.
            img_ends (list or str or tuple, optional): Image features that indicate the end of detection.
            img_possibles (dict, optional): Possible image features and their corresponding click positions.
            skip_first_screenshot (bool, optional): Whether to skip the first screenshot.
            tentative_click (bool, optional): Whether to perform tentative clicks if detection fails.
            tentative_x (int, optional): X-coordinate for tentative clicks.
            tentative_y (int, optional): Y-coordinate for tentative clicks.
            max_fail_cnt (int, optional): Maximum number of failed attempts to perform a tentative click.
            rgb_pop_ups (dict, optional): RGB features for pop-ups that can appear at any time.
            img_pop_ups (dict, optional): Image features for pop-ups that can appear at any time.
            time_out (int, optional): Timeout for the detection process.
            check_pkg_interval (int, optional): Interval for checking the current package.

        Raises:
            - FunctionCallTimeout: If the detection process times out.
            - PackageIncorrect: If the current package is incorrect.
            - RequestHumanTakeOver: If the detection process is stopped manually.

        Returns:
            - str: The name of the detected end feature.
    """
    fail_cnt = 0
    self.last_click_time = 0
    self.last_click_position = (0, 0)
    self.last_click_name = ""
    start_time = time.time()
    feature_last_appear_time = start_time
    last_check_pkg_time = start_time
    while self.flag_run:
        t_start_this_round = time.time()
        if t_start_this_round - start_time > time_out:
            raise FunctionCallTimeout("Co_detect function timeout reached.")
        if t_start_this_round - feature_last_appear_time > check_pkg_interval and t_start_this_round - last_check_pkg_time > check_pkg_interval:
            last_check_pkg_time = t_start_this_round
            self.logger.info("Check package.")
            pkg = self.connection.get_current_package()
            if pkg != self.package_name:
                raise PackageIncorrect(pkg)
        if skip_first_screenshot:
            skip_first_screenshot = False
        else:
            color.wait_loading(self)
        if rgb_ends is not None:
            if type(rgb_ends) is str:
                rgb_ends = [rgb_ends]
            for i in range(0, len(rgb_ends)):
                if color.judgeRGBFeature(self, rgb_ends[i]):
                    self.logger.info("end : " + rgb_ends[i])
                    return rgb_ends[i]
        if img_ends is not None:
            if type(img_ends) is str or type(img_ends) is tuple:
                img_ends = [img_ends]
            for i in range(0, len(img_ends)):
                img_name = img_ends[i]
                threshold = 0.8
                rgb_diff = 20
                if type(img_ends[i]) is tuple:
                    if len(img_ends[i]) == 2:
                        img_name = img_ends[i][0]
                        threshold = img_ends[i][1]
                    elif len(img_ends[i]) == 3:
                        img_name = img_ends[i][0]
                        threshold = img_ends[i][1]
                        rgb_diff = img_ends[i][2]
                if image.compare_image(self, img_name, threshold, rgb_diff):
                    self.logger.info('end : ' + img_name)
                    return img_name
        f = 0
        if rgb_possibles is not None:
            for position, click in rgb_possibles.items():
                if position not in self.rgb_feature:
                    continue
                for j in range(0, len(self.rgb_feature[position][0])):
                    if not color.judge_rgb_range(self,
                                                 self.rgb_feature[position][0][j][0],
                                                 self.rgb_feature[position][0][j][1],
                                                 self.rgb_feature[position][1][j][0],
                                                 self.rgb_feature[position][1][j][1],
                                                 self.rgb_feature[position][1][j][2],
                                                 self.rgb_feature[position][1][j][3],
                                                 self.rgb_feature[position][1][j][4],
                                                 self.rgb_feature[position][1][j][5]):
                        break
                else:
                    fail_cnt = 0
                    f = 1
                    feature_last_appear_time = time.time()
                    if time.time() - self.last_click_time <= 2 and self.last_click_position[0] == click[0] and \
                        self.last_click_position[1] == click[1] and self.last_click_name == position:
                        break
                    self.logger.info("find : " + position)
                    if click[0] >= 0 and click[1] >= 0:
                        self.last_click_time = feature_last_appear_time
                        self.click(click[0], click[1])
                        self.last_click_position = (click[0], click[1])
                        self.last_click_name = position
                    break
        if f == 1:
            continue
        if img_possibles is not None:
            for position, click in img_possibles.items():
                threshold = 0.8
                rgb_diff = 20
                if len(click) == 3:
                    threshold = click[2]
                elif len(click) == 4:
                    threshold = click[2]
                    rgb_diff = click[3]
                if image.compare_image(self, position, threshold, rgb_diff):
                    fail_cnt = 0
                    f = 1
                    feature_last_appear_time = time.time()
                    if time.time() - self.last_click_time <= 2 and self.last_click_position[0] == click[0] and \
                        self.last_click_position[1] == click[1] and self.last_click_name == position:
                        break
                    self.logger.info("find " + position)
                    if click[0] >= 0 and click[1] >= 0:
                        self.last_click_time = feature_last_appear_time
                        self.click(click[0], click[1])
                        self.last_click_position = (click[0], click[1])
                        self.last_click_name = position
                    break
        if f == 1:
            continue
        if not deal_with_pop_ups(self, rgb_pop_ups, img_pop_ups):
            if tentative_click:
                fail_cnt += 1
                if fail_cnt > max_fail_cnt:
                    self.logger.info("tentative clicks")
                    self.click(tentative_x, tentative_y)
                    time.sleep(self.screenshot_interval)
                    fail_cnt = 0
    if not self.flag_run:
        raise RequestHumanTakeOver


def deal_with_pop_ups(self, rgb_pop_ups, img_pop_ups):  # pop ups which can appear at any time
    rgb_possibles = {
        "reward_acquired": (640, 100),
        "relationship_rank_up": (640, 100),
        "level_up": (640, 200)
    }
    if rgb_pop_ups is not None:
        rgb_possibles.update(rgb_pop_ups)
    for position, click in rgb_possibles.items():
        if color.judgeRGBFeature(self, position):
            self.logger.info("find : " + position)
            if position == "fighting_feature":
                self.logger.info("Enter fight, wait fight auto end")
                change_acc_auto(self)
                img_possibles = {
                    "normal_task_mission-operating-task-info-notice": (995, 101),
                    "normal_task_end-turn": (890, 162),
                    "normal_task_teleport-notice": (886, 162),
                    'normal_task_present': (640, 519),
                    "normal_task_fight-confirm": (1171, 670),
                }
                img_ends = "normal_task_task-operating-feature"
                co_detect(self, None, None, img_ends, img_possibles, True)
                self.set_screenshot_interval(1)
            if click[0] >= 0 and click[1] >= 0:
                self.click(click[0], click[1])
                self.last_click_time = time.time()
                self.last_click_position = (click[0], click[1])
                self.last_click_name = position
                return True, position
    img_possibles = {
        'CN': {

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
    img_possibles = img_possibles[self.server]
    if img_pop_ups is not None:
        img_possibles.update(img_pop_ups)
    for position, click in img_possibles.items():
        if image.compare_image(self, position):
            self.logger.info("find " + position)
            if position == "activity_choose-buff":
                choose_buff(self)
            if click[0] >= 0 and click[1] >= 0:
                self.click(click[0], click[1])
                self.last_click_time = time.time()
                self.last_click_position = (click[0], click[1])
                self.last_click_name = position
                return True, position
    return False


def choose_buff(self):
    self.logger.info("Choose Buff")
    img_possibles = {
        "activity_buff-one-of-three": (628, 467),
        "activity_buff-two-of-three": (628, 467),
    }
    img_ends = "activity_buff-three-of-three"
    co_detect(self, None, None, img_ends, img_possibles, True)


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
