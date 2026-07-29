"""Native Windows smoke coverage for the legacy scheduler graph workflow."""

from __future__ import annotations

import gc
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from PyQt5 import sip
from PyQt5.QtCore import (
    QCoreApplication,
    QEvent,
    QObject,
    QPoint,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QMainWindow
from qfluentwidgets import qconfig

from core.config.config_set import ConfigSet
from gui.components.expand import featureSwitch
from gui.components.scheduler_graph import SchedulerTaskNode
from gui.fragments import process
from gui.util.config_gui import ConfigGui


EVENT_TIME = int(datetime(2024, 2, 3, 4, 5, 6).timestamp())
UPDATED_TIME_TEXT = "2025-06-07 08:09:10"
UPDATED_TIME = int(datetime(2025, 6, 7, 8, 9, 10).timestamp())


class _WindowSignals(QObject):
    update_signal = pyqtSignal(list)
    notify_signal = pyqtSignal(str)


class _SmokeProcessFragment(process.ProcessFragment):
    def __init__(self, parent, config, teardown_timers):
        self._teardown_timers = teardown_timers
        super().__init__(parent, config)

    def closeEvent(self, event):
        teardown_timer = None
        if not self._teardown_timers:
            teardown_timer = QTimer()
            teardown_timer.setObjectName("smokeTeardownTimer")
            teardown_timer.setInterval(60_000)
            teardown_timer.start()
            self._teardown_timers.append(teardown_timer)
        try:
            super().closeEvent(event)
        finally:
            if teardown_timer is not None:
                teardown_timer.stop()


def _record(func_name: str, event_name: str, priority: int) -> dict:
    return {
        "func_name": func_name,
        "event_name": event_name,
        "priority": priority,
        "enabled": True,
        "next_tick": EVENT_TIME + priority,
        "interval": 0,
        "daily_reset": [],
        "disabled_time_range": [],
        "pre_task": [],
        "post_task": [],
    }


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _event(event_path: Path, func_name: str) -> dict:
    return next(
        record
        for record in _read_json(event_path)
        if record["func_name"] == func_name
    )


def _wait_until(app: QApplication, predicate, timeout_ms: int = 3000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        QTest.qWait(20)
    app.processEvents()
    return bool(predicate())


def _connected(output_port, input_port) -> bool:
    return input_port in output_port.connected_ports()


def _graph_widget(fragment, func_name: str, property_name: str):
    node = fragment.graph_view.node_for_func(func_name)
    assert node is not None
    return node.get_widget(property_name).get_custom_widget()


def _table_row(fragment, event_name: str) -> int:
    for row, label in enumerate(fragment.table_view.qLabels):
        if label.text() == event_name:
            return row
    raise AssertionError(f"table row not found: {event_name}")


def _assert_queue_is_neutral(fragment, app: QApplication) -> None:
    queue = fragment.listWidget
    assert queue.count() > 0
    assert queue.selectionMode() == QAbstractItemView.NoSelection
    assert queue.focusPolicy() == Qt.NoFocus
    assert queue.currentRow() == -1
    assert queue.selectedItems() == []

    item = queue.item(0)
    assert item.flags() == Qt.ItemIsEnabled
    rect = queue.visualItemRect(item)
    point = rect.center() if rect.isValid() else QPoint(5, 5)
    QTest.mouseMove(queue.viewport(), point)
    QTest.mouseClick(queue.viewport(), Qt.LeftButton, pos=point)
    app.processEvents()

    assert queue.currentRow() == -1
    assert queue.selectedItems() == []
    assert not queue.hasFocus()


def _close_and_delete(app: QApplication, widget) -> None:
    if widget is None or sip.isdeleted(widget):
        return
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def _live_qtimers():
    timers = []
    for candidate in gc.get_objects():
        try:
            if isinstance(candidate, QTimer) and not sip.isdeleted(candidate):
                timers.append(candidate)
        except RuntimeError:
            continue
    return timers


def run_smoke() -> None:
    if os.environ.get("QT_QPA_PLATFORM"):
        raise AssertionError(
            "QT_QPA_PLATFORM must be unset for the native Windows smoke"
        )

    app = QApplication.instance() or QApplication(["smoke_scheduler_graph"])
    assert QGuiApplication.platformName().lower() == "windows", (
        "native Windows Qt plugin required, got "
        f"{QGuiApplication.platformName()!r}"
    )

    original_qconfig = qconfig._cfg
    original_process_config = process.configGui
    original_feature_config = featureSwitch.configGui
    host = None
    fragment = None
    teardown_timers = []

    with tempfile.TemporaryDirectory(prefix="baas-scheduler-graph-smoke-") as tmp:
        temp_root = Path(tmp)
        account_dir = temp_root / "account"
        account_dir.mkdir()
        shutil.copy2(
            PROJECT_ROOT / "config" / "default_config" / "config.json",
            account_dir / "config.json",
        )
        events = [
            _record("a", "Smoke Task A", 1),
            _record("b", "Smoke Task B", 2),
            _record("c", "Smoke Task C", 3),
        ]
        event_path = account_dir / "event.json"
        event_path.write_text(
            json.dumps(events, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        gui_path = temp_root / "gui.json"
        gui_path.write_text("{}", encoding="utf-8")

        smoke_gui_config = ConfigGui()
        qconfig.load(gui_path, smoke_gui_config)
        process.configGui = smoke_gui_config
        featureSwitch.configGui = smoke_gui_config

        signals = _WindowSignals()
        account = ConfigSet(str(account_dir))
        account.add_signal("update_signal", signals.update_signal)
        account.add_signal("notify_signal", signals.notify_signal)
        baseline_threads = set(threading.enumerate())
        baseline_timers = _live_qtimers()

        try:
            host = QMainWindow()
            host.setObjectName("schedulerGraphSmokeHost")
            host.resize(1000, 760)
            account.set_window(host)
            fragment = _SmokeProcessFragment(
                host, account, teardown_timers
            )
            host.setCentralWidget(fragment)
            host.show()
            assert _wait_until(app, lambda: host.isVisible())
            assert fragment.isVisible()
            assert fragment._status_thread.is_alive()
            print("PASS scheduler page opened with native Windows Qt")

            assert _wait_until(app, lambda: fragment.listWidget.count() > 0)
            _assert_queue_is_neutral(fragment, app)
            print("PASS queue rows remain neutral after hover and click")

            fragment.scheduler_selector._onItemClicked(1)
            fragment.table_view.op_3._onItemClicked(1)
            app.processEvents()
            scheduler_preferences = _read_json(gui_path)["Scheduler"]
            assert scheduler_preferences == {
                "NewEventEnableState": "on",
                "SortMode": "next_tick",
            }
            print("PASS exact Scheduler gui.json preferences persisted")

            assert fragment.graph_view is None
            fragment.graph_view_button.click()
            app.processEvents()
            graph_view = fragment.graph_view
            assert graph_view is not None
            assert fragment.editor_stack.currentWidget() is graph_view
            nodes = graph_view.graph.all_nodes()
            assert len(nodes) == len(events) == 3
            assert {
                node.get_property("func_name") for node in nodes
            } == {"a", "b", "c"}
            assert graph_view.graph.create_node(
                SchedulerTaskNode.type_, name="not allowed"
            ) is None
            assert len(graph_view.graph.all_nodes()) == 3

            for func_name in ("a", "b", "c"):
                for role in (
                    "pre_input",
                    "pre_output",
                    "post_input",
                    "post_output",
                ):
                    assert graph_view.port_for(func_name, role) is not None
            print("PASS lazy fixed graph exposes both typed port families")

            enabled = _graph_widget(fragment, "a", "enabled")
            next_tick = _graph_widget(fragment, "a", "next_tick")
            enabled.click()
            next_tick.setFocus()
            next_tick.selectAll()
            QTest.keyClicks(next_tick, UPDATED_TIME_TEXT)
            next_tick.editingFinished.emit()
            app.processEvents()
            assert _event(event_path, "a")["enabled"] is False
            assert _event(event_path, "a")["next_tick"] == UPDATED_TIME
            print("PASS graph enabled and time widgets updated event.json")

            a_pre_output = graph_view.port_for("a", "pre_output")
            b_pre_input = graph_view.port_for("b", "pre_input")
            b_post_output = graph_view.port_for("b", "post_output")
            c_post_input = graph_view.port_for("c", "post_input")
            a_pre_output.connect_to(b_pre_input)
            b_post_output.connect_to(c_post_input)
            app.processEvents()
            assert _connected(a_pre_output, b_pre_input)
            assert _connected(b_post_output, c_post_input)
            assert _event(event_path, "b")["pre_task"] == ["a"]
            assert _event(event_path, "b")["post_task"] == ["c"]
            assert _event(event_path, "a")["post_task"] == []
            assert _event(event_path, "c")["pre_task"] == []
            print("PASS pre and post relationships persist independently")

            before_rejected_edges = event_path.read_bytes()
            a_post_output = graph_view.port_for("a", "post_output")
            a_post_input = graph_view.port_for("a", "post_input")
            a_post_output.connect_to(a_post_input)
            assert _wait_until(
                app, lambda: not _connected(a_post_output, a_post_input)
            )
            assert event_path.read_bytes() == before_rejected_edges

            c_post_output = graph_view.port_for("c", "post_output")
            a_post_input = graph_view.port_for("a", "post_input")
            c_post_output.connect_to(a_post_input)
            assert _wait_until(
                app, lambda: not _connected(c_post_output, a_post_input)
            )
            assert event_path.read_bytes() == before_rejected_edges
            assert graph_view.graph.undo_stack().count() == 0
            print("PASS self and cycle attempts roll back visually and on disk")

            graph_view.node_for_func("a").set_pos(135.5, -42.25)
            graph_view.node_for_func("b").set_pos(-88.0, 901.25)
            fragment.table_view_button.click()
            app.processEvents()
            assert fragment.editor_stack.currentWidget() is fragment.table_view
            row_a = _table_row(fragment, "Smoke Task A")
            assert fragment.table_view.check_boxes[row_a].isChecked() is False
            assert (
                fragment.table_view.times[row_a].text()
                == UPDATED_TIME_TEXT
            )
            table_b = next(
                record
                for record in fragment.table_view._event_config
                if record["func_name"] == "b"
            )
            assert table_b["pre_task"] == ["a"]
            assert table_b["post_task"] == ["c"]
            positions = _read_json(
                account_dir / "scheduler_graph.json"
            )["positions"]
            assert positions["a"] == [135.5, -42.25]
            assert positions["b"] == [-88.0, 901.25]
            print("PASS table sync and graph layout persistence")

            status_thread = fragment._status_thread
            created_timers = [
                timer
                for timer in _live_qtimers()
                if not any(
                    timer is baseline_timer
                    for baseline_timer in baseline_timers
                )
            ]
            for timer in host.findChildren(QTimer):
                if (
                    not any(
                        timer is baseline_timer
                        for baseline_timer in baseline_timers
                    )
                    and not any(
                        timer is created_timer
                        for created_timer in created_timers
                    )
                ):
                    created_timers.append(timer)
            assert teardown_timers == []
            fragment.close()
            assert len(teardown_timers) == 1
            assert _wait_until(app, lambda: not status_thread.is_alive())
            assert not status_thread.is_alive()
            _close_and_delete(app, host)
            host = None
            fragment = None
            for _ in range(3):
                QCoreApplication.sendPostedEvents(
                    None, QEvent.DeferredDelete
                )
                app.processEvents()
                gc.collect()

            post_teardown_timers = _live_qtimers()
            new_post_teardown_timers = [
                timer
                for timer in post_teardown_timers
                if not any(
                    timer is baseline_timer
                    for baseline_timer in baseline_timers
                )
            ]
            teardown_timer = teardown_timers[0]
            assert any(
                timer is teardown_timer
                for timer in new_post_teardown_timers
            )
            assert not teardown_timer.isActive()
            remaining_top_levels = [
                widget
                for widget in QApplication.topLevelWidgets()
                if not sip.isdeleted(widget)
            ]
            assert remaining_top_levels == [], [
                (
                    widget.__class__.__name__,
                    widget.objectName(),
                    widget.isVisible(),
                )
                for widget in remaining_top_levels
            ]
            unexpected_threads = [
                thread
                for thread in threading.enumerate()
                if thread not in baseline_threads
            ]
            assert unexpected_threads == [], [
                (thread.name, thread.ident, thread.daemon)
                for thread in unexpected_threads
            ]
            assert all(
                sip.isdeleted(timer) or not timer.isActive()
                for timer in created_timers
            )
            assert all(
                sip.isdeleted(timer) or not timer.isActive()
                for timer in new_post_teardown_timers
            )
            teardown_timer.deleteLater()
            QCoreApplication.sendPostedEvents(
                teardown_timer, QEvent.DeferredDelete
            )
            app.processEvents()
            assert sip.isdeleted(teardown_timer)
            print(
                "PASS fragment, Python threads, timers, and top-level "
                "widgets stopped"
            )
        finally:
            if fragment is not None and not sip.isdeleted(fragment):
                fragment.close()
            _close_and_delete(app, host)
            for timer in teardown_timers:
                if not sip.isdeleted(timer):
                    timer.stop()
                    timer.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            app.processEvents()
            process.configGui = original_process_config
            featureSwitch.configGui = original_feature_config
            qconfig._cfg = original_qconfig


if __name__ == "__main__":
    try:
        run_smoke()
    except Exception as error:
        print(f"SMOKE FAILED: {error}", file=sys.stderr)
        raise
    print("SMOKE PASSED")
