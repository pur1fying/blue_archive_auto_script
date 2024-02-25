import time


def implement(self):
    self.logger.info("KILL CURRENT UIAUTOMATOR2")
    self.connection.app_stop("com.github.uiautomator")
    self.connection.uiautomator.start()
    self.wait_uiautomator_start()
    self.click(5, 5, wait_over=True)
    self.last_refresh_u2_time = time.time()
    return True
