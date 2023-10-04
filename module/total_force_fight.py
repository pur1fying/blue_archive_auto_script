import time
from core.utils import get_x_y,kmp
from gui.util import log
from module import common_skip_plot_method


def fight_difficulty_x(self, x, skip_plot=False):
    total_force_fight_y = [225, 351, 487, 389, 533]
    total_force_fight_x = 1156
    diificulty_name = ["NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME"]
    log.d("###################################################################################", 1,
          logger_box=self.loggerBox)
    log.d("start total force fight difficulty : " + diificulty_name[x], 1, logger_box=self.loggerBox)
    self.to_main_page()
    self.main_to_page(8)

    ocr_res = self.img_ocr(self.latest_img_array)
    if kmp("再次入场", ocr_res) > 0 or kmp("正在进行", ocr_res) > 0:
        log.d("GIVE UP CURRENT FIGHT", 1, logger_box=self.loggerBox)
        self.click(total_force_fight_x, total_force_fight_y[0])
        time.sleep(1)
        self.click(800, 533)
        time.sleep(1)
        self.click(800, 533)
        time.sleep(3)
        if not self.common_positional_bug_detect_method("total_force_fight", 382, 22, 3, anywhere=True):
            return "UNEXPECTED_PAGE"
    for i in range(0, 4):
        formation_x = 64
        formation_y = [198, 274, 353, 426]
        if i == 0:
            if x >= 3:
                self.connection.swipe(950, 601, 950, 307, 0.2)
                time.sleep(0.2)

            self.click(total_force_fight_x, total_force_fight_y[x])
            time.sleep(1)
            self.click(1015, 524)
            lo = self.pd_pos()
            if lo == "notice":
                log.d("TICKET INADEQUATE QUIT TOTAL FORCE FIGHT TASK", 2, logger_box=self.loggerBox)
                return "NO_TICKETS"
            elif lo == "attack_formation":
                time.sleep(1)
                log.d("choose formation : " + str(i + 1) + " and start fight", 1, logger_box=self.loggerBox)
                self.click(formation_x, formation_y[0])
                time.sleep(1)
                self.click(1157, 666)
                time.sleep(1)
                self.click(770, 500)
                ####
                if skip_plot:
                    common_skip_plot_method.implement(self)
            elif lo == "total_force_fight":
                log.d("CURRENT difficulty UNLOCKED, try LOWER difficulty", 1, logger_box=self.loggerBox)

                return "UNLOCKED"
            else:
                log.d("UNEXPECTED PAGE", 3, logger_box=self.loggerBox)
                return "UNEXPECTED_PAGE"
        else:
            self.click(total_force_fight_x, total_force_fight_y[0])
            time.sleep(1)
            self.click(1015, 524)
            if not self.common_positional_bug_detect_method("attack_formation", 1015,524):
                return "UNEXPECTED_PAGE"
            log.d("choose formation " + str(i + 1) + " and start fight", 1, logger_box=self.loggerBox)
            self.click(formation_x, formation_y[i])
            self.click(1156, 650)

        if not self.common_positional_bug_detect_method("notice", 640, 100, times=7, anywhere=True):
            log.d("SKIP animation", 1, logger_box=self.loggerBox)
            self.click(764, 504)
            time.sleep(3)
            return "UNEXPECTED_PAGE"
        res = self.common_fight_practice()

        if not res:
            log.d("total force fight attempt " + str(i + 1) + " FAILED", 1, logger_box=self.loggerBox)
            self.common_positional_bug_detect_method("total_force_fight", 382, 22, 5, anywhere=True)

        if res:
            log.d("total force fight SUCCEEDED", level=1, logger_box=self.loggerBox)
            log.d("###################################################################################", 1,
                  logger_box=self.loggerBox)
            return "WIN"

    log.d("4 attempts ALL FAILED", 1, logger_box=self.loggerBox)
    log.d("###################################################################################", 1,
          logger_box=self.loggerBox)

    return "LOSE"


def implement(self):
    total_force_fight_y = [225, 351, 487, 389, 533]
    total_force_fight_x = 1156
    Auto = True
    self.first_time_total_force_fight = False
    pri_total_force_fight = 2  # 第pri+1难度
    if self.first_time_total_force_fight:
        return_value = fight_difficulty_x(self, pri_total_force_fight, self.first_time_total_force_fight)
        self.first_time_total_force_fight = False
        while return_value == "WIN":
            pri_total_force_fight += 1
            return_value = fight_difficulty_x(self, pri_total_force_fight, self.first_time_total_force_fight)
            self.common_positional_bug_detect_method("total_force_fight", 382, 22, 5, anywhere=True)
        if return_value == "NO_TICKETS":
            Auto = False
            pri_total_force_fight -= 1
            return True
        if return_value == "UNEXPECTED_PAGE":
            pri_total_force_fight -= 1
            log.d("UNEXPECTED PAGE quit task", 3, logger_box=self.loggerBox)
            return False
        if return_value == "LOSE":
            pri_total_force_fight -= 1

    else:
        t = fight_difficulty_x(self, pri_total_force_fight, self.first_time_total_force_fight)
        while (t == "LOSE" or t == "UNLOCKED") and pri_total_force_fight >= 0:
            pri_total_force_fight -= 1
            t = fight_difficulty_x(self, pri_total_force_fight, self.first_time_total_force_fight)
        if t == "UNEXPECTED_PAGE":
            return False
        if t == "NO_TICKETS":
            Auto = False

    if pri_total_force_fight == -1:
        log.d("打不过最低难度，快找爱丽丝邦邦 QWQ", 4, logger_box=self.loggerBox)
        return True
    if Auto:
        if pri_total_force_fight >= 3:
            self.connection.swipe(950, 601, 950, 307, 0.2)
            time.sleep(0.2)
        self.click(total_force_fight_x, total_force_fight_y[pri_total_force_fight])
        time.sleep(1)
        self.click(1068, 363)
        self.click(1068, 363)
        self.click(944, 393)
        lo = self.pd_pos()
        if lo == "detailed_message":
            log.d("TICKET INADEQUATE", 2, logger_box=self.loggerBox)
        elif lo == "notice":
            log.d("CLEAR LEFT TICKETS", 1,logger_box=self.loggerBox)
            self.click(768, 511)
    if self.common_positional_bug_detect_method("total_force_fight", 382, 22, 5, anywhere=True):
        self.click(1184,657)
        time.sleep(2)
        self.click(917,163)
        time.sleep(0.5)
        self.click(237,303)
        time.sleep(0.3)
        self.latest_img_array = self.get_screen_shot_array()
        path1 = "src/total_force_fight/total_force_fight_collect_reward_bright.png"
        path2 = "src/total_force_fight/total_force_fight_collect_reward_grey.png"
        return_data1 = get_x_y(self.latest_img_array, path1)
        return_data2 = get_x_y(self.latest_img_array, path2)
        print(return_data1)
        print(return_data2)
        if return_data1[1][0] <= 1e-03:
            log.d("collect TOTAL FORCE FIGHT ACCUMULATED POINTS REWARD", 1, logger_box=self.loggerBox)
            self.click(return_data1[0][0], return_data1[0][1])
        elif return_data2[1][0] <= 1e-03:
            log.d("NO ACCUMULATED POINTS REWARD can be collected", 1, logger_box=self.loggerBox)
        else:
            log.d("CAN'T DETECT BUTTON", 3, logger_box=self.loggerBox)
            return False
        return True
