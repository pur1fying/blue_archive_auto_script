# -*- coding: utf-8 -*-
"""
hotkey_manager.py

A module providing a high-level, robust, and thread-safe manager for global
keyboard hotkeys within a PyQt application.

This module utilizes low-level Windows keyboard hooks (WH_KEYBOARD_LL) to capture
keyboard events system-wide, even when the application does not have focus. It
encapsulates all the complexity of ctypes, Win32 API interactions, and thread
management into a single, easy-to-use class.

Main Class:
    GlobalHotkeyManager: Manages the lifecycle of all registered hotkeys.

Key Features:
    - Simple, string-based hotkey registration (e.g., "Ctrl+Shift+Z").
    - Supports letters (A-Z), numbers (0-9), and common function/special keys.
    - Thread-safe: Register, unregister, and update hotkeys dynamically.
    - Includes a ready-to-use GUI Dialog (`HotkeyInputDialog`) for user-friendly
      hotkey configuration.
    - Fully encapsulated professional API with clear error handling.
"""

import ctypes
# --- Internal Dependencies (Hidden from the end-user) ---
from ctypes import wintypes
from typing import Callable, Dict, Set, Tuple, Optional, FrozenSet

# --- Qt Imports ---
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker, pyqtSlot, Qt, QEvent
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QWidget, QFrame
)
from qfluentwidgets import LineEdit, MessageBoxBase, MessageBox

# --- Win32 API Imports ---
try:
    import win32api
    import win32con
except ImportError:
    raise ImportError(
        "The 'pywin32' library is required. Please install it using: "
        "'pip install pywin32'"
    )

# --- Internal Type Definitions for Clarity ---
_VK_CODE = int
_MODIFIERS_SET = FrozenSet[_VK_CODE]
_HOTKEY_TUPLE = Tuple[_MODIFIERS_SET, _VK_CODE]
_Callback = Callable[[], None]
_HotkeyRegistry = Dict[_HOTKEY_TUPLE, _Callback]


# --- Internal Implementation Details (Private Classes) ---

class _KBDLLHOOKSTRUCT(ctypes.Structure):
    """Internal CTypes structure for WH_KEYBOARD_LL hook."""
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


_LPKBDLLHOOKSTRUCT = ctypes.POINTER(_KBDLLHOOKSTRUCT)
_LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


class _KeyboardHookThread(QThread):
    """
    Internal worker thread that runs the Windows message loop and hosts the
    keyboard hook. This class is an implementation detail of GlobalHotkeyManager.
    """
    hotkey_triggered = pyqtSignal(object)

    def __init__(self, hotkey_registry: _HotkeyRegistry, lock: QMutex, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._hotkey_registry = hotkey_registry
        self._lock = lock
        self._hook_handle = 0
        self._native_thread_id = 0
        self._hook_proc_ptr = _LowLevelKeyboardProc(self._hook_procedure)

    def _hook_procedure(self, nCode: int, wParam: int, lParam: int) -> int:
        """The callback function that Windows calls for every keyboard event."""
        if nCode == win32con.HC_ACTION:
            if wParam in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
                kbd_struct = ctypes.cast(lParam, _LPKBDLLHOOKSTRUCT).contents

                pressed_modifiers: Set[_VK_CODE] = set()
                if win32api.GetKeyState(win32con.VK_CONTROL) < 0:
                    pressed_modifiers.add(win32con.VK_CONTROL)
                if win32api.GetKeyState(win32con.VK_SHIFT) < 0:
                    pressed_modifiers.add(win32con.VK_SHIFT)
                if win32api.GetKeyState(win32con.VK_MENU) < 0:
                    pressed_modifiers.add(win32con.VK_MENU)
                if win32api.GetKeyState(win32con.VK_LWIN) < 0 or win32api.GetKeyState(win32con.VK_RWIN) < 0:
                    pressed_modifiers.add(win32con.VK_LWIN)

                current_key = (frozenset(pressed_modifiers), kbd_struct.vkCode)

                with QMutexLocker(self._lock):
                    if current_key in self._hotkey_registry:
                        self.hotkey_triggered.emit(current_key)

        # Cast wParam and lParam to void pointers for CallNextHookEx, as requested.
        c_wParam = ctypes.c_void_p(wParam)
        c_lParam = ctypes.c_void_p(lParam)

        return ctypes.windll.user32.CallNextHookEx(self._hook_handle, nCode, c_wParam, c_lParam)

    def run(self):
        """Thread's main execution function."""
        self._native_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        # Explicitly use ctypes.windll as requested.
        hMod = win32api.GetModuleHandle(None)
        hMod = ctypes.c_void_p(hMod)

        self._hook_handle = ctypes.windll.user32.SetWindowsHookExW(
            win32con.WH_KEYBOARD_LL,
            self._hook_proc_ptr,
            hMod,
            0
        )

        if not self._hook_handle:
            print(f"ERROR: SetWindowsHookExW failed with code: {ctypes.windll.kernel32.GetLastError()}")
            return

        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook_handle:
            ctypes.windll.user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = 0

    def stop(self):
        """Gracefully stops the thread."""
        if self._native_thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._native_thread_id, win32con.WM_QUIT, 0, 0)


