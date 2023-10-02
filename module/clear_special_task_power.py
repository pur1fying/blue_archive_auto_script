import time

from gui.util import log


def implement(self):
    special_task_guard_count = [6, 1]  # 可设置参数 [i,j]表示据点防御第i关打j次 , 请确保关卡已开启扫荡
    special_task_credit_count = [3, 1]  # 可设置参数 [i,j]表示信用回收第i关打j次 , 请确保关卡已开启扫荡

    if len(special_task_guard_count) != 0:
        log.line(self.loggerBox)
        log.d("special task guard begin", level=1, logger_box=self.loggerBox)

        self.click(959, 269)
        time.sleep(1.5)

        self.special_task_common_operation(special_task_guard_count[0], special_task_guard_count[1])
        log.d("special task guard finished", level=1, logger_box=self.loggerBox)

    if len(special_task_guard_count) != 0:
        log.line(self.loggerBox)
        log.d("special task credit begin", level=1, logger_box=self.loggerBox)

        self.to_main_page()
        self.main_to_page(11)
        self.click(964, 408)
        time.sleep(1.5)

        self.special_task_common_operation(special_task_credit_count[0], special_task_credit_count[1])
        log.d("special task credit finished", level=1, logger_box=self.loggerBox)

    self.main_activity[11][1] = 1
    log.d("clear special task power finished", level=1, logger_box=self.loggerBox)
