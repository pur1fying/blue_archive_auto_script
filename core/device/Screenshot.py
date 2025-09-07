import sys

from core.device.screenshot.scrcpy import ScrcpyScreenshot
from core.device.screenshot.nemu import NemuScreenshot
from core.device.screenshot.adb import AdbScreenshot
from core.device.uiautomator2.uiautomator2 import U2Screenshot
import time


class Screenshot:
    def __init__(self, Baas_instance):
        self.screenshot_interval = None
        self.screenshot_instance = None
        self.method = None

        self.Baas_instance = Baas_instance
        self.connection = Baas_instance.connection
        self.config_set = Baas_instance.get_config()
        self.config = self.config_set.config
        self.logger = Baas_instance.get_logger()
        self.set_screenshot_interval(float(self.config.screenshot_interval))
        self.last_screenshot_time = time.time()
        self.init_screenshot_instance()

    def init_screenshot_instance(self):
        self.method = self.config.screenshot_method
        self.logger.info("Screenshot method : " + self.method)

        if self.Baas_instance.is_android_device:
            if self.method == "nemu":
                self.screenshot_instance = NemuScreenshot(self.connection)
            elif self.method == "adb":
                self.screenshot_instance = AdbScreenshot(self.connection)
            elif self.method == "uiautomator2":
                self.screenshot_instance = U2Screenshot(self.connection)
            elif self.method == "scrcpy":
                self.screenshot_instance = ScrcpyScreenshot(self.connection)
        else:
            if sys.platform == "win32":
                from core.device.screenshot.pyautogui import PyautoguiScreenshot
                from core.device.screenshot.mss import MssScreenshot
                if self.method == "pyautogui":
                    self.screenshot_instance = PyautoguiScreenshot(self.connection)
                elif self.method == "mss":
                    self.screenshot_instance = MssScreenshot(self.connection)

        if self.screenshot_instance is None:
            self.logger.error(f"Unsupported screenshot method: {self.method}, please check your config and select a valid screenshot method.")
            raise ValueError("Invalid Screenshot Method")

    def screenshot(self):
        self.ensure_interval()
        image = self.screenshot_instance.screenshot()
        if not self.Baas_instance.is_android_device:
            self.Baas_instance.handle_resolution_dynamic_change()
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
