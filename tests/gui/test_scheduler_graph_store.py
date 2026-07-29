import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "gui" / "util"))

from scheduler_graph_store import (
    InvalidEventConfig,
    InvalidRelationship,
    InvalidTime,
    SchedulerGraphStore,
)


def _record(func_name, event_name, **overrides):
    record = {
        "func_name": func_name,
        "event_name": event_name,
        "enabled": True,
        "next_tick": 1_700_000_000,
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


@pytest.fixture
def config_dir(tmp_path):
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", unknown_record_key={"keep": "me"}),
            _record("b", "Task B"),
            _record("c", "Task C"),
            _record("d", "Task D"),
        ],
    )
    return tmp_path


def test_dependency_manifests_pin_nodegraphqt_exactly():
    root = Path(__file__).resolve().parents[2]
    assert "NodeGraphQt == 0.6.44" in (root / "requirements.txt").read_text(encoding="utf-8")
    assert '"NodeGraphQt == 0.6.44"' in (root / "pyproject.toml").read_text(encoding="utf-8")


def test_load_events_returns_immutable_values_without_json_containers(config_dir):
    events = SchedulerGraphStore(config_dir).load_events()

    assert events[0].func_name == "a"
    assert events[0].pre_task == ()
    assert events[0].post_task == ()
    with pytest.raises(AttributeError):
        events[0].pre_task.append("b")
    with pytest.raises(AttributeError):
        setattr(events[0], "enabled", False)


def test_load_events_rejects_records_missing_required_scheduler_fields(config_dir):
    _write_events(config_dir, [{"func_name": "a"}])

    with pytest.raises(InvalidEventConfig):
        SchedulerGraphStore(config_dir).load_events()


def test_add_pre_relationship_writes_only_target_pre_task(config_dir):
    store = SchedulerGraphStore(config_dir)

    store.add_relationship("pre", "b", "a")

    records = _read_events(config_dir)
    assert records[1]["pre_task"] == ["a"]
    assert records[0]["post_task"] == []


def test_add_post_relationship_writes_only_source_post_task(config_dir):
    store = SchedulerGraphStore(config_dir)

    store.add_relationship("post", "a", "b")

    records = _read_events(config_dir)
    assert records[0]["post_task"] == ["b"]
    assert records[1]["pre_task"] == []


def test_removal_changes_only_requested_relationship_type(config_dir):
    _write_events(
        config_dir,
        [
            _record("a", "Task A", post_task=["b"]),
            _record("b", "Task B", pre_task=["a"]),
            _record("c", "Task C"),
            _record("d", "Task D"),
        ],
    )
    store = SchedulerGraphStore(config_dir)

    store.remove_relationship("pre", "b", "a")

    records = _read_events(config_dir)
    assert records[1]["pre_task"] == []
    assert records[0]["post_task"] == ["b"]


@pytest.mark.parametrize(
    ("kind", "owner", "related", "error"),
    [
        ("pre", "a", "a", InvalidRelationship),
        ("pre", "missing", "a", InvalidRelationship),
        ("pre", "a", "missing", InvalidRelationship),
        ("unknown", "a", "b", InvalidRelationship),
    ],
)
def test_add_relationship_rejects_invalid_metadata(config_dir, kind, owner, related, error):
    with pytest.raises(error):
        SchedulerGraphStore(config_dir).add_relationship(kind, owner, related)


def test_add_relationship_rejects_same_type_duplicate(config_dir):
    _write_events(config_dir, [_record("a", "Task A"), _record("b", "Task B", pre_task=["a"])])

    with pytest.raises(InvalidRelationship):
        SchedulerGraphStore(config_dir).add_relationship("pre", "b", "a")


def test_add_relationship_rejects_a_new_edge_that_closes_combined_graph_cycle(config_dir):
    _write_events(
        config_dir,
        [
            _record("a", "Task A", post_task=["b"]),
            _record("b", "Task B", post_task=["c"]),
            _record("c", "Task C"),
        ],
    )

    with pytest.raises(InvalidRelationship):
        SchedulerGraphStore(config_dir).add_relationship("post", "c", "a")


