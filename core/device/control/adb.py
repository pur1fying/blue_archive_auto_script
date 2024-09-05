from adbutils import adb
from core.device.connection import Connection
import time


class AdbControl(Connection):
    def __init__(self, Baas_instance):
        super().__init__(Baas_instance)
        self.adb = adb.device(self.serial)

    def click(self, x, y):
        start_t = time.time()
        self.adb.shell(f'input tap {x} {y}')
        if time.time() - start_t < 0.05:
            time.sleep(0.05)

    def swipe(self, x1, y1, x2, y2, duration):
        duration = int(duration * 1000)
        self.adb.shell(f'input swipe {x1} {y1} {x2} {y2} {duration}')

    def long_click(self, x, y, duration):
        duration = int(duration * 1000)
        self.adb.shell(f'input swipe {x} {y} {x} {y} {duration}')
