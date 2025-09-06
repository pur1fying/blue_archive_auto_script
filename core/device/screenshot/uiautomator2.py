from core.device.uiautomator2.uiautomator2_client import U2Client


class U2Screenshot:
    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def screenshot(self):
        for i in range(5):
            try:
                screenshot = self.u2.screenshot()
                if screenshot is not None:
                    return screenshot
            except Exception as e:
                print(e)
