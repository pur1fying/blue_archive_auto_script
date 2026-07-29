import inspect
import json
from datetime import datetime
from pathlib import Path

import NodeGraphQt
import pytest
from NodeGraphQt import BaseNode, NodeGraph, Port
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QSignalSpy, QTest
from PyQt5.QtWidgets import QApplication, QLabel

import gui

PROJECT_ROOT = Path(__file__).resolve().parents[2]
gui.__path__.append(str(PROJECT_ROOT / "gui"))

from gui.components import scheduler_graph as graph_module
from gui.components.scheduler_graph import (
    FixedNodeGraph,
    SchedulerGraphView,
    SchedulerTaskNode,
)
from gui.util.scheduler_graph_store import (
    InvalidRelationship,
    SchedulerGraphStore,
)


DISPLAY_TIME = "2024-02-03 04:05:06"
DISPLAY_TIMESTAMP = int(datetime(2024, 2, 3, 4, 5, 6).timestamp())

def _record(func_name, event_name, **overrides):
    record = {
        "func_name": func_name,
        "event_name": event_name,
        "enabled": True,
        "next_tick": DISPLAY_TIMESTAMP,
        "pre_task": [],
        "post_task": [],
    }
    record.update(overrides)
    return record


def _write_events(config_dir, records):
    (config_dir / "event.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _read_events(config_dir):
    return json.loads((config_dir / "event.json").read_text(encoding="utf-8"))


class RecordingStore(SchedulerGraphStore):
    def __init__(self, config_dir):
        super().__init__(config_dir)
        self.mutation_calls = []

    def add_relationship(self, kind, owner_func, related_func):
        self.mutation_calls.append(
            ("add_relationship", kind, owner_func, related_func)
        )
        return super().add_relationship(kind, owner_func, related_func)

    def remove_relationship(self, kind, owner_func, related_func):
        self.mutation_calls.append(
            ("remove_relationship", kind, owner_func, related_func)
        )
        return super().remove_relationship(kind, owner_func, related_func)

    def update_enabled(self, func_name, enabled):
        self.mutation_calls.append(("update_enabled", func_name, enabled))
        return super().update_enabled(func_name, enabled)

    def update_next_tick(self, func_name, time_text):
        self.mutation_calls.append(("update_next_tick", func_name, time_text))
        return super().update_next_tick(func_name, time_text)


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="session")
def nodegraphqt_0644_api():
    """Exact installed signatures; both port signals emit input then output."""
    return {
        "NodeGraph.delete_nodes": "(self, nodes, push_undo=True)",
        "NodeGraph.auto_layout_nodes": (
            "(self, nodes=None, down_stream=True, start_nodes=None)"
        ),
        "BaseNode.add_checkbox": (
            "(self, name, label='', text='', state=False, tooltip=None, tab=None)"
        ),
        "BaseNode.add_text_input": (
            "(self, name, label='', text='', placeholder_text='', "
            "tooltip=None, tab=None)"
        ),
        "BaseNode.set_pos": "(self, x, y)",
        "BaseNode.pos": "(self)",
        "Port.connect_to": (
            "(self, port=None, push_undo=True, emit_signal=True)"
        ),
        "Port.disconnect_from": (
            "(self, port=None, push_undo=True, emit_signal=True)"
        ),
        "port_connected": {
            "qt_signature": (
                "2port_connected(PyQt_PyObject,PyQt_PyObject)"
            ),
            "arguments": ("input_port", "output_port"),
        },
        "port_disconnected": {
            "qt_signature": (
                "2port_disconnected(PyQt_PyObject,PyQt_PyObject)"
            ),
            "arguments": ("input_port", "output_port"),
        },
    }


@pytest.fixture
def managed_views(app):
    views = []
    yield views
    for view in views:
        view.close()
        view.deleteLater()
    app.processEvents()


@pytest.fixture
def config_dir(tmp_path):
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", enabled=True),
            _record("b", "Task B", enabled=False),
            _record("c", "Task C", enabled=True),
        ],
    )
    return tmp_path


def _build_view(config_dir, managed_views):
    stores = []

    def store_factory(path):
        store = RecordingStore(path)
        stores.append(store)
        return store

    view = SchedulerGraphView(config_dir, store_factory=store_factory)
    managed_views.append(view)
    return view, stores[0]


