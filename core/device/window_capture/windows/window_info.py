import time
import ctypes
from ctypes.wintypes import RECT

import pyautogui

class win32_WindowInfo:
    def __init__(self, possible_window_title):
        if type(possible_window_title) is str:
            self._possible_window_titles = [possible_window_title]
        else:
            self._possible_window_titles = possible_window_title
        self._window_title = ""
        self._window = None
        self._hwnd = None
        self._region = None
        self._init_window()

    def get_resolution(self):
        self.activate_window()
        self.update_region()
        return self._region[2] - self._region[0], self._region[3] - self._region[1]

    def is_valid_window(self):
        if self._hwnd is None:
            return False
        return ctypes.windll.user32.IsWindow(self._hwnd)

    def _init_window(self):
        # check if current window is still valid
        if self._window is not None and self.is_valid_window():
            length = ctypes.windll.user32.GetWindowTextLengthW(self._hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(self._hwnd, buffer, length + 1)
                if buffer.value == self._window_title:
                    return
        # search for window
        for title in self._possible_window_titles:
            self._window = pyautogui.getWindowsWithTitle(self._window_title)
            if self._window is not None:
                self._window_title = title
                break
        # ensure window title is fully matched
        for win in self._window:
            if win.title == self._window_title:
                self._window = win
                self._hwnd = win._hWnd
                self._init_region()
                return
        self._window = None
        self._hwnd = None
        self._region = None

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

    def update_region(self):
        self._init_region()

    def get_window_title(self):
        return self._window_title

    def get_possible_window_titles(self):
        return self._possible_window_titles

    def get_window(self):
        return self._window

    def get_region(self):
        return self._region

    def activate_window(self):
        self._init_window()
        if not self._window:
            return False
        if self._window.isActive:
            return True
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
        window_info = win32_WindowInfo("ブルーアーカイブ")
        for i in range(10):
            print(window_info._window.isActive)
            time.sleep(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
