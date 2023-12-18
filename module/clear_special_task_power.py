from gui.util import log
from datetime import datetime

x = {

}

def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    next_time = datetime(year, month, day+1, 4)
    return next_time.timestamp()


def implement(self):
    special_task_guard_count = [1, 1]
    special_task_credit_count = [1, 1]
    self.special_task_status = [False, False]
    just_do_task = False
    if len(special_task_guard_count) != 0:
        just_do_task = True
        log.line(self.loggerBox)
        log.d("special task Guard begin", level=1, logger_box=self.loggerBox)
        self.operation("click", (959, 269))
        if not self.common_positional_bug_detect_method("special_task_guard", 959, 269, 2):
            return False
        if self.special_task_common_operation(special_task_guard_count[0], special_task_guard_count[1]):
            self.special_task_status[0] = True
            log.d("special task Guard finished", level=1, logger_box=self.loggerBox)
        else:
            log.d("special task Guard unsolved", level=2, logger_box=self.loggerBox)
    else:
        self.special_task_status[0] = True

    if len(special_task_credit_count) != 0:
        log.line(self.loggerBox)
        log.d("special task Credit begin", level=1, logger_box=self.loggerBox)
        if just_do_task:
            self.common_positional_bug_detect_method("main_page", 1236, 39, times=7, anywhere=True)
            self.main_to_page(11)

        self.operation("click", (959, 408))
        if not self.common_positional_bug_detect_method("special_task_credit", 959, 408, 2):
            return False
        if self.special_task_common_operation(special_task_credit_count[0], special_task_credit_count[1]):
            self.special_task_status[1] = True
            log.d("special task Credit finished", level=1, logger_box=self.loggerBox)
        else:
            log.d("special task Credit unsolved", level=2, logger_box=self.loggerBox)

    if self.special_task_status[0] and self.special_task_status[1]:
        self.next_execute_time_queue.put(["special_task", get_next_execute_tick()])
        return True
    return False


