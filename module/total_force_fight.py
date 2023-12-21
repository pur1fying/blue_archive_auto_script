import time
from core.utils import get_x_y, kmp, img_crop
from gui.util import log
import numpy as np
from cnocr import CnOcr

from datetime import datetime


def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    next_time = datetime(year, month, day + 1, 4)
    return next_time.timestamp()


def find_button_y(self, y, temp_ocr):
    log.d("START FIND BUTTON FOR LEVEL " + self.total_force_fight_difficulty_name_ordered[y], 1,
          logger_box=self.loggerBox)
    for try_cnt in range(0, 3):
        img = self.operation("get_screenshot_array")
        img = img_crop(img, 661, 811, 0, 720)
        ocr_res = temp_ocr.ocr(img)

        for i in range(0, len(ocr_res)):
            if kmp(self.total_force_fight_difficulty_name_ordered[y].lower(), ocr_res[i]["text"].lower()):
                return ocr_res[i]["position"][3][1]

        log.d("SWIPE DOWNWARDS", 1, logger_box=self.loggerBox)
        self.operation("swipe", [(950, 590), (950, 330)], duration=0.1)
        time.sleep(2)

        for i in range(0, len(ocr_res)):
            if kmp(self.total_force_fight_difficulty_name[y].lower(), ocr_res[i]["text"].lower()):
                return ocr_res[i]["position"][3][1]

        if try_cnt != 3:
            log.d("SWIPE UPWARDS", 1, logger_box=self.loggerBox)
            self.operation("swipe", [(950, 330), (950, 590)], duration=0.1)
            time.sleep(2)

    log.d("CAN'T DETECT BRIGHT BUTTON FOR LEVEL " + self.total_force_fight_difficulty_name_ordered[y], 3,
          logger_box=self.loggerBox)
    return False


def fight_difficulty_x(self, x, temp_ocr):
    total_force_fight_x = 1156
    log.d("###################################################################################", 1,
          logger_box=self.loggerBox)
    log.d("start total force fight difficulty : " + self.total_force_fight_difficulty_name_ordered[x], 1,
          logger_box=self.loggerBox)
    self.operation("stop_getting_screenshot_for_location")
    total_force_fight_y = find_button_y(self, x, temp_ocr)
    if not total_force_fight_y:
        log.d("FAIL", 1, logger_box=self.loggerBox)
        log.d("###################################################################################", 1,
              logger_box=self.loggerBox)
        return False
    log.d("SUCCESS", 1, logger_box=self.loggerBox)

    self.operation("start_getting_screenshot_for_location")
    for i in range(0, 4):
        formation_x = 64
        formation_y = [198, 274, 353, 426]
        if i == 0:
            self.operation("click", (total_force_fight_x, total_force_fight_y), duration=self.screenshot_interval * 2)
            self.common_positional_bug_detect_method("detailed_message", total_force_fight_x, total_force_fight_y,
                                                     times=4, anywhere=True)
            self.operation("click", (1015, 524), 4)
            lo = self.operation("get_current_position")
            if not lo:
                return False
            if lo == "notice":
                log.d("TICKET INADEQUATE QUIT TOTAL FORCE FIGHT TASK", 2, logger_box=self.loggerBox)
                return "NO_TICKETS"
            elif lo == "attack_formation":
                time.sleep(1)
                log.d("choose formation : " + str(i + 1) + " and start fight", 1, logger_box=self.loggerBox)
                self.operation("click", (formation_x, formation_y[0]), duration=1)
                self.operation("click", (1157, 666), duration=1)
                self.operation("click", (770, 500))
                ####
            elif lo == "total_force_fight":
                log.d("CURRENT difficulty UNLOCK, try LOWER difficulty", 1, logger_box=self.loggerBox)
                return "UNLOCK"
            else:
                log.d("UNEXPECTED PAGE", 3, logger_box=self.loggerBox)
                return "UNEXPECTED_PAGE"
        else:
            flag = False
            for j in range(0, 4):
                path = "src/total_force_fight/enter_again.png"
                return_data = self.get_x_y(self.latest_img_array, path)
                print(return_data)
                if return_data[1][0] <= 1e-03:
                    flag = True
                    self.operation("click", (return_data[0][0], return_data[0][1]), duration=1)
                    self.operation("click", (1015, 524))
                    if not self.common_positional_bug_detect_method("attack_formation", 1015, 524):
                        return "UNEXPECTED_PAGE"
                    log.d("choose formation " + str(i + 1) + " and start fight", 1, logger_box=self.loggerBox)
                    self.operation("click", (formation_x, formation_y[i]), duration=1)
                    self.operation("click", (1157, 666))
                    break
                else:
                    time.sleep(1)
            if not flag:
                return "UNEXPECTED_PAGE"

        res = self.common_fight_practice()
        if not res:
            log.d("total force fight attempt " + str(i + 1) + " FAILED", 1, logger_box=self.loggerBox)
            if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382, 22,
                                                      "total_force_fight", 10):
                return False
        if res:
            log.d("total force fight SUCCEEDED", level=1, logger_box=self.loggerBox)
            self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382, 22,
                                               "total_force_fight", 10)
            log.d("###################################################################################", 1,
                  logger_box=self.loggerBox)
            return "WIN"
    log.d("4 attempts ALL FAILED", 1, logger_box=self.loggerBox)
    log.d("###################################################################################", 1,
          logger_box=self.loggerBox)
    return "LOSE"


