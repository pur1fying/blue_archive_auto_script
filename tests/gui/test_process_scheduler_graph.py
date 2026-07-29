import json
from datetime import datetime
from pathlib import Path

import pytest
from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QObject, pyqtSignal
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication, QWidget

import gui

PROJECT_ROOT = Path(__file__).resolve().parents[2]
gui.__path__.append(str(PROJECT_ROOT / "gui"))

from gui.components.expand import featureSwitch
from gui.fragments import process


INITIAL_TIMESTAMP = int(datetime(2024, 2, 3, 4, 5, 6).timestamp())


class _ConfigItem(QObject):
    valueChanged = pyqtSignal(object)


class _GuiConfig:
    def __init__(self):
        self.schedulerNewEventEnableState = _ConfigItem()
        self.schedulerSortMode = _ConfigItem()
        self._values = {
            self.schedulerNewEventEnableState: "default",
            self.schedulerSortMode: "priority",
        }

    def get(self, item):
        return self._values[item]

    def set(self, item, value):
        if self._values[item] == value:
            return
        self._values[item] = value
        item.valueChanged.emit(value)


class _AccountSignals(QObject):
    update_signal = pyqtSignal()
    notify_signal = pyqtSignal(str)


class _AccountConfig:
    def __init__(self, config_dir):
        self.config_dir = str(config_dir)
        self.signals = _AccountSignals()
        self.window = None

    def get_signal(self, key):
        return getattr(self.signals, key)

    def get_main_thread(self):
        return None

    def get_window(self):
        return self.window


def _record(func_name, event_name, priority, **overrides):
    record = {
        "func_name": func_name,
        "event_name": event_name,
        "priority": priority,
        "enabled": True,
        "next_tick": INITIAL_TIMESTAMP,
        "interval": 0,
        "daily_reset": [],
        "disabled_time_range": [],
        "pre_task": [],
        "post_task": [],
    }
    record.update(overrides)
    return record


