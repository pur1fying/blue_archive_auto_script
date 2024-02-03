import time
import numpy as np
from core import color, picture

def implement(self):
    # self.quick_method_to_main_page()
    to_total_assault(self, True)
    tickets = get_total_assault_tickets(self)
    self.logger.info("TICKETS: " + str(tickets))
    # if tickets == 0:
    #     self.logger.warning("NO TICKETS")
    #     return False
    maxx_name = self.config['totalForceFightDifficulty']
    self.logger.info("begin auto total assault highest difficulty: " + maxx_name)
    total_assault_difficulty_name_dict = {"NORMAL": 0, "HARD": 1, "VERYHARD": 2, "HARDCORE": 3, "EXTREME": 4, "INSANE": 5, "TORMENT": 6}
    maxx = total_assault_difficulty_name_dict[maxx_name]
    maxx = 4
    if judge_unfinished_fight(self):
        finish_existing_total_assault_task(self)
    pri_total_assault, y = total_assault_highest_difficulty_button_detection(self, maxx)
    total_assault_x = 1156
    res = fight_difficulty_x(self, pri_total_assault, y)
    tickets -= 1
    win = False
    while res == "WIN" and pri_total_assault != len(self.total_assault_difficulty_name) - 1 and tickets > 0:
        win = True
        if pri_total_assault == maxx:
          break
        pri_total_assault += 1
        res = fight_difficulty_x(self, pri_total_assault)

    while (res == "LOSE" or res == "UNLOCK") and pri_total_assault >= 0 and win == False and tickets > 0:
        if res == "LOSE":
            give_up_current_fight(self)
        pri_total_assault -= 1
        t = fight_difficulty_x(self, pri_total_assault)


    if pri_total_assault == -1:  # normal打不过
        self.logger.info("打不过NORMAL, 快找爱丽丝邦邦 QAQ")
        return True

    if tickets > 0:
        sweep(self)

    collect_season_reward(self)


def find_button_y(self, y):
    self.logger.info("start FIND BUTTON FOR difficulty " + self.total_assault_difficulty_name_ordered[y])
    for try_cnt in range(0, 3):
        img = self.get_screenshot_array()
        img = img_crop(img, 661, 811, 0, 720)
        ocr_res = temp_ocr.ocr(img)

        for i in range(0, len(ocr_res)):
            if kmp(self.total_assault_difficulty_name_ordered[y].lower(), ocr_res[i]["text"].lower()):
                return ocr_res[i]["position"][3][1]

        self.logger.info("SWIPE DOWNWARDS")
        self.swipe", [(950, 590), (950, 330)], duration=0.1)
        time.sleep(2)

        for i in range(0, len(ocr_res)):
            if kmp(self.total_assault_difficulty_name[y].lower(), ocr_res[i]["text"].lower()):
                return ocr_res[i]["position"][3][1]

        if try_cnt != 3:
            self.logger.info("SWIPE UPWARDS")
            self.swipe", [(950, 330), (950, 590)], duration=0.1)
            time.sleep(2)

    self.logger.info("CAN'T DETECT BRIGHT BUTTON FOR LEVEL " + self.total_assault_difficulty_name_ordered[y], 3,
          logger_box=self.loggerBox)
    return False


