import time
from datetime import datetime


def implement(self):
    cur_package = self.connection.app_current()['package']
    if cur_package != self.package_name or self.first_start:
        self.first_start = False
        if cur_package != self.package_name:
            self.logger.warning("APP  NOT RUNNING current package: " + cur_package)
        start(self)
        return True
    self.logger.info("CHECK RESTART")
    if check_need_restart(self):
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.connection.app_stop(self.package_name)
        time.sleep(2)
        start(self)
        return True
    return True


def start(self):
    self.logger.info("-- START BLUE ARCHIVE --")
    activity_name = self.activity_name
    if self.server == 'CN':
        activity_name = None
    self.connection.app_start(self.package_name, activity_name)
    time.sleep(1)


def check_need_restart(self):
    now = datetime.now()
    if self.server == 'CN':
        if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=4).timestamp()) <= 60:
            return True
    elif self.server == 'Global' or self.server == 'JP':
        if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=3).timestamp()) <= 60:
            return True
    return False
