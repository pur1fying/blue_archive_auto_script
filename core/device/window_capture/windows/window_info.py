import time
import ctypes
from ctypes.wintypes import RECT

import pyautogui


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
    ]


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

    def get_resolution(self, activate=True):
        if activate:
            self.activate_window()
        else:
            self._init_window()
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
            windows = pyautogui.getWindowsWithTitle(title)
            # ensure window title is fully matched
            for win in windows:
                if win.title == title:
                    self._window = win
                    self._window_title = title
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

    def is_fullscreen_or_maximized(self):
        self._init_window()
        if not self.is_valid_window():
            return False
        if ctypes.windll.user32.IsZoomed(self._hwnd):
            return True
        window_rect = self._get_window_rect()
        monitor_rect = self._get_monitor_rect()
        if window_rect is None or monitor_rect is None:
            return False
        return (
            window_rect[0] <= monitor_rect[0] and
            window_rect[1] <= monitor_rect[1] and
            window_rect[2] >= monitor_rect[2] and
            window_rect[3] >= monitor_rect[3]
        )

    def resize_client_area(self, target_width=1280, target_height=720, max_retry=2, wait=0.5):
        if not self.activate_window():
            return False, (0, 0)
        self.update_region()
        if self._region is None:
            return False, (0, 0)

        target_client_left, target_client_top = self._region[0], self._region[1]
        final_resolution = self._client_size()
        for _ in range(max_retry + 1):
            self.update_region()
            client_width, client_height = self._client_size()
            final_resolution = (client_width, client_height)
            if final_resolution == (target_width, target_height):
                return True, final_resolution

            window_rect = self._get_window_rect()
            if window_rect is None:
                return False, final_resolution
            window_left, window_top, window_right, window_bottom = window_rect
            window_width = window_right - window_left
            window_height = window_bottom - window_top
            client_offset_x = self._region[0] - window_left
            client_offset_y = self._region[1] - window_top

            new_window_left = target_client_left - client_offset_x
            new_window_top = target_client_top - client_offset_y
            new_window_width = window_width + (target_width - client_width)
            new_window_height = window_height + (target_height - client_height)
            if not self._set_window_pos(new_window_left, new_window_top, new_window_width, new_window_height):
                return False, final_resolution
            time.sleep(wait)

        self.update_region()
        final_resolution = self._client_size()
        return final_resolution == (target_width, target_height), final_resolution

    def _client_size(self):
        if self._region is None:
            return 0, 0
        return self._region[2] - self._region[0], self._region[3] - self._region[1]

    def _get_window_rect(self):
        rect = RECT()
        if not ctypes.windll.user32.GetWindowRect(self._hwnd, ctypes.byref(rect)):
            return None
        return rect.left, rect.top, rect.right, rect.bottom

    def _get_monitor_rect(self):
        monitor_from_window = ctypes.windll.user32.MonitorFromWindow
        get_monitor_info = ctypes.windll.user32.GetMonitorInfoW
        monitor_default_to_nearest = 0x00000002
        monitor = monitor_from_window(self._hwnd, monitor_default_to_nearest)
        if not monitor:
            return None
        monitor_info = MONITORINFO()
        monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
        if not get_monitor_info(monitor, ctypes.byref(monitor_info)):
            return None
        rect = monitor_info.rcMonitor
        return rect.left, rect.top, rect.right, rect.bottom

    def _set_window_pos(self, left, top, width, height):
        swp_nozorder = 0x0004
        return ctypes.windll.user32.SetWindowPos(
            self._hwnd,
            0,
            int(left),
            int(top),
            int(width),
            int(height),
            swp_nozorder
        )

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
        window_info = win32_WindowInfo("BlueArchive")
        for i in range(10):
            print(window_info._window.isActive)
            print(window_info.is_valid_window())
            time.sleep(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
