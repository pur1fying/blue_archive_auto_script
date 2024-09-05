from core.device.uiautomator2_client import U2Client


class U2Control:
    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def click(self, x, y):
        self.u2.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.u2.swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        self.u2.swipe(x, y, x, y, duration)
