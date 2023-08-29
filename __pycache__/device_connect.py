import uiautomator2 as u2

class device_connecter:
    def __init__(self):
        self.device = u2.connect()

