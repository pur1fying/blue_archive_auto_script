import time
from core.utils import get_x_y, kmp
from gui.util import log
from module import common_skip_plot_method
import numpy as np


def find_button_y(self, i):
    fail_cnt = 0
    while fail_cnt <= 3:
        img = self.operation("get_screenshot_array")
        path = "src/total_force_fight/" + self.total_force_fight_name + "/"+ self.total_force_fight_difficulty_name[i] + "_BRIGHT.png"
        return_data = self.get_x_y(img, path)
        print(self.total_force_fight_difficulty_name[i])
        print(return_data)
        if return_data[1][0] <= 1e-02:
            return return_data[0][1] + 40
        log.d("SWIPE DOWNWARDS", 1, logger_box=self.loggerBox)
        if not self.operation("swipe",[(950, 590), (950, 330)], duration=0.1) :
            return False
        time.sleep(2)

        img = self.operation("get_screenshot_array")
        path = "src/total_force_fight/" + self.total_force_fight_name + "/" + self.total_force_fight_difficulty_name[i] + "_BRIGHT.png"
        return_data = self.get_x_y(img, path)
        print(self.total_force_fight_difficulty_name[i])
        print(return_data)

        if return_data[1][0] <= 1e-02:
            return return_data[0][1] + 40

        log.d("SWIPE UPWARDS", 1, logger_box=self.loggerBox)
        self.operation("swipe", [(950, 330), (950, 622)], duration=0.1)
        time.sleep(2)

    log.d("CAN'T DETECT BRIGHT BUTTON FOR LEVEL " + self.total_force_fight_difficulty_name[i], 3, logger_box=self.loggerBox)
    return False


def fight_difficulty_x(self, x):
    total_force_fight_x = 1156
    log.d("###################################################################################", 1,
          logger_box=self.loggerBox)
    log.d("start total force fight difficulty : " + self.total_force_fight_difficulty_name[x], 1, logger_box=self.loggerBox)
    log.d("start FIND BUTTON for " + self.total_force_fight_difficulty_name[x], 1, logger_box=self.loggerBox)
    total_force_fight_y = find_button_y(self, x)
    if not total_force_fight_y:
        log.d("FAIL", 1, logger_box=self.loggerBox)
        return False
    log.d("SUCCESS", 1, logger_box=self.loggerBox)
    for i in range(0, 4):
        formation_x = 64
        formation_y = [198, 274, 353, 426]
        if i == 0:
            self.operation("click", (total_force_fight_x, total_force_fight_y),duration=1)
            self.operation("click", (1015, 524),2)
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
                self.operation("click", (1157,666), duration=1)
                self.operation("click", (770,500))
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
                    self.operation("click",(return_data[0][0],return_data[0][1]),duration=1)
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
                                                      "total_force_fight", 4):
                return False
        if res:
            log.d("total force fight SUCCEEDED", level=1, logger_box=self.loggerBox)
            self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382, 22,
                                                "total_force_fight", 5)
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
        for i in range(0, 4):#四个队伍
            self.operation("click", (x, y),duration=1)
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
                    log.d("*****************************************************************************************", 1,
                          logger_box=self.loggerBox)
                    if not self.common_positional_bug_detect_method("total_force_fight", 61, 40, times=4,):
                        return "UNEXPECTED_PAGE"
                    else:
                        log.d("GIVE UP CURRENT FIGHT",1,logger_box=self.loggerBox)
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


def total_force_fight_highest_difficulty_button_judgement(self,button_list):
    for i in range(0, len(button_list)-1):
        if button_list[i][0] and button_list[i+1][1]:
            return i
    if button_list[len(button_list)-1][0]:
        return len(button_list)-1
    return False


