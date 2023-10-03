import time

from gui.util import log
from module import common_skip_plot_method


def fight_difficulty_x(self, x, skip_plot=False):
    diificulty_name = ["NORMAL","HARD","VERYHARD","HARDCORE","EXTREME"]
    log.d("###################################################################################",1,logger_box=self.loggerBox)
    log.d("start total force fight difficulty : " + diificulty_name[x],1,logger_box=self.loggerBox)

    for i in range(0, 4):
        self.to_main_page()
        self.main_to_page(8)
        total_force_fight_y = [225, 351, 487, 389, 533]
        total_force_fight_x = 1156
        formation_x = 64
        formation_y = [198, 274, 353, 426]
        if i == 0:
            if x >= 3:
                self.connection.swipe(950, 601, 950, 307, 0.2)
                time.sleep(0.2)

            self.click(total_force_fight_x,total_force_fight_y[x])
            time.sleep(0.5)
            self.click(1015, 524)
            lo = self.pd_pos()
            if lo == "notice":
                log.d("TICKET INADEQUATE QUIT TOTAL FORCE FIGHT TASK", 2, logger_box=self.loggerBox)
                return "NO_TICKETS"
            if lo == "attack_formation":
                log.d("choose formation : "+str(i+1) + " and start fight",1,logger_box=self.loggerBox)
                self.click(formation_x, formation_y[0])
                time.sleep(0.2)
                self.click(1157, 666)
                time.sleep(0.5)
                self.click(770,500)
                ####
                if skip_plot:
                    common_skip_plot_method.implement(self)
            else:
                return "UNEXPECTED_PAGE"

        else:
            self.click(total_force_fight_x,total_force_fight_y[0])
            if not self.common_positional_bug_detect_method("attack_formation",total_force_fight_x,total_force_fight_y[0],times=5):
                return "UNEXPECTED_PAGE"
            log.d("choose formation " + str(i + 1) + " and start fight", 1, logger_box=self.loggerBox)
            self.click(formation_x, formation_y[i])
            self.click(1011, 552)

        self.common_positional_bug_detect_method("notice", 764, 504, times=7,any=True)
        log.d("SKIP animation", 1, logger_box=self.loggerBox)
        self.click(764, 504)
        time.sleep(3)
        res = self.common_fight_practice()

        if not res:
            log.d("total force fight attempt" + str(i+1) + "FAILED",1,logger_box=self.loggerBox)

        if res:
            log.d("total force fight SUCCEEDED", level=1, logger_box=self.loggerBox)
            log.d("###################################################################################", 1,
                    logger_box=self.loggerBox)
            return True

    log.d("4 attempts ALL FAILED", 1, logger_box=self.loggerBox)
    log.d("###################################################################################",1,logger_box=self.loggerBox)

    return False


def implement(self):

    self.first_time_total_force_fight = True
    pri_total_force_fight = 1  #第pri+1难度
    if self.first_time_total_force_fight:
        return_value = fight_difficulty_x(self, pri_total_force_fight, self.first_time_total_force_fight)
        self.first_time_total_force_fight = False
        while return_value == "WIN":
            return_value = fight_difficulty_x(self, pri_total_force_fight, self.first_time_total_force_fight)
            self.common_positional_bug_detect_method("total_force_fight", 862, 493, 5, any=True)
            pri_total_force_fight += 1
        if return_value == "NO_TICKETS":
            return True
        if return_value == "UNEXPECTED_PAGE":
            log.d("UNEXPECTED PAGE",3,logger_box=self.loggerBox)
            return False

    pri_total_force_fight -= 1

