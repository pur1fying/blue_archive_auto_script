from PyQt5.QtGui import QIcon
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QWidget


def make_controller(window, available=True, quit_calls=None):
    from gui.util.tray import TrayController

    if quit_calls is None:
        quit_calls = []
    controller = TrayController(
        window,
        icon=QIcon(),
        tray_available=lambda: available,
        quit_callback=lambda: quit_calls.append(True),
    )
    return controller, quit_calls


def test_disabled_controller_keeps_normal_minimization(qapp):
    window = QWidget()
    controller, _ = make_controller(window)
    window.show()
    window.showMinimized()

    assert controller.handle_window_state_change() is False
    assert window.isVisible()
    assert not controller.tray_icon.isVisible()


def test_enabled_controller_hides_minimized_window(qapp):
    window = QWidget()
    controller, _ = make_controller(window)
    controller.set_enabled(True)
    window.show()
    window.showMinimized()

    assert controller.handle_window_state_change() is True
    QTest.qWait(20)
    assert not window.isVisible()
    assert controller.tray_icon.isVisible()


def test_unavailable_tray_never_hides_window(qapp):
    window = QWidget()
    controller, _ = make_controller(window, available=False)
    controller.set_enabled(True)
    window.show()
    window.showMinimized()

    assert controller.handle_window_state_change() is False
    assert window.isVisible()
    assert not controller.tray_icon.isVisible()


def test_tray_becoming_available_shows_icon_before_hiding(qapp):
    availability = {"value": False}
    window = QWidget()
    from gui.util.tray import TrayController

    controller = TrayController(
        window,
        icon=QIcon(),
        tray_available=lambda: availability["value"],
    )
    controller.set_enabled(True)
    window.show()
    window.showMinimized()

    availability["value"] = True
    assert controller.handle_window_state_change() is True
    assert controller.tray_icon.isVisible()
    QTest.qWait(20)
    assert not window.isVisible()


def test_disabling_cancels_a_deferred_hide(qapp):
    window = QWidget()
    controller, _ = make_controller(window)
    controller.set_enabled(True)
    window.show()
    window.showMinimized()

    assert controller.handle_window_state_change() is True
    controller.set_enabled(False)
    QTest.qWait(20)

    assert window.isVisible()
    assert not controller.tray_icon.isVisible()


def test_toggle_show_hide_and_disable_restore_window(qapp):
    window = QWidget()
    controller, _ = make_controller(window)
    controller.set_enabled(True)
    window.show()

    controller.toggle_window()
    assert not window.isVisible()
    controller.toggle_window()
    assert window.isVisible()
    assert not window.isMinimized()
    controller.hide_window()
    controller.set_enabled(False)
    assert window.isVisible()
    assert not controller.tray_icon.isVisible()


def test_menu_actions_and_exit_callback(qapp):
    window = QWidget()
    controller, quit_calls = make_controller(window)
    controller.set_enabled(True)
    window.show()

    controller.hide_action.trigger()
    assert not window.isVisible()
    controller.show_action.trigger()
    assert window.isVisible()
    controller.exit_action.trigger()
    assert quit_calls == [True]
    assert not controller.tray_icon.isVisible()
