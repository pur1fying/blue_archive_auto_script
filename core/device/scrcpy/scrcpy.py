from core.device.scrcpy.scrcpy_client import ScrcpyClient


class ScrcpyControl:
    def __init__(self, conn):
        self.serial = conn.serial
        self.cli = ScrcpyClient.get_instance(self.serial)

    def click(self, x, y):
        self.cli.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.cli.swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        self.cli.long_click(x, y, duration)

