import uiautomator2 as u2
import cv2
import numpy as np


class U2Client:
    connections = dict()

    @staticmethod
    def get_instance(serial):
        if serial not in U2Client.connections:
            U2Client.connections[serial] = U2Client(serial)
        return U2Client.connections[serial]

    @staticmethod
    def release_instance(serial):
        if serial in U2Client.connections:
            del U2Client.connections[serial]

    def __init__(self, serial):
        self.serial = serial
        if ":" in serial:
            self.connection = u2.connect(serial)
        else:
            self.connection = u2.connect_usb(serial)

    def click(self, x, y):
        self.connection.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.connection.swipe(x1, y1, x2, y2, duration)

    def screenshot(self):
        return cv2.cvtColor(np.array(self.connection.screenshot()), cv2.COLOR_RGB2BGR)

    def get_connection(self):
        return self.connection
