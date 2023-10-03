import time

from gui.util import log


def implement(self):
    dif = [3, 4, 5]
    count = [5,5,5]
    self.rewarded_task_status = [False,False,False]
    just_do_task = False
    if not self.rewarded_task_status[0]:
        just_do_task = True
        log.line(self.loggerBox)
        log.d("rewarded task road begin", level=1, logger_box=self.loggerBox)
        self.click(957, 275)
        if not self.common_positional_bug_detect_method("rewarded_task_road",957,275,2):
            return False
        if self.special_task_common_operation(dif[0], count[0], False):
            self.rewarded_task_status[0] = True
            log.d("rewarded task road finished", level=1, logger_box=self.loggerBox)
        else:
            log.d("rewarded task road unsolved", level=2, logger_box=self.loggerBox)

    if not self.rewarded_task_status[1]:
        just_do_task = True
        log.line(self.loggerBox)
        log.d("rewarded task rail begin", level=1, logger_box=self.loggerBox)
        if just_do_task:
            self.to_main_page()
            self.main_to_page(6)
        self.click(957, 412)
        if not self.common_positional_bug_detect_method("rewarded_task_rail",957,412,2):
            return False
        if self.special_task_common_operation(dif[1], count[1], False):
            self.rewarded_task_status[1] = True
            log.d("rewarded task rail finished", level=1, logger_box=self.loggerBox)
        else:
            log.d("rewarded task rail unsolved", level=2, logger_box=self.loggerBox)

    if not self.rewarded_task_status[2]:
        log.line(self.loggerBox)
        log.d("rewarded task class begin", level=1, logger_box=self.loggerBox)
        if just_do_task:
            self.to_main_page()
            self.main_to_page(6)
        self.click(957, 556)
        if not self.common_positional_bug_detect_method("rewarded_task_classroom", 957, 556, 2):
            return False
        if self.special_task_common_operation(dif[2], count[2], False):
            self.rewarded_task_status[2] = True
            log.d("rewarded task classroom finished", level=1, logger_box=self.loggerBox)
        else:
            log.d("rewarded task classroom unsolved", level=2, logger_box=self.loggerBox)

    if self.rewarded_task_status[0] and self.rewarded_task_status[1] and self.rewarded_task_status[2]:
        self.main_activity[6][1]=1
        return True
    return False
