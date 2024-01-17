import time


def implement(self):
    self.logger.info("Check uiautomator2 refresh")
    if time.time() - self.last_start_u2_time <= 10800:
        return True
    self.logger.info("KILL CURRENT UIAUTOMATOR2")
    self.connection.app_stop('com.github.uiautomator')
    self.logger.info("START UIAUTOMATOR2 and test click")
    self.click(5, 5, wait=False, wait_over=True)
    return True
