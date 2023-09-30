from gui.util import log


def implement(self):
    self.click(640, 521)
    log.d("cafe reward task finished", level=1, logger_box=self.loggerBox)
    self.main_activity[0][1] = 1
