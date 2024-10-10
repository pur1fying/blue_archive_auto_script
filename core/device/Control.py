from core.device.control.nemu import NemuControl
from core.device.control.adb import AdbControl
from core.device.control.uiautomator2 import U2Control


class Control:
    def __init__(self, Baas_instance):
        self.Baas_instance = Baas_instance
        self.connection = Baas_instance.connection

        self.config = Baas_instance.get_config()
        self.logger = Baas_instance.get_logger()
        self.control_instance = None
        self.init_control_instance()

    def init_control_instance(self):
        method = self.config.get("control_method")
        self.logger.info("Control method : " + method)
        if method == "nemu":
            self.control_instance = NemuControl(self.connection)
        elif method == "adb":
            self.control_instance = AdbControl(self.connection)
        elif method == "uiautomator2":
            self.control_instance = U2Control(self.connection)

    def click(self, x, y):
        self.control_instance.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.control_instance.swipe(x1, y1, x2, y2, duration)
