import sys
import time

from core.device.adb.adb import AdbClient
from core.device.nemu.nemu import NemuClient
from core.device.scrcpy.scrcpy import ScrcpyClient
from core.device.uiautomator2.uiautomator2 import U2Client
from core.device.windows.mss import MssScreenshot
from core.device.windows.pyautogui import PyautoguiClient


class Screenshot:
    def __init__(self, Baas_instance):
        self.screenshot_interval = None
        self.screenshot_instance = None
        self.screenshot_method = None

        self.Baas_instance = Baas_instance
        self.connection = Baas_instance.connection
        self.config = self.Baas_instance.get_config().config
        self.logger = Baas_instance.get_logger()
        self.set_screenshot_interval(float(self.config.screenshot_interval))
        self.last_screenshot_time = time.time()

        self.init_screenshot_instance()

    def init_screenshot_instance(self):
        self.screenshot_method = self.config.screenshot_method
        self.logger.info("Screenshot method : " + self.screenshot_method)

        if self.Baas_instance.is_android_device:
            if self.screenshot_method == "nemu":
                self.screenshot_instance = NemuClient.get_instance(self.connection)
            elif self.screenshot_method == "adb":
                self.screenshot_instance = AdbClient.get_instance(self.connection.serial)
            elif self.screenshot_method == "uiautomator2":
                self.screenshot_instance = U2Client.get_instance(self.connection.serial)
            elif self.screenshot_method == "scrcpy":
                self.screenshot_instance = ScrcpyClient.get_instance(self.connection.serial)
        else:
            if sys.platform == "win32":
                if self.screenshot_method == "pyautogui":
                    self.screenshot_instance = PyautoguiClient(self.connection)
                elif self.screenshot_method == "mss":
                    self.screenshot_instance = MssScreenshot(self.connection)

        if self.screenshot_instance is None:
            self.logger.error(
                f"Unsupported screenshot method: {self.screenshot_method}, please check your config and select a valid screenshot method.")
            raise ValueError("Invalid Screenshot Method")

    def screenshot(self):
        # Limit screenshot frequency
        diff = time.time() - self.last_screenshot_time
        if diff < self.screenshot_interval:
            time.sleep(self.screenshot_interval - diff)

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
