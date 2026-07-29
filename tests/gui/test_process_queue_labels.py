import re
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QAbstractItemView

import gui

PROJECT_ROOT = Path(__file__).resolve().parents[2]
gui.__path__.append(str(PROJECT_ROOT / "gui"))

from gui.fragments import process


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


class _AccountConfig:
    def get(self, key, default=None):
        return "default" if key == "new_event_enable_state" else default

    def get_main_thread(self):
        return None


class _ThreadTrackingFragment(process.ProcessFragment):
    def __init__(self, *args, **kwargs):
        self.queue_update_threads = []
        self.applied_update_threads = []
        self.close_started = threading.Event()
        super().__init__(*args, **kwargs)

    def _set_queue_items(self, task_list):
        self.queue_update_threads.append(threading.get_ident())
        super()._set_queue_items(task_list)

    def _apply_status_update(self, current_task, task_list):
        self.applied_update_threads.append(threading.get_ident())
        super()._apply_status_update(current_task, task_list)

    def closeEvent(self, event):
        self.close_started.set()
        super().closeEvent(event)


class _BlockingAccountConfig(_AccountConfig):
    def __init__(self):
        self.worker_entered = threading.Event()
        self.release_worker = threading.Event()

    def get_main_thread(self):
        self.worker_entered.set()
        assert self.release_worker.wait(timeout=5)
        return None


class _JoinRecordingThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.join_timeouts = []
        super().__init__(*args, **kwargs)

    def join(self, timeout=None):
        self.join_timeouts.append(timeout)
        return super().join(timeout)


