def implement(self):
    self.logger.info("KILL CURRENT UIAUTOMATOR2")
    self.connection.app_stop('com.github.uiautomator')
    self.logger.info("START UIAUTOMATOR2 and test click")
    self.click(5, 5, wait=False, wait_over=True)
    return True
