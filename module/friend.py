import time

from core import picture, color


def implement(self):
    if self.server == 'Global' or self.server == 'JP':
        self.logger.info("Friend Management Not Support In Global And JP Server")
        return True
    self.quick_method_to_main_page()
    to_friend_management(self, True)
    self.logger.info("Clear Friend White List : + " + str(self.config.get("clear_friend_white_list")))
    self.last_friend_id = None
    last_friend_id = None
    exit_cnt = 0
    checked_position = 0
    while exit_cnt <= 3 and self.flag_run:
        positions = get_possible_friend_positions(self)
        if len(positions) == 0:
            self.logger.info("No Friend Found")
            exit_cnt += 1
            to_friend_management(self)
            continue
        exit_cnt = 0
        self.logger.info("Friend Found At : " + str(positions))
        need_swipe = True
        for i in range(0, len(positions)):
            position = positions[i]
            if position[1] < checked_position + 10:
                self.logger.info("Position : " + str(position[1]) + "already checked, Skip")
                continue
            res = to_player_info(self, position)
            if res == "friend_delete-friend-notice":
                self.logger.info("UI AT delete friend notice, Skip")
                continue
            in_white_list = check_name_in_white_list(self)
            to_friend_management(self)
            if in_white_list:
                if i == len(positions) - 1:
                    if last_friend_id == self.last_friend_id:
                        self.logger.info("Last Friend ID : " + str(last_friend_id) + " remain same, Exit")
                        return True
                    else:
                        last_friend_id = self.last_friend_id
                checked_position = position[1]
                continue
            else:
                delete_position = (1128, position[1] + 85)
                delete_friend(self, delete_position)
                need_swipe = False  # delete a friend, other id move, no need to swipe
                break
        if need_swipe:
            self.swipe(802, 635, 802, 156, 0.5, post_sleep_time=1)
            checked_position = 0
        to_friend_management(self)
    return True


def to_friend_management(self, skip_first_screenshot=False):
    img_ends = "friend_friend-management-menu"
    img_possibles = {
        "friend_friend-menu": (579, 374),
        "main_page_menu": (537, 467),
        "friend_player-info": (903, 101),
        "friend_delete-friend-notice": (887, 165),
        "group_enter-button": (627, 383),
    }
    main_page_click_position = {
        'CN': (1226, 39),
        'Global': (562, 659),
        'JP': (562, 659)
    }
    rgb_possibles = {"main_page": main_page_click_position[self.server]}
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)


def get_possible_friend_positions(self):
    funcs = {
        'CN': search_cn,
        'Global': search_global,
        'JP': search_jp
    }
    return funcs[self.server](self)


def search_cn(self):
    found_list = []
    i = 157
    x = 1183
    while i < 595:
        if color.judge_rgb_range(self, x, i, 34, 54, 60, 80, 88, 108):
            found_list.append((1183, i))
            i += 50
        else:
            i += 1
    return found_list


def search_global(self):
    found_list = []
    i = 157
    x = 487
    while i < 595:
        if color.judge_rgb_range(self, x, i, 250, 255, 250, 255, 250, 255) and color.judge_rgb_range(self, x, i + 18, 250, 255, 250, 255, 250, 255):
            found_list.append((493, i + 9))
            i += 50
        else:
            i += 1
    return found_list


def search_jp(self):
    found_list = []
    i = 157
    x = 487
    while i < 595:
        if color.judge_rgb_range(self, x, i, 250, 255, 250, 255, 250, 255) and color.judge_rgb_range(self, x, i + 18, 250, 255, 250, 255, 250, 255):
            found_list.append((493, i + 9))
            i += 50
        else:
            i += 1
    return found_list


def to_player_info(self, position):
    img_ends = [
        "friend_player-info",
        "friend_delete-friend-notice"
    ]
    img_possibles = {
        "friend_friend-management-menu": position
    }
    return picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def check_name_in_white_list(self):
    ocr_region = {
        'CN': (680, 385, 747, 409),
        'Global': (711, 394, 823, 419),
        'JP': (680, 385, 747, 409),
    }
    white_list = self.config.get("clear_friend_white_list")
    friend_id = self.ocr.get_region_res(self.latest_img_array, ocr_region[self.server], 'Global', self.ratio)
    self.last_friend_id = friend_id
    self.logger.info("Ocr Friend ID : [ " + friend_id + " ]")
    if friend_id in white_list:
        self.logger.info("Friend ID [ " + friend_id + " ] In White List")
        return True
    self.logger.info("Friend ID [ " + friend_id + " ] Not In White List")
    return False


def delete_friend(self, position):
    self.logger.info("Delete Friend At : " + str(position))
    img_ends = "friend_delete-friend-notice"
    img_possibles = {
        "friend_friend-management-menu": position
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)
    img_ends = "friend_friend-management-menu"
    img_possibles = {
        "friend_delete-friend-notice": (761, 499)
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)