def _wait_until(app, predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        QTest.qWait(20)
    app.processEvents()
    return bool(predicate())


@pytest.fixture
def fragment(app, monkeypatch):
    monkeypatch.setattr(process.threading.Thread, "start", lambda self: None)
    monkeypatch.setattr(
        process.expand.__dict__["featureSwitch"], "Layout",
        lambda config: process.QWidget())
    widget = process.ProcessFragment(None, _AccountConfig())
    widget.resize(700, 400)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(widget, QEvent.DeferredDelete)
    app.processEvents()


def test_queue_rows_are_enabled_non_selectable_labels(fragment):
    fragment._set_queue_items(["first task", "second task"])

    assert fragment.listWidget.selectionMode() == QAbstractItemView.NoSelection
    assert fragment.listWidget.focusPolicy() == Qt.NoFocus
    assert fragment.listWidget.count() == 2
    for row in range(fragment.listWidget.count()):
        assert fragment.listWidget.item(row).flags() == Qt.ItemIsEnabled


def test_queue_hover_and_click_never_select_rows(fragment, app):
    fragment._set_queue_items(["first task"])
    rect = fragment.listWidget.visualItemRect(fragment.listWidget.item(0))
    point = rect.center() if rect.isValid() else QPoint(5, 5)

    QTest.mouseMove(fragment.listWidget.viewport(), point)
    QTest.mouseClick(fragment.listWidget.viewport(), Qt.LeftButton, pos=point)
    app.processEvents()

    assert fragment.listWidget.currentItem() is None
    assert fragment.listWidget.selectedItems() == []


def test_queue_refresh_does_not_retain_a_current_row(fragment):
    fragment._set_queue_items(["old task"])
    fragment.listWidget.setCurrentRow(0)
    assert fragment.listWidget.currentItem() is not None

    fragment._set_queue_items(["new task"])

    assert fragment.listWidget.currentItem() is None
    assert fragment.listWidget.selectedItems() == []


def test_status_refresh_applies_widget_changes_only_on_gui_thread(
    app, monkeypatch
):
    monkeypatch.setattr(
        process.expand.__dict__["featureSwitch"], "Layout",
        lambda config: process.QWidget())
    widget = _ThreadTrackingFragment(None, _AccountConfig())
    widget.resize(700, 400)
    widget.show()
    try:
        assert _wait_until(app, lambda: widget.queue_update_threads)

        assert widget.queue_update_threads
        assert widget.applied_update_threads
        assert set(widget.queue_update_threads) == {threading.get_ident()}
        assert set(widget.applied_update_threads) == {threading.get_ident()}
    finally:
        widget.close()


def test_close_waits_for_blocked_worker_and_prevents_late_widget_updates(
    app, monkeypatch
):
    monkeypatch.setattr(
        process.expand.__dict__["featureSwitch"], "Layout",
        lambda config: process.QWidget())
    thread_api = SimpleNamespace(
        Event=threading.Event,
        Thread=_JoinRecordingThread,
        current_thread=threading.current_thread,
    )
    monkeypatch.setattr(process, "threading", thread_api)
    account = _BlockingAccountConfig()
    widget = _ThreadTrackingFragment(None, account)
    widget.resize(700, 400)
    widget.show()
    app.processEvents()
    status_thread = widget._status_thread
    assert isinstance(status_thread, _JoinRecordingThread)
    assert account.worker_entered.wait(timeout=3)
    assert status_thread.is_alive()

    def release_after_close_begins():
        assert widget.close_started.wait(timeout=3)
        account.release_worker.set()

    release_helper = threading.Thread(
        target=release_after_close_begins,
        name="scheduler-status-release-helper",
    )
    release_helper.start()
    try:
        widget.close()
        release_helper.join(timeout=3)

        assert not release_helper.is_alive()
        assert not status_thread.is_alive()
        assert status_thread.join_timeouts == [None]
        assert all(
            thread_id == threading.get_ident()
            for thread_id in widget.queue_update_threads
        )
        assert all(
            thread_id == threading.get_ident()
            for thread_id in widget.applied_update_threads
        )

        update_count = len(widget.queue_update_threads)
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(widget, QEvent.DeferredDelete)
        app.processEvents()

        assert sip.isdeleted(widget)
        assert len(widget.queue_update_threads) == update_count
    finally:
        account.release_worker.set()
        release_helper.join(timeout=3)
        if not sip.isdeleted(widget):
            widget.close()


def test_status_worker_can_request_its_own_stop_without_self_join(
    app, monkeypatch
):
    monkeypatch.setattr(
        process.expand.__dict__["featureSwitch"], "Layout",
        lambda config: process.QWidget())

    class SelfStoppingAccount(_AccountConfig):
        def __init__(self):
            self.fragment_ready = threading.Event()
            self.stop_called = threading.Event()
            self.fragment = None

        def get_main_thread(self):
            assert self.fragment_ready.wait(timeout=3)
            self.fragment._stop_status_refresh()
            self.stop_called.set()
            return None

    account = SelfStoppingAccount()
    widget = process.ProcessFragment(None, account)
    account.fragment = widget
    account.fragment_ready.set()
    try:
        assert account.stop_called.wait(timeout=3)
        assert _wait_until(app, lambda: not widget._status_thread.is_alive())
    finally:
        widget.close()


def _item_rule(qss, selector):
    match = re.search(
        rf"#listWidget::item{re.escape(selector)}\s*\{{(?P<body>.*?)\}}",
        qss,
        re.DOTALL,
    )
    assert match is not None, f"missing queue item rule for {selector or 'normal'}"
    return {
        declaration.strip()
        for declaration in match.group("body").split(";")
        if declaration.strip()
    }


def test_light_and_dark_queue_item_states_have_identical_neutral_styling():
    light = open("gui/qss/light/process.qss", encoding="utf-8").read()
    dark = open("gui/qss/dark/process.qss", encoding="utf-8").read()
    expected = {
        "background-color: transparent",
        "color: inherit",
        "border: none",
        "outline: none",
    }

    for selector in ("", ":hover", ":selected", ":selected:active"):
        assert _item_rule(light, selector) == expected
        assert _item_rule(dark, selector) == expected
