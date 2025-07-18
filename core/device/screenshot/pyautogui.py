import cv2
import pyautogui
import numpy as np


class PyautoguiScreenshot:
    def __init__(self, conn):
        self._window = conn.app_process_window

    def screenshot(self):
        if self._window.get_window() is None:
            return None
        self._window._activate_window()
        screenshot_pil = pyautogui.screenshot().crop(self._window.get_region())
        return cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
