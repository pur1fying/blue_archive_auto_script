import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def main():
    os.environ.pop("QT_QPA_PLATFORM", None)
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(
        prefix="baas-legacy-gui-smoke-"
    ) as runtime:
        os.chdir(runtime)
        window = None
        config_gui = None
        try:
            from PyQt5.QtCore import Qt
            from PyQt5.QtTest import QTest
            from PyQt5.QtWidgets import QApplication, QSystemTrayIcon

            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
            app = QApplication.instance() or QApplication([])

            import window as window_module
            from gui.components.expand.finalRestrictionRls import (
                Layout as FinalRestrictionLayout,
            )
            from gui.components.expand.friendWhiteList import (
                Layout as FriendClearLayout,
            )
            from gui.util.config_gui import configGui

            config_gui = configGui
            window_module.Window.init_main_class = lambda self: None
            window = window_module.Window()
            window.show()
            QTest.qWait(100)
            assert window.isVisible()
            assert hasattr(window, "tray_controller")

            account_config = window.config_dir_list[0]
            final_editor = FinalRestrictionLayout(window, account_config)
            friend_editor = FriendClearLayout(window, account_config)
            assert final_editor.formation_method_combo.count() == 2
            assert friend_editor.level_limit_spin.minimum() == -1

            configGui.set(configGui.minimizeToTray, True)
            assert QSystemTrayIcon.isSystemTrayAvailable()
            window.showMinimized()
            QTest.qWait(150)
            assert not window.isVisible()

            window.tray_controller.show_window()
            QTest.qWait(50)
            assert window.isVisible()
            assert not window.isMinimized()

            window.tray_controller.hide_action.trigger()
            assert not window.isVisible()
            window.tray_controller.show_action.trigger()
            assert window.isVisible()

            configGui.set(configGui.minimizeToTray, False)
            assert not window.tray_controller.tray_icon.isVisible()
            window.close()
            app.processEvents()
        finally:
            if config_gui is not None:
                config_gui.set(
                    config_gui.minimizeToTray, False, save=False
                )
            if window is not None:
                window.close()
                app.processEvents()
            os.chdir(original_cwd)


if __name__ == "__main__":
    main()