def total_force_fight_highest_difficulty_button_detector(self):
    self.operation("stop_getting_screenshot_for_location")
    fail_cnt = 0
    button_detected = np.full([len(self.total_force_fight_difficulty_name), 2], False, dtype=bool)
    while fail_cnt <= 3:
        img = self.operation("get_screenshot_array")

        for i in range(0, len(self.total_force_fight_difficulty_name)):
            if button_detected[i].any():
                continue
            path1 = "src/total_force_fight/" + self.total_force_fight_name + "/"+ self.total_force_fight_difficulty_name[i] + "_BRIGHT.png"
            path2 = "src/total_force_fight/" + self.total_force_fight_name + "/" +self.total_force_fight_difficulty_name[i] + "_GREY.png"
            return_data1 = self.get_x_y(img, path1)
            return_data2 = self.get_x_y(img, path2)
            print(self.total_force_fight_difficulty_name[i])
            print(return_data1, return_data2)
            if return_data1[1][0] <= 1e-02 and not button_detected[i].any():

                log.d("DETECT BUTTON " + self.total_force_fight_difficulty_name[i] + " BRIGHT", 1, logger_box=self.loggerBox)
                button_detected[i][0] = True

                t = total_force_fight_highest_difficulty_button_judgement(self,button_detected)
                if type(t) == int:
                    log.d("DETECT HIGHEST UNLOCK LEVEL " + self.total_force_fight_difficulty_name[t], 1, logger_box=self.loggerBox)
                    self.operation("start_getting_screenshot_for_location")
                    return t

            elif return_data2[1][0] <= 1e-02 and not button_detected[i].any():
                log.d("DETECT BUTTON " + self.total_force_fight_difficulty_name[i] + " GREY", 1, logger_box=self.loggerBox)
                button_detected[i][1] = True
                t = total_force_fight_highest_difficulty_button_judgement(self, button_detected)
                if type(t) == int:
                    log.d("DETECT HIGHEST UNLOCK LEVEL " + self.total_force_fight_difficulty_name[t], 1, logger_box=self.loggerBox)
                    self.operation("start_getting_screenshot_for_location")
                    return t

        log.d("SWIPE DOWNWARDS", 1, logger_box=self.loggerBox)
        if not self.operation("swipe",[(950, 590), (950, 330)], duration=0.1) :
            return False
        time.sleep(2)

        img = self.operation("get_screenshot_array")
        for i in range(0, len(self.total_force_fight_difficulty_name)):
            if button_detected[i].any():
                continue
            path1 = "src/total_force_fight/" + self.total_force_fight_name + "/" + self.total_force_fight_difficulty_name[i] + "_BRIGHT.png"
            path2 = "src/total_force_fight/" +  self.total_force_fight_name + "/" + self.total_force_fight_difficulty_name[i] + "_GREY.png"
            return_data1 = self.get_x_y(img, path1)
            return_data2 = self.get_x_y(img, path2)
            print(self.total_force_fight_difficulty_name[i])
            print(return_data1, return_data2)
            if return_data1[1][0] <= 1e-02 and not button_detected[i].any():
                log.d("DETECT BUTTON " + self.total_force_fight_difficulty_name[i] + " BRIGHT", 1, logger_box=self.loggerBox)
                button_detected[i][0] = True

                t = total_force_fight_highest_difficulty_button_judgement(self, button_detected)
                if type(t) == int:
                    log.d("DETECT HIGHEST UNLOCK LEVEL " + self.total_force_fight_difficulty_name[t], 1, logger_box=self.loggerBox)
                    self.operation("start_getting_screenshot_for_location")
                    return t

            elif return_data2[1][0] <= 1e-02 and not button_detected[i].any():
                log.d("DETECT BUTTON " + self.total_force_fight_difficulty_name[i] + " GREY", 1, logger_box=self.loggerBox)
                button_detected[i][1] = True
                t = total_force_fight_highest_difficulty_button_judgement(self, button_detected)
                if type(t) == int:
                    log.d("DETECT HIGHEST UNLOCK LEVEL " + self.total_force_fight_difficulty_name[t], 1, logger_box=self.loggerBox)
                    self.operation("start_getting_screenshot_for_location")
                    return t

        fail_cnt = fail_cnt + 1
        log.d("SWIPE UPWARDS", 1, logger_box=self.loggerBox)
        self.operation("swipe", [(950, 330), (950, 622)], duration=0.1)
        time.sleep(2)

    log.d("CAN'T DETECT HIGHEST UNLOCK LEVEL", 3, logger_box=self.loggerBox)
    self.operation("start_getting_screenshot_for_location")
    return False


def implement(self):
    maxx = 5
    judge_and_finish_unfinished_total_force_fight_task(self)  # 判断有没有正在进行的总力战
    pri_total_force_fight = min(maxx,total_force_fight_highest_difficulty_button_detector(self))  # 第pri+1难度
    if not isinstance(pri_total_force_fight,int):
        return False

    Auto = True

    total_force_fight_x = 1156

    t = fight_difficulty_x(self, pri_total_force_fight)
    win = False
    while t == "WIN" and pri_total_force_fight != len(self.total_force_fight_difficulty_name) - 1:
        if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 62, 40,
                                                  "total_force_fight", 10):
            return False  # 判断有没有在总力战界面
        win = True
        if pri_total_force_fight == maxx:
            break
        pri_total_force_fight += 1
        t = fight_difficulty_x(self, pri_total_force_fight)

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
        t = fight_difficulty_x(self, pri_total_force_fight)

    if t == "UNEXPECTED_PAGE":
        return False
    if t == "NO_TICKETS":
        Auto = False

    if pri_total_force_fight == -1:
        log.d("打不过最低难度，快找爱丽丝邦邦 QAQ", 4, logger_box=self.loggerBox)
        return True

    if Auto:
        y = find_button_y(self, pri_total_force_fight)
        self.operation("click", (total_force_fight_x,y),duration=1)
        self.operation("click", (1066, 300))
        self.operation("click", (1068, 300))
        self.operation("click", (994, 393))
        lo = self.operation("get_current_position",)
        if lo == "detailed_message":
            log.d("TICKET INADEQUATE", 2, logger_box=self.loggerBox)
        elif lo == "notice":
            log.d("CLEAR LEFT TICKETS", 1, logger_box=self.loggerBox)
            self.operation("click", (768, 511), duration=3)
        self.operation("click", (143, 72))
        self.operation("click", (143, 72))

    if not self.common_icon_bug_detect_method("src/total_force_fight/total_force_fight_page.png", 382, 22,"total_force_fight", 10):
        return False
    self.operation("click", (1184,657),duration=2)
    self.operation("click", (917,163),duration=0.5)
    self.operation("click", (237,303),duration=0.3)
    self.latest_img_array = self.operation("get_screenshot_array")
    path1 = "src/total_force_fight/total_force_fight_collect_reward_bright.png"
    path2 = "src/total_force_fight/total_force_fight_collect_reward_grey.png"
    return_data1 = get_x_y(self.latest_img_array, path1)
    return_data2 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    print(return_data2)
    if return_data1[1][0] <= 1e-03:
        log.d("collect TOTAL FORCE FIGHT ACCUMULATED POINTS REWARD", 1, logger_box=self.loggerBox)
        self.operation("click", (return_data1[0][0], return_data1[0][1]),duration = 2)
        self.operation("click",(1240,40))
        self.operation("click",(1240,40))
        self.operation("click",(1240,40))
    elif return_data2[1][0] <= 1e-03:
        log.d("NO ACCUMULATED POINTS REWARD can be collected", 1, logger_box=self.loggerBox)
        self.operation("click", (1240, 40))
        self.operation("click", (1240, 40))
    else:
        log.d("CAN'T DETECT BUTTON", 3, logger_box=self.loggerBox)
        return False
    return True

