from core.device.connection import Connection
from core.Baas_thread import Baas_thread
from adbutils import adb


class AdbScreenshot(Connection):
    def __init__(self, Baas_instance: Baas_thread):
        super().__init__(Baas_instance)
        self.adb = adb.device(self.serial)

    def screenshot(self):
        return self.adb.screencap()

