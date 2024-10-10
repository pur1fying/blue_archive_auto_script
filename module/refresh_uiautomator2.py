import time


def implement(self):
    self.logger.info("KILL CURRENT UIAUTOMATOR2")
    self.u2.app_stop("com.github.uiautomator")
    self.u2.uiautomator.start()
    self.wait_uiautomator_start()
    self.click(5, 5, wait_over=True)
    self.last_refresh_u2_time = time.time()
    return True
