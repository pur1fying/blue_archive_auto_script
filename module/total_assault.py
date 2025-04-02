import time

import numpy as np

from core import color, picture
from module import main_story


def implement(self):
    self.logger.info("Total Assault is Disabled")
    return True
    self.to_main_page()
    to_total_assault(self, True)
    tickets = get_total_assault_tickets(self)
    self.logger.info("TICKETS: " + str(tickets))
    if tickets == 0:
        self.logger.warning("NO TICKETS")
        return True
    maxx_name = self.config.totalForceFightDifficulty
    self.logger.info("begin auto total assault highest difficulty: " + maxx_name)
    total_assault_difficulty_name_dict = {"NORMAL": 0, "HARD": 1, "VERYHARD": 2, "HARDCORE": 3, "EXTREME": 4,
                                          "INSANE": 5, "TORMENT": 6}
    maxx = total_assault_difficulty_name_dict[maxx_name]
    if judge_unfinished_fight(self):
        finish_existing_total_assault_task(self)
    pri_total_assault, y = total_assault_highest_difficulty_button_detection(self, maxx)
    res = fight_difficulty_x(self, pri_total_assault, y)
    max_sweepable = -1
    if res == "NO_TICKETS":
        tickets = 0
    else:
        tickets -= 1
        while res == "WIN" and pri_total_assault != len(self.total_assault_difficulty_names) - 2 and tickets > 0 and self.flag_run:
            max_sweepable = pri_total_assault
            if pri_total_assault == maxx:
                break
            pri_total_assault += 1
            res = fight_difficulty_x(self, pri_total_assault)
            if res == "WIN":
                max_sweepable = pri_total_assault

        while res == "LOSE" and pri_total_assault >= 0 and tickets > 0 and self.flag_run:
            give_up_current_fight(self)
            pri_total_assault -= 1
            res = fight_difficulty_x(self, pri_total_assault)
            if res == "WIN":
                max_sweepable = pri_total_assault
                break

    if pri_total_assault == -1:
        self.logger.critical("打不过NORMAL, 快找爱丽丝邦邦 QAQ")
        return True

    if tickets > 0 and max_sweepable != -1:
        start_sweep(self, max_sweepable, tickets)

    collect_season_reward(self)
    collect_accumulated_point_reward(self)
    return True


def find_button_y(self, y):
    self.logger.info("start FIND BUTTON FOR difficulty " + self.total_assault_difficulty_names[y])
    target_dict = {}
    temp = self.total_assault_difficulty_names[y].lower()
    for i in range(0, len(temp)):
        target_dict.setdefault(temp[i], 0)
        target_dict[temp[i]] += 1
    while self.flag_run:
        res = detect_level_y(self, target_dict)
        if res != "NOT_FOUND":
            return res
        self.logger.info("SWIPE DOWNWARDS")
        self.swipe(950, 590, 950, 0, duration=0.1, post_sleep_time=1)
        self.latest_img_array = self.get_screenshot_array()
        res = detect_level_y(self, target_dict)
        if res != "NOT_FOUND":
            return res
        self.logger.info("SWIPE UPWARDS")
        self.swipe(950, 168, 950, 720, duration=0.1, post_sleep_time=1)
        self.latest_img_array = self.get_screenshot_array()


def fight_difficulty_x(self, level, y_for_x=0):
    self.logger.info("start total force fight difficulty : " + self.total_assault_difficulty_names[level])
    if y_for_x == 0:
        y_for_x = find_button_y(self, level)
    for i in range(0, 4):
        self.logger.info("choose formation : " + str(i + 1) + " and start fight")
        to_room_info(self, (1156, y_for_x if i == 0 else 219), True)
        res = to_formation_edit_i(self, i, (1019, 524), True)
        if res == "total_assault_inadequate-ticket":
            self.logger.warning("TICKET INADEQUATE QUIT auto total assault")
            to_total_assault(self, True)
            return "NO_TICKETS"
        enter_fight(self)
        main_story.auto_fight(self, True if i == 0 else False)
        res = get_fight_result(self)
        to_total_assault(self, True)
        if res == "total_assault_battle-lost-confirm":
            self.logger.info("total force fight attempt " + str(i + 1) + " FAILED")
        if res == "total_assault_battle-win-confirm":
            self.logger.info("total assault auto fight SUCCEEDED")
            return "WIN"
    self.logger.info("4 attempts ALL FAILED")
    return "LOSE"


