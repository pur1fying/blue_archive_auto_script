import time

from gui.util import log


def implement(self):
    dif = [5, 5, 5]
    log.line(self.loggerBox)
    log.d("rewarded task road begin", level=1, logger_box=self.loggerBox)
    self.click(957, 275)
    time.sleep(1.5)
    self.special_task_common_operation(dif[0], 6, False)
    log.d("rewarded task road finished", level=1, logger_box=self.loggerBox)

    log.line(self.loggerBox)
    log.d("rewarded task rail begin", level=1, logger_box=self.loggerBox)
    self.main_to_page(6)
    self.click(957, 412)
    time.sleep(1.5)
    self.special_task_common_operation(dif[1], 6, False)
    log.d("rewarded task rail finished", level=1, logger_box=self.loggerBox)

    log.line(self.loggerBox)
    log.d("rewarded task class begin", level=1, logger_box=self.loggerBox)
    self.main_to_page(6)
    self.click(957, 556)
    time.sleep(1.5)
    self.special_task_common_operation(dif[2], 6, False)
    log.d("rewarded task class finished", level=1, logger_box=self.loggerBox)
