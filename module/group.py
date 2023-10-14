from gui.util import log


def implement(self):
    log.d("group task finished", level=1, logger_box=self.loggerBox)
    self.operation("click", (1236, 39))
    self.operation("click", (1236, 39))
    return True
