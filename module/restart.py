import time
from datetime import datetime

from core.utils import is_android


def implement(self):
    if not self.is_android_device:
        return True
    cur_package = self.u2.app_current()['package']
    if cur_package != self.package_name:
        if cur_package != self.package_name:
            self.logger.warning("APP NOT RUNNING current package: " + cur_package)
        start(self)
        return True
    self.logger.info("CHECK RESTART")
    if check_need_restart(self):
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.u2.app_stop(self.package_name)
        time.sleep(2)
        start(self)
        return True
    return True


def start(self):
    self.logger.info("-- START BLUE ARCHIVE --")
    if is_android():
        self.u2.shell(f"am start --display {self.target_display.logical_id} -n {self.package_name}/{self.activity_name}")
    else:
        self.u2.app_start(self.package_name, self.activity_name)
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
