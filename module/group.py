from gui.util import log


def implement(self):
    log.d("group task finished", level=1, logger_box=self.loggerBox)
    self.main_activity[1][1] = 1
    return True
