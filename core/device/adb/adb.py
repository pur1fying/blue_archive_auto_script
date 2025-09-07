import time

import cv2
import numpy as np
from adbutils import adb


class AdbClient:
    clients = {}

    @staticmethod
    def get_instance(serial: str):
        if serial not in AdbClient.clients:
            AdbClient.clients[serial] = AdbClient(serial)
        return AdbClient.clients[serial]

    def __init__(self, serial: str):
        self.serial = serial
        self.connection = adb.device(self.serial)
        AdbClient.clients[serial] = self

    def click(self, x, y):
        start_t = time.time()
        self.connection.shell(f'input tap {x} {y}')
        if time.time() - start_t < 0.05:
            time.sleep(0.05)

    def swipe(self, x1, y1, x2, y2, duration):
        duration = int(duration * 1000)
        self.connection.shell(f'input swipe {x1} {y1} {x2} {y2} {duration}')

    def long_click(self, x, y, duration):
        duration = int(duration * 1000)
        self.connection.shell(f'input swipe {x} {y} {x} {y} {duration}')

    def screenshot(self):
        image = self.connection.screenshot()
        image_opencv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return image_opencv