def _widget(node, property_name):
    return node.get_widget(property_name).get_custom_widget()


def _message(view):
    return view.findChild(QLabel, "schedulerGraphMessage")


def _ports(view, kind, source_func="a", target_func="b"):
    return (
        view.port_for(source_func, f"{kind}_output"),
        view.port_for(target_func, f"{kind}_input"),
    )


def _connect(view, kind, source_func="a", target_func="b"):
    output_port, input_port = _ports(view, kind, source_func, target_func)
    output_port.connect_to(input_port)
    return output_port, input_port


def _disconnect(view, kind, source_func="a", target_func="b"):
    output_port, input_port = _ports(view, kind, source_func, target_func)
    output_port.disconnect_from(input_port)
    return output_port, input_port


def _is_connected(output_port, input_port):
    return input_port in output_port.connected_ports()


def test_nodegraphqt_characterization_matches_pinned_0644(
    app, nodegraphqt_0644_api
):
    graph = NodeGraph()
    assert NodeGraphQt.__version__ == "0.6.44"
    assert str(inspect.signature(NodeGraph.delete_nodes)) == (
        nodegraphqt_0644_api["NodeGraph.delete_nodes"]
    )
    assert str(inspect.signature(NodeGraph.auto_layout_nodes)) == (
        nodegraphqt_0644_api["NodeGraph.auto_layout_nodes"]
    )
    assert str(inspect.signature(BaseNode.add_checkbox)) == (
        nodegraphqt_0644_api["BaseNode.add_checkbox"]
    )
    assert str(inspect.signature(BaseNode.add_text_input)) == (
        nodegraphqt_0644_api["BaseNode.add_text_input"]
    )
    assert str(inspect.signature(BaseNode.set_pos)) == nodegraphqt_0644_api[
        "BaseNode.set_pos"
    ]
    assert str(inspect.signature(BaseNode.pos)) == nodegraphqt_0644_api[
        "BaseNode.pos"
    ]
    assert str(inspect.signature(Port.connect_to)) == nodegraphqt_0644_api[
        "Port.connect_to"
    ]
    assert str(inspect.signature(Port.disconnect_from)) == (
        nodegraphqt_0644_api["Port.disconnect_from"]
    )
    assert graph.port_connected.signal == (
        nodegraphqt_0644_api["port_connected"]["qt_signature"]
    )
    assert graph.port_disconnected.signal == (
        nodegraphqt_0644_api["port_disconnected"]["qt_signature"]
    )


def test_construction_maps_fixed_tasks_widgets_and_typed_ports(
    config_dir, managed_views, monkeypatch
):
    monkeypatch.setattr(
        graph_module.bt,
        "tr",
        lambda context, text: f"translated:{text}",
    )

    view, store = _build_view(config_dir, managed_views)

    assert isinstance(view.graph, FixedNodeGraph)
    assert len(view.graph.all_nodes()) == 3
    node_a = view.node_for_func("a")
    node_b = view.node_for_func("b")
    assert isinstance(node_a, SchedulerTaskNode)
    assert node_a.func_name == "a"
    assert node_a.name() == "translated:Task A"
    assert _widget(node_a, "enabled").isChecked() is True
    assert _widget(node_b, "enabled").isChecked() is False
    assert _widget(node_a, "next_tick").text() == DISPLAY_TIME
    assert list(node_a.inputs()) == ["前置任务", "作为后置任务"]
    assert list(node_a.outputs()) == ["作为前置任务", "后置任务"]

    pre_input = view.port_for("a", "pre_input")
    pre_output = view.port_for("a", "pre_output")
    post_input = view.port_for("a", "post_input")
    post_output = view.port_for("a", "post_output")
    assert pre_input.name() == "前置任务"
    assert pre_output.name() == "作为前置任务"
    assert post_input.name() == "作为后置任务"
    assert post_output.name() == "后置任务"
    assert tuple(pre_input.color[:3]) == tuple(pre_output.color[:3])
    assert tuple(post_input.color[:3]) == tuple(post_output.color[:3])
    assert tuple(pre_input.color[:3]) != tuple(post_input.color[:3])
    assert store.mutation_calls == []


