import math

import cv2
from core.device.scrcpy.core import Client
from core.device.scrcpy import const
from core.device.scrcpy.control import ControlSender
import threading
import time
from adbutils import adb


class ScrcpyError(Exception):
    pass


class ScrcpyClient:
    connections = dict()

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
        if serial not in ScrcpyClient.connections:
            ScrcpyClient.connections[serial] = ScrcpyClient(serial)
        return ScrcpyClient.connections[serial]

    @staticmethod
    def release_instance(serial):
        if serial in ScrcpyClient.connections:
            del ScrcpyClient.connections[serial]

    def screenshot(self):
        with self._scrcpy_control_socket_lock:
            # Wait new frame
            now = time.time()
            while 1:
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

    def get_connection(self):
        return self.connection

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
        step_len, step_delay = self.get_swipe_params(x1, y1, x2, y2, duration)
        self.swipe_scrcpy(x1, y1, x2, y2, step_len, step_delay)

    def swipe_scrcpy(self, x1, y1, x2, y2, step_len, step_delay):
        with self._scrcpy_control_socket_lock:
            # Unlike minitouch, scrcpy swipes needs to be continuous
            # So 5 times smother
            points = self.insert_swipe_points(x1, y1, x2, y2, step_len)
            self._scrcpy_control.touch(x1, y1, const.ACTION_DOWN)

            for point in points[1:-1]:
                self._scrcpy_control.touch(*point, const.ACTION_MOVE)
                time.sleep(step_delay)

            self._scrcpy_control.touch(x2, y2, const.ACTION_UP)

    @staticmethod
    def get_swipe_params(x1, y1, x2, y2, duration) -> tuple[float, list]:
        dis = (x2 - x1) ** 2 + (y2 - y1) ** 2
        sleep_delay = 0.005
        if dis <= 25:
            step_len = 5
        else:
            total_steps = int(duration * 1000) // 5
            dis = math.sqrt(dis)
            step_len = int(dis / total_steps) + 1
            if step_len < 5:
                step_len = 5
                total_steps = dis // 5
                sleep_delay = duration / total_steps
        return step_len, sleep_delay

    @staticmethod
    def insert_swipe_points(x1, y1, x2, y2, step_len) -> list:
        points = list()
        points.append((x1, y1))
        dis = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if dis < step_len ** 2:
            points.append((x2, y2))
            return points
        step_num = int(math.sqrt(dis) / step_len)
        dx = (x2 - x1) / step_num
        dy = (y2 - y1) / step_num
        for i in range(1, step_num):
            points.append((int(x1 + dx * i), int(y1 + dy * i)))
        points.append((x2, y2))
        return points
