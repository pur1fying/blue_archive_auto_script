from datetime import datetime
import time
import random
from core import color


def implement(self):
    cur_package = self.connection.app_current()['package']
    if cur_package != self.package_name or self.first_start:
        self.first_start = False
        if cur_package != self.package_name:
            self.logger.warning("APP  NOT RUNNING current package: " + cur_package)
        start(self)
        return True
    self.logger.info("CHECK RESTART")
    now = datetime.now()
    if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=4).timestamp()) <= 60:
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.connection.app_stop(self.package_name)
        time.sleep(2)
        start(self)
        return True
    return True


def start(self):
    self.logger.info("--START BLUE ARCHIVE--")
    activity = '.MxUnityPlayerActivity' if self.server == 'Global' else None
    self.connection.app_start(self.package_name, activity=activity)
    if self.server == 'CN':
        self.logger.info("--ENSURE UI AT MAIN PAGE--")
        self.quick_method_to_main_page()
        time.sleep(2)
    elif self.server == 'Global':
        color.wait_loading(self)
        while not color.detect_rgb_one_time(self, [], [], ['main_page']):
            x = random.randint(0, 200)
            y = random.randint(30, 150)
            self.click(x + 1050, y, wait=False, wait_over=True)
            color.wait_loading(self)
        time.sleep(2)
        self.quick_method_to_main_page()
        time.sleep(2)
        while not color.detect_rgb_one_time(self, [], [], ['main_page']):
            x = random.randint(0, 200)
            y = random.randint(30, 150)
            self.click(x + 1050, y, wait=False, wait_over=True)
            color.wait_loading(self)
