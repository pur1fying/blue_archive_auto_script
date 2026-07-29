from PyQt5.QtCore import QEvent
from PyQt5.QtTest import QTest


def test_window_minimize_uses_real_tray_controller(
    qapp, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    import window as window_module
    from gui.util.config_gui import configGui
    from gui.util.tray import TrayController

    monkeypatch.setattr(
        window_module.Window, "init_main_class", lambda self: None
    )
    monkeypatch.setattr(
        window_module,
        "TrayController",
        lambda window, icon: TrayController(
            window,
            icon,
            tray_available=lambda: True,
        ),
    )
    configGui.set(configGui.minimizeToTray, False, save=False)
    window = window_module.Window()
    try:
        configGui.set(configGui.minimizeToTray, True, save=False)
        assert window.tray_controller.tray_icon.isVisible()

        with monkeypatch.context() as patch:
            patch.setattr(
                window_module.Window, "isMinimized", lambda self: True
            )
            window.changeEvent(QEvent(QEvent.WindowStateChange))
        QTest.qWait(50)
        assert not window.isVisible()

        window.tray_controller.show_window()
        assert window.isVisible()
        assert not window.isMinimized()

        window.close()
        qapp.processEvents()
        assert not window.isVisible()
    finally:
        configGui.set(configGui.minimizeToTray, False, save=False)
