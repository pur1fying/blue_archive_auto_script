import math
import threading
import time

from adbutils import adb

from core.device.scrcpy import const
from core.device.scrcpy.control import ControlSender
from core.device.scrcpy.core import Client


class ScrcpyError(Exception):
    pass


class ScrcpyClient:
    clients = dict()

    def __init__(self, serial):
        self.serial = serial
        self._scrcpy_control_socket_lock = threading.Lock()
        self.connection = Client(adb.device(serial=serial))
        try:
            self.connection.start(threaded=True)
        except Exception as e:
            raise ScrcpyError(f"Failed to start scrcpy: {e}")
        self._scrcpy_control = ControlSender(self.connection)

    @staticmethod
    def get_instance(serial):
        if serial not in ScrcpyClient.clients:
            ScrcpyClient.clients[serial] = ScrcpyClient(serial)
        return ScrcpyClient.clients[serial]

    def screenshot(self):
        with self._scrcpy_control_socket_lock:
            # Wait new frame
            now = time.time()
            while True:
                time.sleep(0.001)
                thread = self.connection
                self.check_scrcpy_alive()
                if thread.last_frame_time > now:
                    screenshot = thread.last_frame.copy()
                    return screenshot

    def check_scrcpy_alive(self):
        thread = self.connection
        if thread is None or not thread.is_alive():
            raise ScrcpyError('_scrcpy_stream_loop_thread died')

    def click(self, x, y):
        self.check_scrcpy_alive()
        with self._scrcpy_control_socket_lock:
            self._scrcpy_control.touch(x, y, const.ACTION_DOWN)
            self._scrcpy_control.touch(x, y, const.ACTION_UP)
            time.sleep(0.05)

    def long_click(self, x, y, duration=1.0):
        with self._scrcpy_control_socket_lock:
            self._scrcpy_control.touch(x, y, const.ACTION_DOWN)
            time.sleep(duration)
            self._scrcpy_control.touch(x, y, const.ACTION_UP)
            time.sleep(0.05)

    def swipe(self, x1, y1, x2, y2, duration):
        dis = (x2 - x1) ** 2 + (y2 - y1) ** 2
        step_delay = 0.005
        if dis <= 25:
            step_len = 5
        else:
            total_steps = int(duration * 1000) // 5
            dis = math.sqrt(dis)
            step_len = int(dis / total_steps) + 1
            if step_len < 5:
                step_len = 5
                total_steps = dis // 5
                step_delay = duration / total_steps

        with self._scrcpy_control_socket_lock:
            # Unlike minitouch, scrcpy swipes needs to be continuous
            # So 5 times smother
            points = [(x1, y1)]
            dis = (x2 - x1) ** 2 + (y2 - y1) ** 2
            if dis < step_len ** 2:
                points.append((x2, y2))
            else:
                step_num = int(math.sqrt(dis) / step_len)
                dx = (x2 - x1) / step_num
                dy = (y2 - y1) / step_num
                for i in range(1, step_num):
                    points.append((int(x1 + dx * i), int(y1 + dy * i)))
                points.append((x2, y2))
            self._scrcpy_control.touch(x1, y1, const.ACTION_DOWN)

            for point in points[1:-1]:
                self._scrcpy_control.touch(*point, const.ACTION_MOVE)
                time.sleep(step_delay)

            self._scrcpy_control.touch(x2, y2, const.ACTION_UP)