def test_existing_cycles_warn_without_mutation_and_allow_unrelated_acyclic_edge(config_dir):
    _write_events(
        config_dir,
        [
            _record("a", "Task A", post_task=["b"]),
            _record("b", "Task B", post_task=["a"]),
            _record("c", "Task C"),
            _record("d", "Task D"),
        ],
    )
    before = (config_dir / "event.json").read_text(encoding="utf-8")
    store = SchedulerGraphStore(config_dir)

    relationships, warnings = store.load_relationships()

    assert [(item.source_func, item.target_func) for item in relationships] == [("a", "b"), ("b", "a")]
    assert any("cycle" in warning.lower() for warning in warnings)
    assert (config_dir / "event.json").read_text(encoding="utf-8") == before

    store.add_relationship("post", "c", "d")
    assert _read_events(config_dir)[2]["post_task"] == ["d"]


def test_unknown_dependencies_stay_in_json_but_are_not_drawable_and_warn(config_dir):
    _write_events(config_dir, [_record("a", "Task A", post_task=["unknown"]), _record("b", "Task B")])

    relationships, warnings = SchedulerGraphStore(config_dir).load_relationships()

    assert relationships == []
    assert any("unknown" in warning.lower() for warning in warnings)
    assert _read_events(config_dir)[0]["post_task"] == ["unknown"]


def test_update_next_tick_uses_strict_local_time_and_only_updates_requested_event(config_dir):
    store = SchedulerGraphStore(config_dir)

    store.update_next_tick("b", "2024-02-03 04:05:06")

    records = _read_events(config_dir)
    assert records[1]["next_tick"] == int(datetime(2024, 2, 3, 4, 5, 6).timestamp())
    assert records[0]["next_tick"] == 1_700_000_000


@pytest.mark.parametrize("time_text", ["2024-2-03 04:05:06", "2024-02-03 04:05", "2024-02-30 04:05:06"])
def test_update_next_tick_rejects_invalid_time_format_and_range(config_dir, time_text):
    with pytest.raises(InvalidTime):
        SchedulerGraphStore(config_dir).update_next_tick("a", time_text)


def test_update_enabled_only_changes_requested_event(config_dir):
    SchedulerGraphStore(config_dir).update_enabled("c", False)

    records = _read_events(config_dir)
    assert records[2]["enabled"] is False
    assert records[0]["enabled"] is True


@pytest.mark.parametrize(
    "update",
    [
        lambda store: store.update_enabled("a", False),
        lambda store: store.update_next_tick("a", "2024-02-03 04:05:06"),
        lambda store: store.add_relationship("post", "a", "b"),
        lambda store: store.remove_relationship("post", "a", "b"),
    ],
)
def test_every_update_preserves_unknown_keys_record_order_and_unrelated_records(config_dir, update):
    before = _read_events(config_dir)
    update(SchedulerGraphStore(config_dir))
    after = _read_events(config_dir)

    assert [record["func_name"] for record in after] == ["a", "b", "c", "d"]
    assert after[0]["unknown_record_key"] == {"keep": "me"}
    assert after[1] == before[1]
    assert after[2] == before[2]
    assert after[3] == before[3]


def test_layout_round_trip_preserves_floating_point_positions(config_dir):
    store = SchedulerGraphStore(config_dir)

    store.save_positions({"a": (120.0, 240.5), "missing": (-1.25, 0.0)})

    assert store.load_positions() == {"a": (120.0, 240.5), "missing": (-1.25, 0.0)}


def test_malformed_layout_falls_back_to_empty_positions(config_dir):
    (config_dir / "scheduler_graph.json").write_text('{"version": 1, "positions": []}', encoding="utf-8")

    assert SchedulerGraphStore(config_dir).load_positions() == {}


def test_atomic_write_failure_leaves_existing_file_intact_and_removes_temp_file(config_dir, monkeypatch):
    import scheduler_graph_store as graph_store_module

    before = (config_dir / "event.json").read_text(encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(graph_store_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        SchedulerGraphStore(config_dir).update_enabled("a", False)

    assert (config_dir / "event.json").read_text(encoding="utf-8") == before
    assert not list(config_dir.glob("*.tmp"))
