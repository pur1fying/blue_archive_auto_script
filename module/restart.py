import time
from datetime import datetime


def implement(self):
    if not self.is_android_device:
        return True
    cur_package = self.connection.get_current_package()
    if cur_package != self.package_name:
        if cur_package != self.package_name:
            self.logger.warning("APP NOT RUNNING current package: " + cur_package)
        start(self)
        return True
    self.logger.info("CHECK RESTART")
    if check_need_restart(self):
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.connection.stop_app(self.package_name)
        time.sleep(2)
        start(self)
        return True
    return True


def start(self):
    self.logger.info("-- START BLUE ARCHIVE --")
    activity_name = self.activity_name
    if self.server == 'CN':
        activity_name = None
    self.connection.start_app(self.package_name, activity_name)
    time.sleep(1)
    if self.server == 'Global':
        self.to_main_page()
        time.sleep(4)


def check_need_restart(self):
    now = datetime.now()
    if self.server == 'CN':
        if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=4).timestamp()) <= 60:
            return True
    elif self.server == 'Global' or self.server == 'JP':
        if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=3).timestamp()) <= 60:
            return True
    return False