def test_node_creation_ui_and_context_menus_are_disabled(
    app, config_dir, managed_views
):
    view, _store = _build_view(config_dir, managed_views)
    view.show()
    app.processEvents()

    assert all(
        not menu.isEnabled() and not menu.isVisible()
        for menu in view.graph.viewer().context_menus().values()
    )
    assert view.graph.viewer().acceptDrops() is False
    view.graph.toggle_node_search()
    app.processEvents()
    assert view.graph.viewer()._search_widget.isHidden()


def test_cross_role_ports_reject_visual_connection_without_store_mutation(
    config_dir, managed_views
):
    view, store = _build_view(config_dir, managed_views)
    pre_output = view.port_for("a", "pre_output")
    post_input = view.port_for("b", "post_input")

    pre_output.connect_to(post_input)

    assert not _is_connected(pre_output, post_input)
    assert store.mutation_calls == []


@pytest.mark.parametrize("key", [Qt.Key_Delete, Qt.Key_Backspace])
def test_delete_shortcuts_and_delete_nodes_cannot_remove_tasks(
    app, config_dir, managed_views, key
):
    view, _store = _build_view(config_dir, managed_views)
    node = view.node_for_func("a")
    node.set_selected(True)

    QTest.keyClick(view.graph.viewer(), key)
    view.graph.delete_nodes([node], push_undo=False)
    app.processEvents()

    assert len(view.graph.all_nodes()) == 3
    assert view.node_for_func("a") is node


@pytest.mark.parametrize(
    ("kind", "expected_call"),
    [
        ("pre", ("add_relationship", "pre", "b", "a")),
        ("post", ("add_relationship", "post", "a", "b")),
    ],
)
def test_connect_uses_exact_store_mapping_and_emits_data_changed(
    config_dir, managed_views, kind, expected_call
):
    view, store = _build_view(config_dir, managed_views)
    changed = QSignalSpy(view.data_changed)

    output_port, input_port = _connect(view, kind)

    assert _is_connected(output_port, input_port)
    assert store.mutation_calls == [expected_call]
    assert len(changed) == 1


@pytest.mark.parametrize(
    ("kind", "records", "expected_call"),
    [
        (
            "pre",
            [_record("a", "Task A"), _record("b", "Task B", pre_task=["a"])],
            ("remove_relationship", "pre", "b", "a"),
        ),
        (
            "post",
            [_record("a", "Task A", post_task=["b"]), _record("b", "Task B")],
            ("remove_relationship", "post", "a", "b"),
        ),
    ],
)
def test_disconnect_uses_exact_store_mapping_and_emits_data_changed(
    tmp_path, managed_views, kind, records, expected_call
):
    _write_events(tmp_path, records)
    view, store = _build_view(tmp_path, managed_views)
    changed = QSignalSpy(view.data_changed)

    output_port, input_port = _disconnect(view, kind)

    assert not _is_connected(output_port, input_port)
    assert store.mutation_calls == [expected_call]
    assert len(changed) == 1


@pytest.mark.parametrize(
    "failure",
    [
        InvalidRelationship("rejected relationship"),
        OSError("simulated add write failure"),
    ],
)
def test_failed_connect_rolls_back_only_new_relationship_and_reports_error(
    app, tmp_path, managed_views, monkeypatch, failure
):
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", post_task=["b"]),
            _record("b", "Task B"),
        ],
    )
    view, store = _build_view(tmp_path, managed_views)
    post_output, post_input = _ports(view, "post")
    assert _is_connected(post_output, post_input)
    errors = QSignalSpy(view.error_occurred)
    changed = QSignalSpy(view.data_changed)

    def fail_add(*_args):
        raise failure

    monkeypatch.setattr(store, "add_relationship", fail_add)
    pre_output, pre_input = _connect(view, "pre")
    app.processEvents()

    assert not _is_connected(pre_output, pre_input)
    assert _is_connected(post_output, post_input)
    assert view.graph.undo_stack().count() == 0
    assert len(errors) == 1
    assert str(failure) in _message(view).text()
    assert len(changed) == 0