# --- Public API Classes ---

class GlobalHotkeyManager(QObject):
    """
    A high-level manager for system-wide keyboard hotkeys.
    """
    _MODIFIER_MAP = {
        'ctrl': win32con.VK_CONTROL, 'shift': win32con.VK_SHIFT,
        'alt': win32con.VK_MENU, 'win': win32con.VK_LWIN,
    }
    _VK_TO_MODIFIER_MAP = {v: k.capitalize() for k, v in _MODIFIER_MAP.items()}

    _KEY_MAP = {
        'esc': win32con.VK_ESCAPE, 'f1': win32con.VK_F1, 'f2': win32con.VK_F2,
        'f3': win32con.VK_F3, 'f4': win32con.VK_F4, 'f5': win32con.VK_F5,
        'f6': win32con.VK_F6, 'f7': win32con.VK_F7, 'f8': win32con.VK_F8,
        'f9': win32con.VK_F9, 'f10': win32con.VK_F10, 'f11': win32con.VK_F11,
        'f12': win32con.VK_F12, 'tab': win32con.VK_TAB, 'enter': win32con.VK_RETURN,
        'space': win32con.VK_SPACE, 'backspace': win32con.VK_BACK,
        'delete': win32con.VK_DELETE, 'insert': win32con.VK_INSERT,
        'home': win32con.VK_HOME, 'end': win32con.VK_END,
        'pageup': win32con.VK_PRIOR, 'pagedown': win32con.VK_NEXT,
        'left': win32con.VK_LEFT, 'right': win32con.VK_RIGHT,
        'up': win32con.VK_UP, 'down': win32con.VK_DOWN,
    }
    VK_TO_KEY_MAP = {v: k.capitalize() for k, v in _KEY_MAP.items()}

    QT_TO_VK_MAP = {
        Qt.Key_Control: win32con.VK_CONTROL,
        Qt.Key_Shift: win32con.VK_SHIFT,
        Qt.Key_Alt: win32con.VK_MENU,
        Qt.Key_Meta: win32con.VK_LWIN,  # Meta key (Windows key)
        Qt.Key_Escape: win32con.VK_ESCAPE,
        Qt.Key_F1: win32con.VK_F1, Qt.Key_F2: win32con.VK_F2,
        Qt.Key_F3: win32con.VK_F3, Qt.Key_F4: win32con.VK_F4,
        Qt.Key_F5: win32con.VK_F5, Qt.Key_F6: win32con.VK_F6,
        Qt.Key_F7: win32con.VK_F7, Qt.Key_F8: win32con.VK_F8,
        Qt.Key_F9: win32con.VK_F9, Qt.Key_F10: win32con.VK_F10,
        Qt.Key_F11: win32con.VK_F11, Qt.Key_F12: win32con.VK_F12,
        Qt.Key_Tab: win32con.VK_TAB,
        Qt.Key_Return: win32con.VK_RETURN,
        Qt.Key_Space: win32con.VK_SPACE,
        Qt.Key_Backspace: win32con.VK_BACK,
        Qt.Key_Delete: win32con.VK_DELETE,
        Qt.Key_Insert: win32con.VK_INSERT,
        Qt.Key_Home: win32con.VK_HOME,
        Qt.Key_End: win32con.VK_END,
        Qt.Key_PageUp: win32con.VK_PRIOR,
        Qt.Key_PageDown: win32con.VK_NEXT,
        Qt.Key_Left: win32con.VK_LEFT,
        Qt.Key_Right: win32con.VK_RIGHT,
        Qt.Key_Up: win32con.VK_UP,
        Qt.Key_Down: win32con.VK_DOWN,
    }

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._hotkey_registry: _HotkeyRegistry = {}
        self._hook_thread: Optional[_KeyboardHookThread] = None
        self._lock = QMutex()

    def _parse_hotkey_string(self, hotkey_str: str) -> _HOTKEY_TUPLE:
        """Parses a human-readable hotkey string."""
        parts = [part.strip().lower() for part in hotkey_str.split('+')]
        modifiers: Set[_VK_CODE] = set()
        main_key_str = ""

        for part in parts:
            if part in self._MODIFIER_MAP:
                modifiers.add(self._MODIFIER_MAP[part])
            elif not main_key_str:
                main_key_str = part
            else:
                raise ValueError(f"Invalid hotkey '{hotkey_str}': Only one main key allowed.")

        if not main_key_str:
            raise ValueError(f"Invalid hotkey '{hotkey_str}': Must include a main key.")

        vk_code = 0
        if main_key_str in self._KEY_MAP:
            vk_code = self._KEY_MAP[main_key_str]
        elif len(main_key_str) == 1:
            if 'a' <= main_key_str <= 'z' or '0' <= main_key_str <= '9':
                # VK codes for A-Z and 0-9 are their ASCII values.
                vk_code = ord(main_key_str.upper())

        if not vk_code:
            raise ValueError(f"Unsupported main key: '{main_key_str}' in '{hotkey_str}'.")

        return (frozenset(modifiers), vk_code)

    def _format_hotkey_tuple(self, hotkey_tuple: _HOTKEY_TUPLE) -> str:
        """Converts an internal hotkey tuple back to a human-readable string."""
        modifiers, vk_code = hotkey_tuple
        mod_names = [self._VK_TO_MODIFIER_MAP[mod] for mod in sorted(list(modifiers))]

        key_name = self.VK_TO_KEY_MAP.get(vk_code)
        if not key_name:
            # Check if it's A-Z or 0-9
            if ord('A') <= vk_code <= ord('Z') or ord('0') <= vk_code <= ord('9'):
                key_name = chr(vk_code)

        if not key_name:
            return "Invalid Hotkey"

        return "+".join(mod_names + [key_name])

    @pyqtSlot(object)
    def _on_hotkey_triggered(self, hotkey_tuple: _HOTKEY_TUPLE):
        """Internal slot to safely execute user callbacks."""
        with QMutexLocker(self._lock):
            callback = self._hotkey_registry.get(hotkey_tuple)

        if callback and callable(callback):
            try:
                callback()
            except Exception as e:
                print(f"ERROR: Exception in hotkey callback for {hotkey_tuple}: {e}")

    def register(self, hotkey_str: str, callback: _Callback):
        """Registers a global hotkey."""
        key = self._parse_hotkey_string(hotkey_str)
        with QMutexLocker(self._lock):
            if key in self._hotkey_registry:
                raise KeyError(f"Hotkey '{hotkey_str}' is already registered.")
            self._hotkey_registry[key] = callback

    def unregister(self, hotkey_str: str):
        """Unregisters a global hotkey."""
        key = self._parse_hotkey_string(hotkey_str)
        with QMutexLocker(self._lock):
            if key not in self._hotkey_registry:
                raise KeyError(f"Hotkey '{hotkey_str}' is not registered.")
            del self._hotkey_registry[key]

    def update(self, old_hotkey_str: str, new_hotkey_str: str):
        """
        Atomically updates a hotkey from an old combination to a new one,
        preserving its callback function.
        """
        old_key = self._parse_hotkey_string(old_hotkey_str)
        new_key = self._parse_hotkey_string(new_hotkey_str)
        with QMutexLocker(self._lock):
            if old_key not in self._hotkey_registry:
                raise KeyError(f"Old hotkey '{old_hotkey_str}' is not registered.")
            if new_key in self._hotkey_registry and new_key != old_key:
                raise KeyError(f"New hotkey '{new_hotkey_str}' is already in use.")

            callback = self._hotkey_registry.pop(old_key)
            self._hotkey_registry[new_key] = callback

    def start(self):
        """Starts the hotkey listener thread."""
        with QMutexLocker(self._lock):
            if self._hook_thread and self._hook_thread.isRunning():
                return
            self._hook_thread = _KeyboardHookThread(self._hotkey_registry, self._lock)
            self._hook_thread.hotkey_triggered.connect(self._on_hotkey_triggered)
            self._hook_thread.start()

    def stop(self):
        """Stops the hotkey listener thread."""
        with QMutexLocker(self._lock):
            if self._hook_thread and self._hook_thread.isRunning():
                self._hook_thread.stop()
                self._hook_thread.wait(5000)
                self._hook_thread = None


