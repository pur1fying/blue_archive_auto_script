from adbutils import adb
import cv2
import numpy as np


class AdbScreenshot:
    def __init__(self, conn):
        self.serial = conn.serial
        self.logger = conn.logger

        self.adb = adb.device(self.serial)

    def screenshot(self):
        data = self.adb.shell(['screencap', '-p'], stream=True)
        if len(data) < 500:
            self.logger.warning(f'Unexpected screenshot: {data}')
        image = np.frombuffer(data, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
        return image