def finish_existing_total_assault_task(self):
    self.logger.info("-- continue EXISTING fight --")
    to_room_info(self, (1157, 219), True)
    unable_to_fight_formation = np.full(4, False, dtype=bool)
    for i in range(0, 4):
        for j in range(0, 4):
            if not unable_to_fight_formation[j]:
                unable_to_fight_formation[j] = True
                self.logger.info("detect formation " + str(j + 1))
                to_formation_edit_i(self, j, (1021, 530), True)
                if not judge_formation_usable(self):
                    self.logger.info("FORMATION " + str(j + 1) + " UNUSABLE")
                    break
                self.logger.info("CONTINUE with FORMATION " + str(j + 1))
                enter_fight(self)
                main_story.auto_fight(self, True)
                res = get_fight_result(self)
                to_total_assault(self, True)
                if res == "total_assault_battle-lost-confirm":
                    self.logger.info("total assault FAILED")
                if res == "total_assault_battle-win-confirm":
                    self.logger.info("total assault auto fight SUCCEEDED")
                    return "WIN"
        if unable_to_fight_formation.all():
            self.logger.info("0 USABLE FORMATION")
            give_up_current_fight(self)
            return "GIVE_UP_FIGHT"


def total_assault_highest_difficulty_button_judgement(button_detected):
    if button_detected[len(button_detected) - 1][0]:
        return len(button_detected) - 1
    for i in range(0, len(button_detected) - 1):
        if button_detected[i][0] and button_detected[i + 1][1]:
            return i
    return "NOT_FOUND"


def total_assault_highest_difficulty_button_detection(self, maxx):
    self.logger.info("detect HIGHEST UNLOCK LEVEL")
    button_detected = np.full([len(self.total_assault_difficulty_names), 2], False, dtype=bool)
    character_dict = []
    for i in range(0, len(self.total_assault_difficulty_names)):
        temp = self.total_assault_difficulty_names[i].lower()
        character_dict.append({})
        for j in range(0, len(temp)):
            character_dict[i].setdefault(temp[j], 0)
            character_dict[i][temp[j]] += 1
    for try_cnt in range(0, 3):
        res, button_detected = one_detect(self, button_detected, maxx, character_dict)
        if res != "NOT_FOUND":
            return res
        self.logger.info("SWIPE DOWNWARDS")
        self.swipe(950, 590, 950, 0, duration=0.1, post_sleep_time=1)
        self.latest_img_array = self.get_screenshot_array()
        res, button_detected = one_detect(self, button_detected, maxx, character_dict)
        if res != "NOT_FOUND":
            return res
        if try_cnt != 3:
            self.logger.info("SWIPE UPWARDS")
            self.swipe(950, 168, 950, 720, duration=0.1, post_sleep_time=1)
            self.latest_img_array = self.get_screenshot_array()


def judge_unfinished_fight(self):
    if color.rgb_in_range(self, 1105, 206, 131, 151, 218, 238, 245, 255) and color.rgb_in_range(
        self.latest_img_array, 1109, 252, 131, 151, 218, 238, 245, 255):
        return True
    self.logger.info("NO UNFINISHED FIGHT")
    return False


def collect_accumulated_point_reward(self):
    self.logger.info("collect accumulated point reward")
    to_total_assault_info(self, False)
    rgb_possibles = {
        'total_assault_rank_info': (928, 162),
        'total_assault_accumulated_point_reward': (241, 238),
        'reward_acquired': (640, 100),
    }
    rgb_ends = "total_assault_rank_reward"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, None, True)
    judge_and_collect_reward(self)


