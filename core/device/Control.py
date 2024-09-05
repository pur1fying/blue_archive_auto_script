from core.device.control.nemu import NemuControl
from core.device.control.adb import AdbControl
from core.device.control.uiautomator2 import U2Control
from core.Baas_thread import Baas_thread


class Control:
    def __init__(self, Baas_instance: Baas_thread):
        self.Baas_instance = Baas_instance
        self.config = Baas_instance.get_config()
        self.logger = Baas_instance.get_logger()
        self.control_instance = None
        self.init_control_instance()

    def init_control_instance(self):
        method = self.config.get("screenshot_method")
        if method == "nemu":
            self.control_instance = NemuControl(self.Baas_instance)
        elif method == "adb":
            self.control_instance = AdbControl(self.Baas_instance)
        elif method == "uiautomator2":
            self.control_instance = U2Control(self.Baas_instance)

    def click(self, x, y):
        self.control_instance.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.control_instance.swipe(x1, y1, x2, y2, duration)
