from adbutils import adb
from core.device.connection import Connection
import time


class AdbControl:
    def __init__(self, conn):
        self.serial = conn.serial
        self.adb = adb.device(self.serial)
        self.display_id = None

    def set_display_id(self, display_id):
        self.display_id = display_id

    def _build_input_cmd(self, action_cmd: str) -> str:
        if self.display_id:
            return f"input -d {self.display_id} {action_cmd}"
        else:
            return f"input {action_cmd}"

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
