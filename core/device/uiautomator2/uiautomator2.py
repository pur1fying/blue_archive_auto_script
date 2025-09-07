import base64

import cv2
import numpy as np
import uiautomator2 as u2


class U2Client:
    clients = dict()

    @staticmethod
    def get_instance(serial):
        if serial not in U2Client.clients:
            U2Client.clients[serial] = U2Client(serial)
        return U2Client.clients[serial]

    @staticmethod
    def release_instance(serial):
        if serial in U2Client.clients:
            del U2Client.clients[serial]

    def __init__(self, serial):
        self.serial = serial
        if ":" in serial:
            self.connection = u2.connect(serial)
        else:
            self.connection = u2.connect_usb(serial)
        U2Client.clients[serial] = self

    def click(self, x, y):
        self.connection.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.connection.swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        self.connection.swipe(x, y, x, y, duration)

    def screenshot(self):
        # copied and modified from uiautomator2 source code
        # original version do not support unadjusted screenshot
        base64_data = self.connection.jsonrpc.takeScreenshot(1, 100)
        # takeScreenshot may return None
        # so we need a fallback method here
        if base64_data:
            jpg_raw = base64.b64decode(base64_data)
            img_array = np.frombuffer(jpg_raw, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        else:
            # fallback to the screencap method
            return self.connection._dev.screenshot()
