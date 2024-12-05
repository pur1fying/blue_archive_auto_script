from core.device.scrcpy_client import ScrcpyClient


class ScrcpyScreenshot:
    def __init__(self, conn):
        self.serial = conn.serial
        self.cli = ScrcpyClient.get_instance(self.serial)

    def screenshot(self):
        return self.cli.screenshot()
