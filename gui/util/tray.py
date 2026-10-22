from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayController(QObject):
    def __init__(
        self,
        window,
        icon=None,
        tray_available=None,
        quit_callback=None,
    ):
        super().__init__(window)
        self.window = window
        self._enabled = False
        self._tray_available = (
            tray_available or QSystemTrayIcon.isSystemTrayAvailable
        )
        app = QApplication.instance()
        self._quit_callback = (
            quit_callback
            or (app.quit if app is not None else lambda: None)
        )
        self.tray_icon = QSystemTrayIcon(icon or QIcon(), self)
        self.tray_icon.setToolTip("BlueArchiveAutoScript")

        self.menu = QMenu(window)
        self.show_action = self.menu.addAction(self.tr("显示主窗口"))
        self.hide_action = self.menu.addAction(self.tr("隐藏主窗口"))
        self.exit_action = self.menu.addAction(self.tr("退出"))
        self.tray_icon.setContextMenu(self.menu)

        self.show_action.triggered.connect(self.show_window)
        self.hide_action.triggered.connect(self.hide_window)
        self.exit_action.triggered.connect(self.exit_application)
        self.tray_icon.activated.connect(self._on_activated)

    def set_enabled(self, enabled):
        was_enabled = self._enabled
        self._enabled = bool(enabled)
        if self._enabled and self._tray_available():
            self.tray_icon.show()
            return
        self.tray_icon.hide()
        if (
            was_enabled
            and not self._enabled
            and not self.window.isVisible()
        ):
            self.show_window()

    def handle_window_state_change(self):
        if (
            not self._enabled
            or not self._tray_available()
            or not self.window.isMinimized()
        ):
            return False
        if not self.tray_icon.isVisible():
            self.tray_icon.show()
        if not self.tray_icon.isVisible():
            return False
        QTimer.singleShot(0, self._hide_minimized_window)
        return True

    def _hide_minimized_window(self):
        if (
            self._enabled
            and self._tray_available()
            and self.tray_icon.isVisible()
            and self.window.isMinimized()
        ):
            self.window.hide()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def toggle_window(self):
        if self.window.isVisible() and not self.window.isMinimized():
            self.hide_window()
        else:
            self.show_window()

    def show_window(self):
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def hide_window(self):
        if self._enabled and self._tray_available():
            self.window.hide()

    def exit_application(self):
        self.tray_icon.hide()
        self._quit_callback()