def collect_season_reward(self):
    self.logger.info("collect season reward")
    to_total_assault_info(self, True)
    rgb_possibles = {
        'total_assault_rank_info': (928, 162),
        'total_assault_rank_reward': (241, 311),
        'reward_acquired': (640, 100),
    }
    rgb_ends = "total_assault_accumulated_point_reward"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, None, True)
    judge_and_collect_reward(self)


def judge_and_collect_reward(self):
    if color.rgb_in_range(self, 962, 558, 213, 233, 213, 233, 213, 233):
        self.logger.info("need not collect")
        return False
    self.logger.info("collect")
    self.click(1054, 580, duration=1, wait_over=True)


def to_total_assault(self, skip_first_screenshot):
    rgb_possibles = {"main_page": (1193, 572)}
    totalAssaultIconLocation = {
        'CN': (922, 447),
        'Global': (922, 447),
        'JP': (879, 441),
    }
    img_possibles = {
        "main_page_bus": totalAssaultIconLocation[self.server],
        "total_assault_battle-lost-confirm": (640, 636),
        "total_assault_battle-win-confirm": (1144, 649),
        "total_assault_room-info": (1123, 168),
        'total_assault_inadequate-ticket': (886, 162),
        'total_assault_edit-force': (62, 38),
        'total_assault_total-assault-result': (640, 568),
        'total_assault_win-reward-confirm': (772, 659),
        "total_assault_reach-season-highest-record":(640, 528),
        "normal_task_sweep-complete": (643, 585),
        'normal_task_skip-sweep-complete': (643, 506),
    }
    img_ends = "total_assault_menu"
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_room_info(self, lo, skip_first_screenshot):
    img_possibles = {"total_assault_menu": lo}
    img_ends = "total_assault_room-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_total_assault_info(self, skip_first_screenshot):
    img_possibles = {"total_assault_menu": (1174, 636)}
    img_ends = "total_assault_total-assault-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_formation_edit_i(self, i, lo, skip_first_screenshot=False):
    loy = [195, 275, 354, 423]
    y = loy[i]
    rgb_ends = "formation_edit" + str(i + 1)
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_possibles.pop("formation_edit" + str(i + 1))
    img_ends = "total_assault_inadequate-ticket"
    img_possibles = {"total_assault_room-info": lo}
    return picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def judge_formation_usable(self):
    regions = [(223, 432, 1087, 461), (283, 674, 376, 696), (634, 674, 727, 696)]
    word = {
        'CN': ['无', '法', '作', '战'],
        'Global': ['u', 'n', 'u', 's', 'a', 'b', 'l', 'e'],
        'JP': ['参', '加', '不', '可'],
    }
    mode = {
        'CN': 'CN',
        'Global': 'Global',
        'JP': 'CN',
    }
    for k in range(0, 3):
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()
        for region in regions:
            ocr_res = self.ocr.get_region_res(self.latest_img_array, region, mode[self.server], self.ratio)
            cnt = 0
            for j in range(0, len(ocr_res)):
                if ocr_res[j].lower() in word[self.server]:
                    cnt += 1
            if cnt >= len(word[self.server]) / 2:
                return False
    return True


def get_total_assault_tickets(self):
    region = (943, 111, 979, 135)
    res = self.ocr.get_region_res(self.latest_img_array, region, 'Global', self.ratio)
    if res[0].isdigit():
        return int(res[0])
    return 3


def calc_acc(dict1, dict2):
    judge = 0
    cnt = 0
    temp = dict2.copy()
    for key in dict1:
        cnt += dict1[key]
        if key in temp:
            judge += temp[key]
            temp[key] -= dict1[key]
    for key in temp:
        judge -= abs(temp[key])
    return judge / cnt


