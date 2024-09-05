from core.device.connection import Connection
from core.device.screenshot.nemu import NemuScreenshot
from core.device.screenshot.adb import AdbScreenshot
from core.device.screenshot.uiautomator2 import U2Screenshot
import time


class Screenshot:
    def __init__(self, Baas_instance):
        self.screenshot_interval = None
        self.screenshot_instance = None

        self.Baas_instance = Baas_instance
        self.connection = Baas_instance.connection
        self.config = Baas_instance.get_config()
        self.logger = Baas_instance.get_logger()
        self.set_screenshot_interval(float(self.config.get("screenshot_interval")))
        self.last_screenshot_time = time.time()
        self.init_screenshot_instance()

    def init_screenshot_instance(self):
        method = self.config.get("screenshot_method")
        self.logger.info("Screenshot method : " + method)
        if method == "nemu":
            self.screenshot_instance = NemuScreenshot(self.connection)
        elif method == "adb":
            self.screenshot_instance = AdbScreenshot(self.connection)
        elif method == "uiautomator2":
            self.screenshot_instance = U2Screenshot(self.connection)

    def screenshot(self):
        self.ensure_interval()
        image = self.screenshot_instance.screenshot()
        self.last_screenshot_time = time.time()
        return image

    def set_screenshot_interval(self, interval):
        if interval < 0.3:
            self.logger.warning("screenshot_interval must be greater than 0.3")
            interval = 0.3
        self.logger.info("screenshot_interval set to " + str(interval))
        self.screenshot_interval = interval
        return interval

    def ensure_interval(self):
        diff = time.time() - self.last_screenshot_time
        if diff < self.screenshot_interval:
            time.sleep(self.screenshot_interval - diff)