class HotkeyCaptureInput(LineEdit):
    """A custom input widget that captures a key combination instead of text."""

    # Map Qt.Key values to their string representations for display.
    _QT_KEY_MAP = {
        Qt.Key_Control: 'Ctrl', Qt.Key_Shift: 'Shift',
        Qt.Key_Alt: 'Alt', Qt.Key_Meta: 'Win',
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._modifiers: Set[int] = set()
        self._main_key: int = 0
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setPlaceholderText("Click here and press a key combination")
        self._pressed_count = 0
        self._reset = False

    def keyPressEvent(self, event: QEvent):
        """Overrides QLineEdit's key press to capture combinations."""
        # print(GlobalHotkeyManager._VK_TO_KEY_MAP[
        #           GlobalHotkeyManager._QT_TO_VK_MAP[int(event.key())]])
        if self._reset:
            self.clear()
            self._reset = False
        key = event.key()
        if key in self._QT_KEY_MAP:
            self._modifiers.add(key)
        else:
            self._main_key = key
        self._update_display(key)
        event.accept()
        self._pressed_count += 1

    def keyReleaseEvent(self, event: QEvent):
        """Finalizes the hotkey if the main key is released."""
        # if not event.isAutoRepeat() and event.key() == self._main_key:
        #     # You can add logic here if needed, but for now, the display
        #     # is updated on press. The combination is "set".
        #     pass
        event.accept()
        self._pressed_count -= 1
        if self._pressed_count == 0:
            self._reset = True

    def clear(self):
        """Resets the captured hotkey."""
        super().clear()
        self._modifiers.clear()
        self._main_key = 0

    def _update_display(self, key_id: Optional[int] = None):
        """Updates the text to show the currently pressed combination."""
        mod_names = [self._QT_KEY_MAP[mod] for mod in sorted(list(self._modifiers))]
        r_key = None

        if key_id in GlobalHotkeyManager.QT_TO_VK_MAP:
            vk_key = GlobalHotkeyManager.QT_TO_VK_MAP[key_id]
            if vk_key in GlobalHotkeyManager.VK_TO_KEY_MAP:
                r_key = GlobalHotkeyManager.VK_TO_KEY_MAP[vk_key]

        # Qt.Key constants for A-Z and 0-9 are their ASCII values
        key_name = ""
        if Qt.Key_A <= self._main_key <= Qt.Key_Z or Qt.Key_0 <= self._main_key <= Qt.Key_9:
            key_name = chr(self._main_key)
        elif r_key is not None:
            key_name = r_key

        self.setText("+".join(mod_names + [key_name]))

    def get_hotkey_string(self) -> str:
        """Returns the captured hotkey as a string."""
        return self.text()


class HotkeyInputDialog(MessageBoxBase):
    """A dialog for capturing a new hotkey from the user."""

    def __init__(self, current_hotkey: str, parent: Optional[QWidget] = None,
                 hotkey_manager: Optional[GlobalHotkeyManager] = None):
        super().__init__(parent)
        """ Initializes the dialog with a hotkey input field. """
        self.viewLayout = QVBoxLayout(self)
        super().__init__(parent=parent)
        # self.setWindowTitle("Set New Hotkey")
        self.setModal(True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Press the desired key combination."))

        self.input_field = HotkeyCaptureInput(self)
        self.input_field.setText(current_hotkey)
        self.current_hotkey = current_hotkey
        layout.addWidget(self.input_field)

        # Create a frame to wrap the provided layout
        frame = QFrame(self)
        layout_wrapper = QVBoxLayout(frame)
        layout_wrapper.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout_wrapper.setSpacing(15)  # Set spacing to zero
        layout_wrapper.addLayout(layout)  # Add the provided layout to the wrapper
        frame.setLayout(layout_wrapper)

        # Add the frame to the dialog's main layout
        self.viewLayout.addWidget(frame)
        self.new_hotkey = ""
        self.manager = hotkey_manager

    def accept(self):
        """Overrides accept to validate and store the new hotkey."""
        hotkey_text = self.input_field.get_hotkey_string()
        self.new_hotkey = hotkey_text
        if not hotkey_text or "+" not in hotkey_text:
            MessageBox(
                parent=self, title="❗Invalid Hotkey",
                content="A valid hotkey must include at least one modifier (Ctrl, Shift, Alt)."
            ).show()
            # self.input_field.info
            return

        try:
            self.manager.update(self.current_hotkey, self.new_hotkey)
        except KeyError as e:
            MessageBox(
                parent=self, title="❗Error",
                content=f"Could not update hotkey: {e}"
            ).show()
            return
        except ValueError as e:
            MessageBox(
                parent=self, title="❗Error",
                content=f"Invalid hotkey format: {e}"
            ).show()
            return
        self.new_hotkey = hotkey_text
        super().accept()

    @staticmethod
    def get_hotkey(parent: QWidget, current_hotkey: str,
                   hotkey_manager: GlobalHotkeyManager) -> Tuple[Optional[str], bool]:
        """Static method to show the dialog and get the result."""
        dialog = HotkeyInputDialog(current_hotkey, parent, hotkey_manager)
        if dialog.exec_() == MessageBoxBase.Accepted:
            return dialog.new_hotkey, True
        return None, False

    def enterEvent(self, a0):
        self.input_field.setFocus()