def one_detect(self, button_detected, maxx, character_dict):
    name = ["BRIGHT", "GREY"]
    region = (661, 161, 833, 608)
    y = np.zeros(len(self.total_assault_difficulty_names), dtype=int)
    ocr_res = self.ocr.get_region_raw_res(self.latest_img_array, region, "Global", self.ratio)
    for i in range(0, len(button_detected)):
        if button_detected[i].any():
            continue
        for j in range(0, len(ocr_res)):
            text = ocr_res[j]["text"].lower()
            text_dict = {}
            acc = []
            for k in range(0, len(text)):
                text_dict.setdefault(text[k], 0)
                text_dict[text[k]] += 1
            for k in range(0, len(button_detected)):
                acc.append(calc_acc(character_dict[k], text_dict))
            maximum_acc_index = acc.index(max(acc))
            if acc[maximum_acc_index] > 0.8 and (not button_detected[maximum_acc_index].any()):
                temp = 1
                y[maximum_acc_index] = int(ocr_res[j]["position"][3][1]/self.ratio) + region[1]
                if color.rgb_in_range(self, 1163, y[maximum_acc_index], 235, 255, 223, 243, 65, 85):
                    temp = 0
                self.logger.info("find " + self.total_assault_difficulty_names[maximum_acc_index].upper() + " " + name[
                    temp] + " button")
                if maximum_acc_index >= maxx and temp == 0:
                    return (maxx, y[maxx]), button_detected
                button_detected[maximum_acc_index][temp] = True
                t = total_assault_highest_difficulty_button_judgement(button_detected)
                if isinstance(t, int):
                    return (t, y[t]), button_detected
    return "NOT_FOUND", button_detected


def give_up_current_fight(self):
    self.logger.info("give up current fight")
    to_room_info(self, (1157, 219), True)
    img_possibles = {
        "total_assault_room-info": (821, 522),
        "total_assault_give-up-notice": (766, 501),
    }
    img_ends = "total_assault_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def detect_level_y(self, target_dict):
    region = (661, 161, 833, 608)
    ocr_res = self.ocr.get_region_raw_res(self.latest_img_array, region, "Global", self.ratio)
    for i in range(0, len(ocr_res)):
        temp = ocr_res[i]["text"].lower()
        ocr_dict = {}
        for j in range(0, len(temp)):
            ocr_dict.setdefault(temp[j], 0)
            ocr_dict[temp[j]] += 1
        acc = calc_acc(target_dict, ocr_dict)
        if acc > 0.8:
            return int(ocr_res[i]["position"][3][1]) + region[1]
    return "NOT_FOUND"


def enter_fight(self):
    img_possibles = {
        "total_assault_enter-fight-without-further-editing-notice": (767, 498),
        "total_assault_use-ticket-notice": (767, 498),
        "total_assault_edit-force": (1159, 654),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519),
    }
    rgb_ends = 'fighting_feature'
    rgb_possibles = {
        "formation_edit1": (1159, 654),
        "formation_edit2": (1159, 654),
        "formation_edit3": (1159, 654),
        "formation_edit4": (1159, 654),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)


def get_fight_result(self):
    img_ends = [
        "total_assault_battle-lost-confirm",
        "total_assault_battle-win-confirm"
    ]
    return picture.co_detect(self, None, None, img_ends)


def start_sweep(self, pri_total_assault, tickets):
    self.logger.info("SWEEP :" + str(pri_total_assault) + " " + str(tickets) + " times")
    y = find_button_y(self, pri_total_assault)
    to_room_info(self, (1157, y), True)
    if tickets >= 2:
        self.click(1069, 297, wait_over=True,  duration=0.1, count=tickets-1)
    img_ends = [
        "total_assault_inadequate-ticket",
        "normal_task_start-sweep-notice",
    ]
    img_possibles = {"total_assault_room-info": (941, 411)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, True)
    if res != "total_assault_inadequate-ticket":
        img_ends = [
            "normal_task_skip-sweep-complete",
            "normal_task_sweep-complete",
        ]
        img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
        picture.co_detect(self, None,None, img_ends, img_possibles, True)
    to_total_assault(self, True)
