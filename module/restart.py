from datetime import datetime
import time


def implement(self):
    self.logger.info("CHECK RESTART")
    cur_package = self.connection.app_current()['package']
    now = datetime.now()
    if cur_package == self.package_name and abs(
            time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=4).timestamp()) <= 60:
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.connection.app_stop(self.package_name)
        time.sleep(2)
        self.logger.info("--START BLUE ARCHIVE--")
        self.connection.app_start(self.package_name)
    return True