def _write_events(config_dir, records=None):
    config_dir.mkdir(parents=True, exist_ok=True)
    records = records or [
        _record("a", "Task A", 1),
        _record("b", "Task B", 2),
    ]
    (config_dir / "event.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _read_events(config_dir):
    return json.loads(
        (config_dir / "event.json").read_text(encoding="utf-8")
    )


def _event(config_dir, func_name):
    return next(
        record
        for record in _read_events(config_dir)
        if record["func_name"] == func_name
    )


def _table_row(table, event_name):
    return next(
        index
        for index, label in enumerate(table.qLabels)
        if label.text() == event_name
    )


def _graph_widget(fragment, func_name, property_name):
    return (
        fragment.graph_view.node_for_func(func_name)
        .get_widget(property_name)
        .get_custom_widget()
    )


def _click_graph(fragment, app):
    fragment.graph_view_button.click()
    app.processEvents()


def _click_table(fragment, app):
    fragment.table_view_button.click()
    app.processEvents()


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def integration(app, tmp_path, monkeypatch):
    gui_config = _GuiConfig()
    monkeypatch.setattr(process, "configGui", gui_config)
    monkeypatch.setattr(featureSwitch, "configGui", gui_config)

    started_threads = []
    monkeypatch.setattr(
        process.threading.Thread,
        "start",
        lambda thread: started_threads.append(thread),
    )

    fragments = []

    def build(name="account", records=None, parent=None):
        config_dir = tmp_path / name
        _write_events(config_dir, records)
        account = _AccountConfig(config_dir)
        fragment = process.ProcessFragment(parent, account)
        account.window = fragment
        fragment.resize(900, 700)
        fragment.show()
        app.processEvents()
        fragments.append(fragment)
        return fragment, account, config_dir

    yield build, gui_config, started_threads

    for fragment in fragments:
        if sip.isdeleted(fragment):
            continue
        fragment.close()
        fragment.deleteLater()
    app.processEvents()


def test_default_page_keeps_status_and_queue_outside_table_editor_stack(
    integration,
):
    build, _gui_config, started_threads = integration
    fragment, _account, _config_dir = build()

    assert fragment.editor_stack.currentIndex() == 0
    assert fragment.editor_stack.count() == 1
    assert fragment.editor_stack.widget(0) is fragment.table_view
    assert fragment.graph_view is None
    assert not fragment.editor_stack.isAncestorOf(fragment.on_status)
    assert not fragment.editor_stack.isAncestorOf(fragment.listWidget)
    assert (
        fragment.VBoxWrapperLayout.indexOf(fragment.displayWidget)
        < fragment.VBoxWrapperLayout.indexOf(fragment.editor_stack)
    )
    assert fragment.scheduler_controls_layout.indexOf(
        fragment.scheduler_selector
    ) >= 0
    assert fragment.scheduler_controls_layout.indexOf(
        fragment.view_selector
    ) >= 0
    assert len(started_threads) == 1


def test_title_toggle_switches_only_the_lower_editor_and_reuses_fragment(
    integration, app
):
    build, _gui_config, started_threads = integration
    fragment, _account, _config_dir = build()
    fragment_identity = id(fragment)
    table_identity = id(fragment.table_view)
    status_thread = started_threads[0]

    _click_graph(fragment, app)

    assert id(fragment) == fragment_identity
    assert id(fragment.table_view) == table_identity
    assert fragment.editor_stack.currentIndex() == 1
    assert fragment.editor_stack.widget(1) is fragment.graph_view

    _click_table(fragment, app)

    assert fragment.editor_stack.currentIndex() == 0
    assert fragment.editor_stack.widget(0) is fragment.table_view
    assert started_threads == [status_thread]


def test_table_reload_from_disk_is_idempotent_and_reapplies_persisted_sort(
    integration,
):
    build, gui_config, _started_threads = integration
    gui_config.set(gui_config.schedulerSortMode, "next_tick")
    records = [
        _record("priority_first", "Priority First", 1, next_tick=300),
        _record("tick_first", "Tick First", 2, next_tick=100),
    ]
    fragment, account, config_dir = build(records=records)
    table = fragment.table_view
    receiver_count = account.signals.receivers(account.signals.update_signal)
    sort_receiver_count = gui_config.schedulerSortMode.receivers(
        gui_config.schedulerSortMode.valueChanged
    )
    assert [label.text() for label in table.qLabels] == [
        "Tick First",
        "Priority First",
    ]

    records[0]["next_tick"] = 50
    _write_events(config_dir, records)
    table.reload_from_disk()
    table.reload_from_disk()
    table.reload_from_disk()

    assert account.signals.receivers(
        account.signals.update_signal
    ) == receiver_count == 1
    assert gui_config.schedulerSortMode.receivers(
        gui_config.schedulerSortMode.valueChanged
    ) == sort_receiver_count == 1
    assert table.op_3.currentIndex() == 1
    assert [label.text() for label in table.qLabels] == [
        "Priority First",
        "Tick First",
    ]

    save_calls = []
    original_save = table._save_config

    def record_save():
        save_calls.append(True)
        original_save()

    table._save_config = record_save
    table.times[0].setText("2028-09-10 11:12:13")

    assert save_calls == [True]


def test_toggles_synchronize_real_time_edits_in_both_directions_and_save_layout(
    integration, app
):
    build, _gui_config, _started_threads = integration
    fragment, _account, config_dir = build()
    table = fragment.table_view

    _click_graph(fragment, app)
    node = fragment.graph_view.node_for_func("a")
    node.set_pos(135.5, -42.25)
    graph_time = _graph_widget(fragment, "a", "next_tick")
    graph_time.setText("2025-06-07 08:09:10")
    graph_time.editingFinished.emit()

    _click_table(fragment, app)

    row = _table_row(table, "Task A")
    assert table.times[row].text() == "2025-06-07 08:09:10"
    positions = json.loads(
        (config_dir / "scheduler_graph.json").read_text(encoding="utf-8")
    )["positions"]
    assert positions["a"] == [135.5, -42.25]

    table.times[row].setText("2026-07-08 09:10:11")
    table_tick = _event(config_dir, "a")["next_tick"]
    assert table_tick == int(
        datetime(2026, 7, 8, 9, 10, 11).timestamp()
    )
    assert isinstance(table_tick, int)
    previous_graph = fragment.graph_view.graph
    assert fragment.editor_stack.currentWidget() is table
    _click_graph(fragment, app)

    assert fragment.editor_stack.currentIndex() == 1
    assert fragment.graph_view.graph is not previous_graph
    assert _graph_widget(
        fragment, "a", "next_tick"
    ).text() == "2026-07-08 09:10:11"
    assert _event(config_dir, "a")["next_tick"] == int(
        datetime(2026, 7, 8, 9, 10, 11).timestamp()
    )


def test_graph_enabled_and_relationship_changes_reload_only_visible_table(
    integration, app
):
    build, _gui_config, started_threads = integration
    fragment, _account, config_dir = build()
    table = fragment.table_view
    status_thread = started_threads[0]

    _click_graph(fragment, app)
    graph_checkbox = _graph_widget(fragment, "a", "enabled")
    graph_checkbox.click()
    output_port = fragment.graph_view.port_for("a", "pre_output")
    input_port = fragment.graph_view.port_for("b", "pre_input")
    output_port.connect_to(input_port)

    stale_row = _table_row(table, "Task A")
    assert table.check_boxes[stale_row].isChecked() is True
    assert fragment._table_stale is True

    _click_table(fragment, app)

    row = _table_row(table, "Task A")
    assert table.check_boxes[row].isChecked() is False
    assert _event(config_dir, "b")["pre_task"] == ["a"]
    assert fragment._table_stale is False

    _click_graph(fragment, app)

    reloaded_output = fragment.graph_view.port_for("a", "pre_output")
    reloaded_input = fragment.graph_view.port_for("b", "pre_input")
    assert reloaded_input in reloaded_output.connected_ports()
    assert _graph_widget(
        fragment, "a", "enabled"
    ).isChecked() is False
    assert started_threads == [status_thread]


def test_existing_table_detail_editor_uses_configured_window_inside_stack(
    integration, monkeypatch
):
    build, _gui_config, _started_threads = integration
    fragment, account, _config_dir = build()
    row = _table_row(fragment.table_view, "Task A")
    dialog_parents = []

    class _DismissedDetailDialog:
        def __init__(self, *args, parent=None, **kwargs):
            dialog_parents.append(parent)

        def exec_(self):
            return False

    monkeypatch.setattr(
        featureSwitch,
        "DetailSettingMessageBox",
        _DismissedDetailDialog,
    )
    fragment.table_view._update_detail(row)

    assert dialog_parents == [account.get_window()]


@pytest.mark.parametrize("lifecycle", ["hide", "close"])
def test_fragment_lifecycle_saves_positions_without_touching_event_json(
    integration, app, lifecycle
):
    build, _gui_config, _started_threads = integration
    fragment, _account, config_dir = build()
    _click_graph(fragment, app)
    fragment.graph_view.node_for_func("a").set_pos(11.0, 22.0)
    before = (config_dir / "event.json").read_bytes()

    getattr(fragment, lifecycle)()
    app.processEvents()

    positions = json.loads(
        (config_dir / "scheduler_graph.json").read_text(encoding="utf-8")
    )["positions"]
    assert positions["a"] == [11.0, 22.0]
    assert (config_dir / "event.json").read_bytes() == before


def test_direct_deferred_delete_saves_latest_layout_without_touching_events(
    integration, app
):
    build, _gui_config, _started_threads = integration
    host = QWidget()
    host.resize(900, 700)
    host.show()
    fragment, _account, config_dir = build(parent=host)
    _click_graph(fragment, app)
    fragment.graph_view.node_for_func("a").set_pos(777.5, -333.25)
    event_bytes = (config_dir / "event.json").read_bytes()
    event_records = _read_events(config_dir)

    fragment.deleteLater()
    QCoreApplication.sendPostedEvents(fragment, QEvent.DeferredDelete)
    app.processEvents()

    assert sip.isdeleted(fragment)
    positions = json.loads(
        (config_dir / "scheduler_graph.json").read_text(encoding="utf-8")
    )["positions"]
    assert positions["a"] == [777.5, -333.25]
    assert (config_dir / "event.json").read_bytes() == event_bytes
    assert _read_events(config_dir) == event_records
    host.close()
    host.deleteLater()


def test_missing_nodegraphqt_reports_translated_error_and_table_stays_editable(
    integration, app, monkeypatch
):
    build, _gui_config, _started_threads = integration
    fragment, account, config_dir = build()
    notices = QSignalSpy(account.signals.notify_signal)

    def unavailable(_module_name):
        raise ModuleNotFoundError(
            "No module named 'NodeGraphQt'", name="NodeGraphQt"
        )

    monkeypatch.setattr(process, "import_module", unavailable, raising=False)

    _click_graph(fragment, app)

    assert fragment.editor_stack.currentIndex() == 0
    assert fragment.editor_stack.count() == 1
    assert fragment.graph_view is None
    assert fragment.table_view_button.isSelected is True
    assert fragment.graph_view_button.isSelected is False
    assert len(notices) == 1
    payload = json.loads(notices[0][0])
    assert payload["msg"] == fragment.tr(
        "图形视图需要安装 NodeGraphQt"
    )

    row = _table_row(fragment.table_view, "Task A")
    fragment.table_view.times[row].setText("2027-08-09 10:11:12")

    assert _event(config_dir, "a")["next_tick"] == int(
        datetime(2027, 8, 9, 10, 11, 12).timestamp()
    )
