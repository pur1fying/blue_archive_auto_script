import ctypes
import time
from functools import lru_cache

import cv2
import numpy as np
import pyautogui


class PyautoguiControlError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"PyautoguiControlError: {self.message}"


class PyautoguiScreenshotError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"PyautoguiScreenshotError: {self.message}"


class PyautoguiClient:
    def __init__(self, conn):
        self._window = conn.app_process_window
        self.logger = conn.logger
        pyautogui.FAILSAFE = False

    def click(self, x, y):
        self._ensure_window()
        x, y = self._convert_screen_p_to_window_p(x, y)
        self._click(x, y, 0, True)

    def swipe(self, x1, y1, x2, y2, duration):
        self._ensure_window()
        x1, y1 = self._convert_screen_p_to_window_p(x1, y1)
        x2, y2 = self._convert_screen_p_to_window_p(x2, y2)
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=duration)

    def scroll(self, x, y, clicks):
        self._ensure_window()
        x, y = self._convert_screen_p_to_window_p(x, y)
        d = 2000 if get_mouse_sensitivity() <= 10 else 1000
        pyautogui.scroll(-d * clicks, x=x, y=y)

    def long_click(self, x, y, duration):
        self._ensure_window()
        x, y = self._convert_screen_p_to_window_p(x, y)
        self._click(x, y, duration, True)

    def _convert_screen_p_to_window_p(self, x, y):
        ulx, uly, _, _ = self._window.get_region()
        return ulx + x, uly + y

    def _ensure_window(self):
        if not self._window.activate_window():
            if self._window.get_window() is None:
                self.logger.error(
                    f"[PyAutoGUI Control] No active window found. Please check if your process [{self._window.get_window_title()}] is running.")
                raise PyautoguiControlError(f"App window not found")
            self.logger.warning(
                f"[PyAutoGUI Control] Failed to activate process [{self._window.get_window_title()}] window.")
        self._window.update_region()

    def screenshot(self):
        self._ensure_window()
        screenshot_pil = pyautogui.screenshot().crop(self._window.get_region())
        return cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _click(x, y, duration, is_primary=True):
        btn = pyautogui.PRIMARY if is_primary else pyautogui.SECONDARY
        if duration > 0:
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown(button=btn)
            time.sleep(duration)
            pyautogui.mouseUp(button=btn)
        else:
            pyautogui.click(x, y, button=btn)


@lru_cache
def get_mouse_sensitivity():
    user32 = ctypes.windll.user32
    speed = ctypes.c_int()
    user32.SystemParametersInfoA(0x0070, 0, ctypes.byref(speed), 0)
    return speed.value
