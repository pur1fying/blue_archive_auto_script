import cv2
import time
import ctypes
import pyautogui
from ctypes.wintypes import RECT


class win32_WindowInfo:
    def __init__(self, window_title):
        self._window_title = window_title
        self._window = None
        self._hwnd = None
        self._region = None
        self._init_window()

    def get_resolution(self):
        return self._region[2] - self._region[0], self._region[3] - self._region[1]

    def is_valid_window(self):
        if self._hwnd is None:
            return False
        return ctypes.windll.user32.IsWindow(self._hwnd)

    def _init_window(self):
        self._window = pyautogui.getWindowsWithTitle(self._window_title)
        if len(self._window) == 0:
            self._window = None
            self._hwnd = None
            self._region = None
            return
        self._window = self._window[0]
        self._hwnd = self._window._hWnd
        self._init_region()

    def _init_region(self):
        client_rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetClientRect(self._hwnd, ctypes.byref(client_rect))
        left_top_pos = ctypes.wintypes.POINT(client_rect.left, client_rect.top)
        ctypes.windll.user32.ClientToScreen(self._hwnd, ctypes.byref(left_top_pos))
        self._region = (
            left_top_pos.x,
            left_top_pos.y,
            left_top_pos.x + client_rect.right,
            left_top_pos.y + client_rect.bottom,
        )
        print(f"Region: {self._region}")

    def get_window(self):
        return self._window

    def get_region(self):
        return self._region

    def _activate_window(self):
        self._init_window()
        if not self._window:
            return False
        try:
            return self._try_activate_window()
        except Exception:
            self._window.minimize()
        try:
            return self._try_activate_window()
        except Exception:
            return False

    def _try_activate_window(self):
        self._window.restore()
        self._window.activate()
        for _ in range(10):
            if self._window.isActive:
                return True
            time.sleep(0.001)
        return False


if __name__ == "__main__":
    try:
        window_info = win32_WindowInfo("clash for windows")
        window_info._activate_window()

        screenshot = window_info._pyautogui_screenshot()
        screenshot_mss = window_info._mss_screenshot()
        screenshot_dxcam = window_info._dxcam_screenshot()
        cv2.imshow("Screenshot PyAutoGUI", screenshot)
        cv2.imshow("Screenshot MSS", screenshot_mss)
        cv2.imshow("Screenshot DXCam", screenshot_dxcam)
        cv2.waitKey(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
