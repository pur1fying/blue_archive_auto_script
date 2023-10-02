import time

from gui.util import log


def total_force_fight_choose_difficulty_and_formation(self, difficulty, formation=3):
    total_force_fight_y = [225, 351, 487, 389, 533]
    total_force_fight_x = 1156
    formation_x = 64
    formation_y = [198, 274, 353, 426]
    path = [[total_force_fight_x, 1011, formation_x], [total_force_fight_y[difficulty], 522, formation_y[formation]],
            ["detailed_message", "attack_formation", "attack_formation"]]
    if difficulty >= 2:
        self.connection.swipe(950, 601, 950, 307, 0.2)
        time.sleep(0.2)
    i = 0
    times = 0
    step = len(path[0])
    while i != step:
        x = path[0][i]
        y = path[1][i]
        page = path[2][i]
        self.click(x, y)
        if self.pd_pos() != page:
            if times <= 1:
                times += 1
                log.d("not in page " + str(page) + " , count = " + str(times), level=2, logger_box=self.loggerBox)
            elif times == 2:
                log.d("not in page " + str(page) + " , return to main page", level=2, logger_box=self.loggerBox)
                self.to_main_page()
                self.main_to_page(8)
                times = 0
                i = 0
        else:
            times = 0
            i += 1


def implement(self):
    pri_total_force_fight = 4
    total_force_fight_choose_difficulty_and_formation(self, pri_total_force_fight)
    self.click(1156, 657)
    time.sleep(0.5)
    self.click(851, 458)
    time.sleep(6)
    while self.pd_pos(True) != "notice":
        self.click(768, 504)
        time.sleep(4)

    self.click(764, 504)
    time.sleep(1)
    res = self.common_fight_practice()

    if not res:
        log.d("total force fight failed", level=1, logger_box=self.loggerBox)
        fail_count = 1
        while fail_count <= 3:
            self.to_main_page()
            self.main_to_page(8)
            log.d("continue with formation: " + str(fail_count + 1), level=1, logger_box=self.loggerBox)
            total_force_fight_choose_difficulty_and_formation(self, pri_total_force_fight, fail_count)
            self.click(1156, 657)
            time.sleep(6)
            while self.pd_pos(True) != "notice":
                self.click(764, 504)
                time.sleep(4)
            self.click(764, 504)
            res = self.common_fight_practice()
            if not res:
                fail_count += 1
            else:
                break
        log.d("total force fight difficulty " + str(self.pri_total_force_fight + 1) + "failed", level=3,
              logger_box=self.loggerBox)
        self.pri_total_force_fight -= 1
        time.sleep(4)
        self.click(1162, 225)
        log.d("give up", level=3, logger_box=self.loggerBox)
        time.sleep(0.5)
        self.click(821, 532)
        return
    if res:
        log.d("total force fight succeeded", level=1, logger_box=self.loggerBox)
        self.click(1156, self.total_force_fight_y[self.pri_total_force_fight])
        time.sleep(0.2)
        for i in range(0, 5):
            self.click(1070, 297)
        while self.pd_pos() != "total_force_fight":
            self.click(300, 50)
        self.click(1180, 655)
        time.sleep(0.8)
        self.click(923, 177)
        time.sleep(0.2)
        self.click(240, 303)
        time.sleep(0.2)
        self.click(1051, 577)
        self.main_activity[8][1] = 1
        return
