import sys

from core.device.control.nemu import NemuControl
from core.device.control.adb import AdbControl
from core.device.control.uiautomator2 import U2Control
from core.device.control.scrcpy import ScrcpyControl


class Control:
    def __init__(self, Baas_instance):
        self.control_instance = None
        self.method = None

        self.Baas_instance = Baas_instance
        self.connection = Baas_instance.connection
        self.config_set = Baas_instance.get_config()
        self.config = self.config_set.config
        self.logger = Baas_instance.get_logger()
        self.init_control_instance()

    def init_control_instance(self):
        self.method = self.config.control_method
        self.logger.info("Control method : " + self.method)

        if self.Baas_instance.is_android_device:
            if self.method == "nemu":
                self.control_instance = NemuControl(self.connection)
            elif self.method == "adb":
                self.control_instance = AdbControl(self.connection)
            elif self.method == "uiautomator2":
                self.control_instance = U2Control(self.connection)
            elif self.method == "scrcpy":
                self.control_instance = ScrcpyControl(self.connection)
        else:
            if sys.platform == "win32":
                from core.device.control.pyautogui import PyautoguiControl
                if self.method == "pyautogui":
                    self.control_instance = PyautoguiControl(self.connection)

        if self.control_instance is None:
            self.logger.error(f"Unsupported control method: {self.method}, please check your config and select a valid control method.")
            raise ValueError("Invalid Control Method")

    def click(self, x, y):
        self.control_instance.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.control_instance.swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        self.control_instance.long_click(x, y, duration)

    def scroll(self, x, y, clicks):
        self.control_instance.scroll(x, y, clicks)
