import time

from gui.util import log


def implement(self):
    self.click(767, 500)
    while self.pd_pos(True) != "notice":
        self.click(768, 504)
        time.sleep(2)

    self.click(764, 504)
    time.sleep(1)
    res = self.common_fight_practice()

    if not res:
        log.d("total force fight failed", level=1, logger_box=self.loggerBox)
        fail_x = 68
        fail_count_y = [271, 353, 438]
        fail_count = 1
        while fail_count <= 3:
            self.to_main_page()
            self.main_to_page(14)
            log.d("continue with formation: " + str(fail_count + 1), level=1, logger_box=self.loggerBox)
            self.click(fail_x, fail_count_y[fail_count - 1])
            time.sleep(2)
            self.click(1155, 658)
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
