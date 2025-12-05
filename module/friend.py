import re

from core import picture, image
from core.utils import merge_nearby_coordinates
from statistics import median


def implement(self):
    self.to_main_page()
    to_friend_management(self, True)
    self.logger.info("Clear Friend White List : " + str(self.config.clear_friend_white_list))
    self.last_friend_id = None
    last_friend_id = None
    exit_cnt = 0
    while exit_cnt <= 3 and self.flag_run:
        temp = get_possible_friend_positions(self)
        temp = merge_nearby_coordinates(temp, 10)
        positions = []
        for pos in temp:
            x_coords = [coord[0] for coord in pos]
            y_coords = [coord[1] for coord in pos]
            positions.append((median(x_coords), median(y_coords)))

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
            data = get_friend_data(self, position)
            if data is False:
                continue
            need_delete = judge_need_delete(self, data)
            if not need_delete:
                if i == len(positions) - 1:
                    if last_friend_id == self.last_friend_id:
                        self.logger.info("Last Friend ID [ " + str(last_friend_id) + " ] remain same, Exit")
                        return True
                    else:
                        last_friend_id = self.last_friend_id
                continue
            else:
                delete_friend(self, position)
                need_swipe = False  # delete a friend, other id move, no need to swipe
                break
        if need_swipe:
            self.swipe(802, 635, 802, 156, 0.5, post_sleep_time=1)
        to_friend_management(self)
    return True


def to_friend_management(self, skip_first_screenshot=False):
    img_ends = "friend_friend-management-menu"
    img_possibles = {
        "friend_player-info": (903, 101),
        "friend_delete-friend-notice": (887, 165),
        "group_enter-button": (627, 383),
    }
    rgb_possibles = {"main_page": (562, 659)}
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)


def get_possible_friend_positions(self):
    return image.get_image_all_appear_position(self, "friend_delete-friend", (1067, 155, 1217, 691), 0.8)


def to_player_info(self, position):
    self.rgb_feature["friend_already_deleted"] = [[[position[0]-100, position[1]]], [[164, 184, 183, 203, 193, 213]]]
    img_ends = [
        "friend_player-info",
        "friend_delete-friend-notice"
    ]
    img_possibles = {
        "friend_friend-management-menu": (position[0] - 608, position[1] + 20)
    }
    return picture.co_detect(self, "friend_already_deleted", None, img_ends, img_possibles, skip_first_screenshot=True)

def select_player_info(self, tp):
    self.logger.info(f"Player Info To Page [ {tp} ].")
    p = {
        "profile": (538, 160),
        "progress": (718, 160),
        "assistant": (900, 160),
    }
    p = p[tp]
    img_ends = f"friend_player-info-{tp}-selected"
    img_possibles = {
        'friend_player-info-profile-selected': p,
        'friend_player-info-progress-selected': p,
        'friend_player-info-assistant-selected': p,
    }
    img_possibles.pop(img_ends)
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def get_friend_data(self, position):
    self.logger.info("Get Friend Data")
    d = {
        'id': None,
        'level': None,
        'last_login_days': None,
        'last_total_assault_rank': None
    }

    # last_login_days
    offset = {
        'CN': (-444, 14, -316, 40),
        'Global': (-444, 14, -316, 40),
        'JP': (-436, 14, -337, 40),
    }
    region = (
        position[0] + offset[self.server][0],
        position[1] + offset[self.server][1],
        position[0] + offset[self.server][2],
        position[1] + offset[self.server][3]
    )

    d['last_login_days'] = self.ocr.recognize_int(self, region, "Last Login Days")

    if to_player_info(self, position) == "friend_already_deleted":
        self.logger.info("Possibly Due to Network Delay, this friend has already been deleted, skip.")
        return False
    select_player_info(self, 'profile')
    # level
    ocr_region = {
        'CN': (607, 218, 637, 241),
        'Global': (591, 221, 662, 241),
        'JP': (594, 220, 662, 241),
    }
    d['level'] = self.ocr.recognize_int(self, ocr_region[self.server], "Level")

    # id
    ocr_region = {
        'CN': (711, 390, 796, 416),
        'Global': (711, 394, 855, 419),
        'JP': (715, 394, 855, 419),
    }
    self.last_friend_id = self.ocr.get_region_res(self, ocr_region[self.server], 'en-us', "Friend ID")
    d['id'] = self.last_friend_id

    select_player_info(self, 'progress')
    # last_total_assault_rank
    ocr_region = {
        'CN': (383, 462, 543, 498),
        'Global': (383, 462, 543, 498),
        'JP': (383, 462, 543, 498),
    }
    text = self.ocr.get_region_res(self, ocr_region[self.server], self.ocr_language, "Last Total Assault Rank")
    match = re.search(r'(\d+)', text)
    rank = 999999
    if match:
        rank = int(match.group(1))
    d['last_total_assault_rank'] = rank

    to_friend_management(self)

    self.logger.info("ID : " + self.last_friend_id)
    self.logger.info("Level : " + str(d['level']))
    self.logger.info("Last Login Days : " + str(d['last_login_days']))
    self.logger.info("Last Total Assault Rank : " + str(d['last_total_assault_rank']))
    return d

def judge_need_delete(self, friend_data):
    # Do not delete friend in white list
    _id = friend_data['id']
    if _id is not None:
        if _id in self.config.clear_friend_white_list:
            self.logger.info(f"[ {_id} ] In White List")
            return False
        self.logger.info(f"[ {_id} ] Not In White List")

    # last_login_days
    last_login_days = friend_data['last_login_days']
    _max = self.config.clear_friend_last_login_time_days
    if _max != -1 and last_login_days is not None:
        if last_login_days >= _max:
            self.logger.info(f"Last Login Days [ {last_login_days} ] >= [ {_max} ], Delete")
            return True
        else:
            self.logger.info(f"Last Login Days [ {last_login_days} ] < [ {_max} ]")

    # last_total_assault_rank
    last_rank = friend_data['last_total_assault_rank']
    _min = self.config.clear_friend_last_total_assault_rank_limit
    if _min != -1 and last_rank is not None:
        if last_rank <= _min:
            self.logger.info(f"Last Total Assault Rank [ {last_rank} ] <= [ {_min} ], Delete")
            return True
        else:
            self.logger.info(f"Last Total Assault Rank [ {last_rank} ] > [ {_min} ]")

    # level
    level = friend_data['level']
    _min_level = self.config.clear_friend_level_limit
    if _min_level != -1 and level is not None:
        if level <= _min_level:
            self.logger.info(f"Level [ {level} ] <= [ {_min_level} ], Delete")
            return True
        else:
            self.logger.info(f"Level [ {level} ] > [ {_min_level} ]")

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
