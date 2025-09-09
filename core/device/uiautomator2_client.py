import base64

import cv2
import numpy as np
import uiautomator2 as u2


class U2Client:
    connections = dict()

    def __init__(self, serial):
        self.serial = serial
        if ":" in serial:
            self.connection = u2.connect(serial)
        else:
            self.connection = u2.connect_usb(serial)

    @staticmethod
    def get_instance(serial):
        if serial not in U2Client.connections:
            U2Client.connections[serial] = U2Client(serial)
        return U2Client.connections[serial]

    @staticmethod
    def release_instance(serial):
        if serial in U2Client.connections:
            del U2Client.connections[serial]

    def click(self, x, y):
        self.connection.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.connection.swipe(x1, y1, x2, y2, duration)

    def screenshot(self):
        # copied and modified from uiautomator2 source code
        # original version do not support unadjusted screenshot
        base64_data = self.connection.jsonrpc.takeScreenshot(1, 100)
        # takeScreenshot may return None
        if base64_data:
            jpg_raw = base64.b64decode(base64_data)
            img_array = np.frombuffer(jpg_raw, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        else:
            return None

    def get_connection(self):
        return self.connection
