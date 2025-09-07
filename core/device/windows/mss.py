import mss
import cv2
import numpy as np


class MssScreenshot:
    def __init__(self, conn):
        self._window = conn.app_process_window
        self._sct = mss.mss()
        self.logger = conn.logger

    def screenshot(self):
        self._ensure_window()
        screenshot_pil = self._sct.grab(self._window.get_region())
        return cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_BGRA2BGR)

    def _ensure_window(self):
        if not self._window.activate_window():
            if self._window.get_window() is None:
                self.logger.error(f"[MSS Screenshot] No active window found. Please check if your process [{self._window.get_window_title()}] is running.")
                raise MssScreenshotError(f"App window not found")
            self.logger.warning(f"[MSS Screenshot] Failed to activate process [{self._window.get_window_title()}] window.")
        self._window.update_region()

class MssScreenshotError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"MssScreenshotError: {self.message}"
