import mss
import cv2
import numpy as np


class MssScreenshot:
    def __init__(self, conn):
        self._window = conn.app_process_window
        self._sct = mss.mss()

    def screenshot(self):
        if self._window.get_window() is None:
            return None
        self._window._activate_window()
        screenshot_pil = self._sct.grab(self._window.get_region())
        return cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_BGRA2BGR)

