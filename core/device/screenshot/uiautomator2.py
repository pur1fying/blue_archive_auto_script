from core.device.uiautomator2_client import U2Client


class U2Screenshot:
    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def screenshot(self):
        for i in range(5):
            try:
                return self.u2.screenshot()
            except Exception as e:
                print(e)