@pytest.mark.parametrize(
    "failure",
    [
        InvalidRelationship("rejected removal"),
        OSError("simulated remove write failure"),
    ],
)
def test_failed_disconnect_restores_only_removed_relationship_and_reports_error(
    app, tmp_path, managed_views, monkeypatch, failure
):
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", post_task=["b"]),
            _record("b", "Task B", pre_task=["a"]),
        ],
    )
    view, store = _build_view(tmp_path, managed_views)
    pre_output, pre_input = _ports(view, "pre")
    post_output, post_input = _ports(view, "post")
    assert _is_connected(pre_output, pre_input)
    assert _is_connected(post_output, post_input)
    errors = QSignalSpy(view.error_occurred)
    changed = QSignalSpy(view.data_changed)

    def fail_remove(*_args):
        raise failure

    monkeypatch.setattr(store, "remove_relationship", fail_remove)
    _disconnect(view, "pre")
    app.processEvents()

    assert _is_connected(pre_output, pre_input)
    assert _is_connected(post_output, post_input)
    assert view.graph.undo_stack().count() == 0
    assert len(errors) == 1
    assert str(failure) in _message(view).text()
    assert len(changed) == 0


def test_checkbox_and_time_commit_only_on_deliberate_boundaries(
    config_dir, managed_views
):
    view, store = _build_view(config_dir, managed_views)
    node = view.node_for_func("a")
    checkbox = _widget(node, "enabled")
    line_edit = _widget(node, "next_tick")
    changed = QSignalSpy(view.data_changed)
    assert store.mutation_calls == []

    line_edit.setText("2025-06-07 08:09:10")
    assert store.mutation_calls == []

    checkbox.click()
    line_edit.editingFinished.emit()

    assert store.mutation_calls == [
        ("update_enabled", "a", False),
        ("update_next_tick", "a", "2025-06-07 08:09:10"),
    ]
    assert len(changed) == 2
    records = _read_events(config_dir)
    assert records[0]["enabled"] is False
    assert records[0]["next_tick"] == int(
        datetime(2025, 6, 7, 8, 9, 10).timestamp()
    )


def test_invalid_time_restores_last_persisted_text_without_data_change(
    app, config_dir, managed_views
):
    view, _store = _build_view(config_dir, managed_views)
    line_edit = _widget(view.node_for_func("a"), "next_tick")
    errors = QSignalSpy(view.error_occurred)
    changed = QSignalSpy(view.data_changed)

    line_edit.setText("not a scheduler time")
    line_edit.editingFinished.emit()
    app.processEvents()

    assert line_edit.text() == DISPLAY_TIME
    assert view.graph.undo_stack().count() == 0
    assert len(errors) == 1
    assert len(changed) == 0
    assert _read_events(config_dir)[0]["next_tick"] == DISPLAY_TIMESTAMP


def test_failed_enabled_write_restores_previous_checkbox_state(
    app, config_dir, managed_views, monkeypatch
):
    view, store = _build_view(config_dir, managed_views)
    node = view.node_for_func("a")
    checkbox = _widget(node, "enabled")
    errors = QSignalSpy(view.error_occurred)
    changed = QSignalSpy(view.data_changed)

    def fail_update(*_args):
        raise OSError("simulated enabled write failure")

    monkeypatch.setattr(store, "update_enabled", fail_update)
    checkbox.click()
    app.processEvents()

    assert checkbox.isChecked() is True
    assert node.get_property("enabled") is True
    assert view.graph.undo_stack().count() == 0
    assert len(errors) == 1
    assert len(changed) == 0
    assert _read_events(config_dir)[0]["enabled"] is True


def test_failed_time_write_restores_previous_text(
    app, config_dir, managed_views, monkeypatch
):
    view, store = _build_view(config_dir, managed_views)
    node = view.node_for_func("a")
    line_edit = _widget(node, "next_tick")
    errors = QSignalSpy(view.error_occurred)
    changed = QSignalSpy(view.data_changed)

    def fail_update(*_args):
        raise OSError("simulated time write failure")

    monkeypatch.setattr(store, "update_next_tick", fail_update)
    line_edit.setText("2025-06-07 08:09:10")
    line_edit.editingFinished.emit()
    app.processEvents()

    assert line_edit.text() == DISPLAY_TIME
    assert node.get_property("next_tick") == DISPLAY_TIME
    assert view.graph.undo_stack().count() == 0
    assert len(errors) == 1
    assert len(changed) == 0
    assert _read_events(config_dir)[0]["next_tick"] == DISPLAY_TIMESTAMP