def fight_difficulty_x(self, x, temp_ocr):
    total_assault_x = 1156
    self.logger.info("###################################################################################", 1,
          logger_box=self.loggerBox)
    self.logger.info("start total force fight difficulty : " + self.total_assault_difficulty_name_ordered[x], 1,
          logger_box=self.loggerBox)
    self.stop_getting_screenshot_for_location")
    total_assault_y = find_button_y(self, x, temp_ocr)
    if not total_assault_y:
        self.logger.info("FAIL")
        self.logger.info("###################################################################################", 1,
              logger_box=self.loggerBox)
        return False
    self.logger.info("SUCCESS")

    self.start_getting_screenshot_for_location")
    for i in range(0, 4):
        formation_x = 64
        formation_y = [198, 274, 353, 426]
        if i == 0:
            self.click(total_assault_x, total_assault_y), duration=self.screenshot_interval * 2)
            self.common_positional_bug_detect_method("detailed_message", total_assault_x, total_assault_y,
                                                     times=4, anywhere=True)
            self.click(1015, 524), 4)
            lo = self.get_current_position")
            if not lo:
                return False
            if lo == "notice":
                self.logger.info("TICKET INADEQUATE QUIT TOTAL FORCE FIGHT TASK", 2, logger_box=self.loggerBox)
                return "NO_TICKETS"
            elif lo == "attack_formation":
                time.sleep(1)
                self.logger.info("choose formation : " + str(i + 1) + " and start fight")
                self.click(formation_x, formation_y[0]), duration=1)
                self.click(1157, 666), duration=1)
                self.click(770, 500))
                ####
            elif lo == "total_assault":
                self.logger.info("CURRENT difficulty UNLOCK, try LOWER difficulty")
                return "UNLOCK"
            else:
                self.logger.info("UNEXPECTED PAGE", 3, logger_box=self.loggerBox)
                return "UNEXPECTED_PAGE"
        else:
            flag = False
            for j in range(0, 4):
                path = "src/total_assault/enter_again.png"
                return_data = self.get_x_y(self.latest_img_array, path)
                print(return_data)
                if return_data[1][0] <= 1e-03:
                    flag = True
                    self.click(return_data[0][0], return_data[0][1]), duration=1)
                    self.click(1015, 524))
                    if not self.common_positional_bug_detect_method("attack_formation", 1015, 524):
                        return "UNEXPECTED_PAGE"
                    self.logger.info("choose formation " + str(i + 1) + " and start fight")
                    self.click(formation_x, formation_y[i]), duration=1)
                    self.click(1157, 666))
                    break
                else:
                    time.sleep(1)
            if not flag:
                return "UNEXPECTED_PAGE"

        res = self.common_fight_practice()
        if not res:
            self.logger.info("total force fight attempt " + str(i + 1) + " FAILED")
            if not self.common_icon_bug_detect_method("src/total_assault/total_assault_page.png", 382, 22,
                                                      "total_assault", 10):
                return False
        if res:
            self.logger.info("total force fight SUCCEEDED", level=1, logger_box=self.loggerBox)
            self.common_icon_bug_detect_method("src/total_assault/total_assault_page.png", 382, 22,
                                               "total_assault", 10)
            self.logger.info("###################################################################################", 1,
                  logger_box=self.loggerBox)
            return "WIN"
    self.logger.info("4 attempts ALL FAILED")
    self.logger.info("###################################################################################", 1,
          logger_box=self.loggerBox)
    return "LOSE"


def finish_existing_total_assault_task(self):
    self.logger.info("-- continue EXISTING fight --")
    to_room_info(self, (1157, 219), True)
    unable_to_fight_formation = np.full(4, False, dtype=bool)
    for i in range(0, 4):
        to_formation_edit_i(self, i + 1, (1021, 530), True)
        for j in range(0, 4):
            if not unable_to_fight_formation[j]:
                unable_to_fight_formation[j] = True
                self.logger.info("detect formation " + str(j + 1))
                to_formation_edit_i(self, j + 1, (1021, 530), True)
                if not judge_formation_usable(self):
                    self.logger.info("FORMATION " + str(j + 1) + " UNUSABLE")
                    break
                self.logger.info("CONTINUE with FORMATION " + str(j + 1))
                self.click(1160, 666)
                res = self.common_fight_practice()
                if not res:
                    self.logger.info("total force fight attempt FAILED")
                if res:
                    self.logger.info("total force fight SUCCEEDED")
                    return "WIN"
                break
        if unable_to_fight_formation.all():
            self.logger.info("0 USABLE FORMATION")
            self.logger.info("GIVE UP current fight")
            self.click(x, y, duration=1)
            self.click(800, 533, duration=1)
            self.click(800, 500, duration=3)
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
        self.swipe(950, 590, 950, 330, duration=0.1)
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()
        res, button_detected = one_detect(self, button_detected, maxx, character_dict)
        if res != "NOT_FOUND":
            return res
        if try_cnt != 3:
            self.logger.info("SWIPE UPWARDS")
            self.swipe(950, 330, 950, 590, duration=0.1)
            time.sleep(1)
            self.latest_img_array = self.get_screenshot_array()