def judge_and_finish_unfinished_total_force_fight_task(self):
    log.d("BEGIN JUDGE UNFINISHED FIGHT", 1, logger_box=self.loggerBox)
    y = 225
    x = 1156
    formation_x = 64
    formation_y = [198, 274, 353, 426]
    unable_to_fight_formation = np.full(4, False, dtype=bool)
    ocr_res = self.img_ocr(self.latest_img_array)
    if kmp("再次入场", ocr_res) > 0 or kmp("正在进行", ocr_res) > 0:
        log.d("*****************************************************************************************", 1,
              logger_box=self.loggerBox)
        log.d("[CONTINUE UNSOLVED FIGHT]", 1, logger_box=self.loggerBox)
        for i in range(0, 4):  # 四个队伍
            self.operation("click", (x, y), duration=1)
            self.operation("click", (1012, 525))
            if not self.common_positional_bug_detect_method("attack_formation", 1012, 525, times=4, anywhere=True):
                return "UNEXPECTED_PAGE"
            else:
                for j in range(0, 4):  # 四个队伍
                    if not unable_to_fight_formation[j]:  # 检测能不能打
                        log.d("detect formation " + str(j + 1), 1, logger_box=self.loggerBox)
                        self.operation("click", (formation_x, formation_y[j]))
                        for k in range(0, 3):
                            time.sleep(1)
                            self.latest_img_array = self.operation("get_screenshot_array")
                            ocr_res = self.img_ocr(self.latest_img_array)
                            print(ocr_res)
                            if kmp("无法", ocr_res) > 0:
                                log.d("FORMATION " + str(j + 1) + " UNUSABLE", 1, logger_box=self.loggerBox)
                                unable_to_fight_formation[j] = True
                                break
                    if not unable_to_fight_formation[j]:
                        unable_to_fight_formation[j] = True
                        log.d("CONTINUE with FORMATION " + str(j + 1), 1, logger_box=self.loggerBox)
                        self.operation("click", (1160, 666), duration=4)
                        res = self.common_fight_practice()
                        if not res:
                            log.d("total force fight attempt FAILED", 1, logger_box=self.loggerBox)
                        if res:
                            log.d("total force fight SUCCEEDED", level=1, logger_box=self.loggerBox)
                            log.d(
                                "*****************************************************************************************",
                                1,
                                logger_box=self.loggerBox)
                            self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382,
                                                               22,
                                                               "total_force_fight", 10)
                            return "WIN"
                        break
                if unable_to_fight_formation.all():
                    log.d("NO USABLE FORMATION", 1, logger_box=self.loggerBox)
                    log.d("*****************************************************************************************",
                          1,
                          logger_box=self.loggerBox)
                    if not self.common_positional_bug_detect_method("total_force_fight", 61, 40, times=4, ):
                        return "UNEXPECTED_PAGE"
                    else:
                        log.d("GIVE UP CURRENT FIGHT", 1, logger_box=self.loggerBox)
                        self.operation("click", (x, y), duration=1)
                        self.operation("click", (800, 533), duration=1)
                        self.operation("click", (800, 500), duration=3)
                        if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png",
                                                                  382, 22,
                                                                  "total_force_fight", 4):
                            return "UNEXPECTED_PAGE"

                        return "GIVE_UP_FIGHT"

            if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382, 22,
                                                      "total_force_fight", 4):
                return "UNEXPECTED_PAGE"
    else:
        log.d("NO UNFINISHED FIGHT", 1, logger_box=self.loggerBox)
        return "NO_UNFINISHED_FIGHT"


