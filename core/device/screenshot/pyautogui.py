import cv2
import pyautogui
import numpy as np


class PyautoguiScreenshot:
    def __init__(self, conn):
        self._window = conn.app_process_window
        self.logger = conn.logger

    def screenshot(self):
        self._ensure_window()
        screenshot_pil = pyautogui.screenshot().crop(self._window.get_region())
        return cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)

    def _ensure_window(self):
        if not self._window.activate_window():
            if self._window.get_window() is None:
                self.logger.error(
                    f"[PyAutoGUI Control] No active window found. Please check any of the process is running.")
                for name in self._window.get_possible_window_titles():
                    self.logger.error(f"{name}")
                raise PyautoguiScreenshotError(f"App window not found")
            self.logger.warning(f"[PyAutoGUI Control] Failed to activate process [{self._window.get_window_title()}] window.")
        self._window.update_region()

class PyautoguiScreenshotError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"PyautoguiScreenshotError: {self.message}"