def judge_unfinished_fight(self):
    if color.judge_rgb_range(self.latest_img_array, 1105, 206, 131, 121, 218, 238, 245, 255) and color.judge_rgb_range(
            self.latest_img_array, 1109, 252, 131, 121, 218, 238, 245, 255):
        return True
    self.logger.info("NO UNFINISHED FIGHT")
    return False


# def collect_point_reward(self):
#     to_total_assault_info(self, True)
#     if return_data1[1][0] <= 1e-03:
#         self.logger.info("collect TOTAL FORCE FIGHT ACCUMULATED POINTS REWARD")
#         self.click(return_data1[0][0], return_data1[0][1]), duration=2)
#         self.click(1240, 40))
#         self.click(1240, 40))
#         self.click(1240, 40))
#     elif return_data2[1][0] <= 1e-03:
#         self.logger.info("NO ACCUMULATED POINTS REWARD can be collected")
#         self.click(1240, 40))
#         self.click(1240, 40))
#     else:
#         self.logger.info("CAN'T DETECT BUTTON", 3, logger_box=self.loggerBox)
#         return False
#     return True


def collect_season_reward(self):
    to_total_assault_info(self, True)
    self.click(1184, 657, duration=2)
    self.click(917, 163, duration=0.5)
    self.click(237, 303, duration=0.3)


def to_total_assault(self, skip_first_screenshot):
    rgb_possibles = {"main_page": (1193, 572)}
    img_possibles = {
        "main_page_bus": (922, 447),
        "total_assault_battle-fail-confirm": (577, 636),
        "total_assault_battle-win-confirm": (1144, 649),
    }
    img_ends = "total_assault_menu"
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
    y = loy[i - 1]
    rgb_ends = "formation_edit" + str(i)
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_possibles.pop("formation_edit" + str(i))
    img_possibles = {"total_assault_room-info": lo}
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def judge_formation_usable(self):
    regions = [(223, 432, 1087, 461), (283, 674, 376, 696), (634, 674, 727, 696)]
    word = {
        'CN': ['无', '法', '作', '战'],
        'Global': ['U', 'N', 'U', 'S', 'A', 'B', 'L', 'E'],
        'JP': ['参','加', '不', '可'],
    }
    mode = {
        'CN': 'CN',
        'Global': 'Global',
        'JP': 'CN',
    }
    for k in range(0, 3):
        for region in regions:
            time.sleep(1)
            self.latest_img_array = self.get_screenshot_array
            ocr_res = self.ocr.get_region_res(self.latest_img_array, region, mode[self.server])
            return False
    return True


def get_total_assault_tickets(self):
    region = {
        'CN': (943, 111, 979, 135),
        'Global': (1100, 0, 1280, 40),
        'JP': (1100, 0, 1280, 40),
    }
    res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global')
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
    ocr_res = self.ocr.get_region_raw_res(self.latest_img_array, region, "Global")
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
                y = int(ocr_res[j]["position"][3][1]) + region[1]
                if color.judge_rgb_range(self.latest_img_array, 1163, y, 235, 255, 223, 243, 65, 85):
                    temp = 0
                self.logger.info("find " + self.total_assault_difficulty_names[maximum_acc_index].upper() + " " + name[temp] + " button")
                if maximum_acc_index >= maxx and temp == 0:
                    return (maxx, y), button_detected
                button_detected[maximum_acc_index][temp] = True
                t = total_assault_highest_difficulty_button_judgement(button_detected)
                if isinstance(t, int):
                    return (t, y), button_detected
    return "NOT_FOUND", button_detected


def give_up_current_fight(self):
    to_room_info(self, (1157, 219), True)