def total_force_fight_highest_difficulty_button_judgement(button_list):
    for i in range(0, len(button_list) - 1):
        if button_list[i][0] and button_list[i + 1][1]:
            return i
    if button_list[len(button_list) - 1][0]:
        return len(button_list) - 1
    return "NOT_FIND"


def total_force_fight_highest_difficulty_button_detector(self, maxx, temp_ocr):
    log.d("BEGIN DETECT HIGHEST UNLOCK LEVEL", 1, logger_box=self.loggerBox)
    button_detected = np.full([len(self.total_force_fight_difficulty_name), 2], False, dtype=bool)
    name = ["BRIGHT", "GREY"]
    for try_cnt in range(0, 3):
        img = self.operation("get_screenshot_array")
        crop_img = img_crop(img, 661, 811, 0, 720)
        ocr_res = temp_ocr.ocr(crop_img)
        for i in range(0, len(self.total_force_fight_difficulty_name)):
            num = self.total_force_fight_difficulty_name_dict[self.total_force_fight_difficulty_name[i]]
            if button_detected[num].any():
                continue
            for j in range(0, len(ocr_res)):
                if kmp(self.total_force_fight_difficulty_name[i].lower(), ocr_res[j]["text"].lower()):
                    temp = 0
                    y = int(ocr_res[j]["position"][3][1])

                    if img[y][1163].sum() / 3 < 127:
                        temp = 1

                    log.d("detect " + self.total_force_fight_difficulty_name[i] + " " + name[temp] + " button", 1,
                          logger_box=self.loggerBox)

                    if num >= maxx and temp == 0:
                        return maxx

                    button_detected[num][temp] = True
                    t = total_force_fight_highest_difficulty_button_judgement(button_detected)

                    if isinstance(t, int):
                        return t
                    break

        log.d("SWIPE DOWNWARDS", 1, logger_box=self.loggerBox)
        self.operation("swipe", [(950, 590), (950, 330)], duration=0.1)
        time.sleep(2)

        for i in range(0, len(self.total_force_fight_difficulty_name)):
            num = self.total_force_fight_difficulty_name_dict[self.total_force_fight_difficulty_name[i]]
            if button_detected[num].any():
                continue
            for j in range(0, len(ocr_res)):
                if kmp(self.total_force_fight_difficulty_name[i].lower(), ocr_res[j]["text"].lower()):
                    temp = 0
                    y = int(ocr_res[j]["position"][3][1])

                    if img[y][1163].sum() / 3 < 127:
                        temp = 1

                    log.d("detect " + self.total_force_fight_difficulty_name[i] + " " + name[temp] + " button", 1,
                          logger_box=self.loggerBox)

                    num = self.total_force_fight_difficulty_name_dict[self.total_force_fight_difficulty_name[i]]

                    if num >= maxx and temp == 0:
                        return maxx

                    button_detected[num][temp] = True
                    t = total_force_fight_highest_difficulty_button_judgement(button_detected)
                    if isinstance(t, int):
                        return t
                    break

        if try_cnt != 3:
            log.d("SWIPE UPWARDS", 1, logger_box=self.loggerBox)
            self.operation("swipe", [(950, 330), (950, 590)], duration=0.1)

    log.d("CAN'T DETECT HIGHEST UNLOCK LEVEL", 3, logger_box=self.loggerBox)
    return False