def test_existing_cycle_and_unknown_dependency_warn_without_mutating_events(
    tmp_path, managed_views
):
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", post_task=["b", "unknown"]),
            _record("b", "Task B", post_task=["a"]),
        ],
    )
    before = (tmp_path / "event.json").read_bytes()

    view, store = _build_view(tmp_path, managed_views)

    message = _message(view).text().lower()
    assert "cycle" in message
    assert "unknown" in message
    assert not _message(view).isHidden()
    assert store.mutation_calls == []
    assert (tmp_path / "event.json").read_bytes() == before


def test_saved_positions_load_and_round_trip_across_fresh_graph_instances(
    config_dir, managed_views
):
    SchedulerGraphStore(config_dir).save_positions(
        {"a": (10.5, 20.25), "b": (300.0, -40.0), "c": (-25.0, 75.0)}
    )
    view, store = _build_view(config_dir, managed_views)
    assert view.node_for_func("a").pos() == [10.5, 20.25]
    old_graph = view.graph

    view.node_for_func("a").set_pos(123.5, 456.25)
    view.reload_from_disk()

    assert view.graph is not old_graph
    assert view.node_for_func("a").pos() == [123.5, 456.25]
    assert store.load_positions()["a"] == (123.5, 456.25)


def test_hide_event_saves_current_node_coordinates(
    app, config_dir, managed_views
):
    view, store = _build_view(config_dir, managed_views)
    view.show()
    app.processEvents()
    view.node_for_func("b").set_pos(-88.5, 901.25)

    view.hide()
    app.processEvents()

    assert store.load_positions()["b"] == (-88.5, 901.25)


@pytest.mark.parametrize(
    "layout_payload",
    [
        None,
        "{not json",
        json.dumps({"version": 1, "positions": {}}),
        json.dumps({"version": 1, "positions": {"a": [1.0, 2.0]}}),
    ],
)
def test_missing_malformed_empty_or_incomplete_layout_auto_arranges_nodes(
    tmp_path, managed_views, layout_payload
):
    _write_events(
        tmp_path,
        [
            _record("a", "Task A"),
            _record("b", "Task B"),
            _record("c", "Task C"),
        ],
    )
    if layout_payload is not None:
        (tmp_path / "scheduler_graph.json").write_text(
            layout_payload, encoding="utf-8"
        )

    view, _store = _build_view(tmp_path, managed_views)

    positions = {tuple(node.pos()) for node in view.graph.all_nodes()}
    assert len(positions) == 3


def test_failed_layout_write_reports_error_and_leaves_graph_editable(
    config_dir, managed_views, monkeypatch
):
    view, store = _build_view(config_dir, managed_views)
    errors = QSignalSpy(view.error_occurred)

    def fail_save(*_args):
        raise OSError("simulated layout write failure")

    monkeypatch.setattr(store, "save_positions", fail_save)
    view.node_for_func("a").set_pos(44.0, 55.0)
    view.save_layout()
    output_port, input_port = _connect(view, "post")

    assert len(view.graph.all_nodes()) == 3
    assert view.node_for_func("a").pos() == [44.0, 55.0]
    assert _is_connected(output_port, input_port)
    assert len(errors) == 1
    assert "simulated layout write failure" in _message(view).text()


def test_failed_layout_write_before_reload_stays_visible_on_fresh_graph(
    config_dir, managed_views, monkeypatch
):
    view, store = _build_view(config_dir, managed_views)
    old_graph = view.graph
    errors = QSignalSpy(view.error_occurred)

    def fail_save(*_args):
        raise OSError("simulated reload layout failure")

    monkeypatch.setattr(store, "save_positions", fail_save)
    view.reload_from_disk()

    assert view.graph is not old_graph
    assert len(view.graph.all_nodes()) == 3
    assert len(errors) == 1
    assert "simulated reload layout failure" in _message(view).text()
