from core.device.control.nemu import NemuControl
from core.device.control.adb import AdbControl
from core.device.control.uiautomator2 import U2Control
from core.device.control.scrcpy import ScrcpyControl

class Control:
    def __init__(self, Baas_instance):
        self.Baas_instance = Baas_instance
        self.connection = Baas_instance.connection

        self.config = Baas_instance.get_config()
        self.method = self.config.get("control_method")
        self.logger = Baas_instance.get_logger()
        self.control_instance = None
        self.init_control_instance()

    def init_control_instance(self):
        self.logger.info("Control method : " + self.method)
        if self.method == "nemu":
            self.control_instance = NemuControl(self.connection)
        elif self.method == "adb":
            self.control_instance = AdbControl(self.connection)
        elif self.method == "uiautomator2":
            self.control_instance = U2Control(self.connection)
        elif self.method == "scrcpy":
            self.control_instance = ScrcpyControl(self.connection)

    def click(self, x, y):
        self.control_instance.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.control_instance.swipe(x1, y1, x2, y2, duration)