def implement(self):
    self.logger.info("reconstructing total_force_fight task")
    return True
    temp_ocr = CnOcr(det_model_name="en_PP-OCRv3_det", rec_model_name='en_number_mobile_v2.0')
    maxx_name = self.config.get('totalForceFightDifficulty')
    self.name_dict = {"NORMAL": 0, "HARD": 1, "VERYHARD": 2, "HARDCORE": 3, "EXTREME": 4}
    maxx = self.total_force_fight_difficulty_name_dict[maxx_name]
    print("maxx: ", maxx)

    judge_and_finish_unfinished_total_force_fight_task(self)  # 判断有没有正在进行的总力战

    self.operation("stop_getting_screenshot_for_location")
    pri_total_force_fight = total_force_fight_highest_difficulty_button_detector(self, maxx, temp_ocr)
    self.operation("start_getting_screenshot_for_location")

    print("pri: ", pri_total_force_fight)
    Auto = True

    total_force_fight_x = 1156

    t = fight_difficulty_x(self, pri_total_force_fight, temp_ocr)
    win = False
    while t == "WIN" and pri_total_force_fight != len(self.total_force_fight_difficulty_name) - 1:
        win = True
        if pri_total_force_fight == maxx:
            break
        pri_total_force_fight += 1
        t = fight_difficulty_x(self, pri_total_force_fight, temp_ocr)

    while (t == "LOSE" or t == "UNLOCK") and pri_total_force_fight >= 0 and win == False:
        if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 62, 40,
                                                  "total_force_fight", 10):
            return False  # 判断有没有在总力战界面
        if t == "LOSE":
            log.d("GIVE UP CURRENT FIGHT", 1, logger_box=self.loggerBox)
            self.operation("click", (1164, 225), duration=1)
            self.operation("click", (800, 533), duration=1)
            self.operation("click", (800, 500), duration=3)
            if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png",
                                                      382, 22,
                                                      "total_force_fight", 4):
                return False
        pri_total_force_fight -= 1
        t = fight_difficulty_x(self, pri_total_force_fight, temp_ocr)

    if t == "UNEXPECTED_PAGE":
        return False
    if t == "NO_TICKETS":
        Auto = False

    if pri_total_force_fight == -1:  # normal打不过
        log.d("打不过最低难度，快找爱丽丝邦邦 QAQ", 4, logger_box=self.loggerBox)
        return True

    if Auto:  # 至少打过一个难度，可使用扫荡券
        y = find_button_y(self, pri_total_force_fight, temp_ocr)
        self.operation("click", (total_force_fight_x, y), duration=1)
        self.operation("click", (1066, 300))
        self.operation("click", (1068, 300))
        self.operation("click", (994, 393))
        lo = self.operation("get_current_position", )
        if lo == "detailed_message":
            log.d("TICKET INADEQUATE", 2, logger_box=self.loggerBox)
        elif lo == "notice":
            log.d("CLEAR LEFT TICKETS", 1, logger_box=self.loggerBox)
            self.operation("click", (768, 511), duration=3)
        self.operation("click", (143, 72))
        self.operation("click", (143, 72))

    if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382, 22,
                                              "total_force_fight", 10):
        return False
    self.operation("click", (1184, 657), duration=2)  # 领取 总力战积分奖励
    self.operation("click", (917, 163), duration=0.5)
    self.operation("click", (237, 303), duration=0.3)
    self.latest_img_array = self.operation("get_screenshot_array")
    path1 = "src/total_force_fight/total_force_fight_collect_reward_bright.png"
    path2 = "src/total_force_fight/total_force_fight_collect_reward_grey.png"
    return_data1 = get_x_y(self.latest_img_array, path1)
    return_data2 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    print(return_data2)
    if return_data1[1][0] <= 1e-03:
        log.d("collect TOTAL FORCE FIGHT ACCUMULATED POINTS REWARD", 1, logger_box=self.loggerBox)
        self.operation("click", (return_data1[0][0], return_data1[0][1]), duration=2)
        self.operation("click", (1240, 40))
        self.operation("click", (1240, 40))
        self.operation("click", (1240, 40))
    elif return_data2[1][0] <= 1e-03:
        log.d("NO ACCUMULATED POINTS REWARD can be collected", 1, logger_box=self.loggerBox)
        self.operation("click", (1240, 40))
        self.operation("click", (1240, 40))
    else:
        log.d("CAN'T DETECT BUTTON", 3, logger_box=self.loggerBox)
        return False
    return True
