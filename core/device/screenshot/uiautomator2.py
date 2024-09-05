from core.device.uiautomator2_client import U2Client
from core.device.connection import Connection
from core.Baas_thread import Baas_thread


class U2Screenshot(Connection):
    def __init__(self, Baas_instance: Baas_thread):
        super().__init__(Baas_instance)
        self.u2 = U2Client.get_instance(self.serial)

    def screenshot(self):
        return self.u2.screenshot()
