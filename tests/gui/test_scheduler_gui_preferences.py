import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import qconfig

import gui

PROJECT_ROOT = Path(__file__).resolve().parents[2]
gui.__path__.append(str(PROJECT_ROOT / "gui"))

from gui.components.expand import featureSwitch
from gui.fragments import process
from gui.util import config_gui as config_gui_module
from gui.util.config_gui import ConfigGui
import window


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def gui_config(tmp_path, monkeypatch):
    config_path = tmp_path / "gui.json"
    original_config = qconfig._cfg
    original_sort_mode = ConfigGui.schedulerSortMode.value

    def load(payload=None):
        if payload is not None:
            config_path.write_text(json.dumps(payload), encoding="utf-8")
        ConfigGui.schedulerSortMode.value = (
            ConfigGui.schedulerSortMode.defaultValue
        )
        config = ConfigGui()
        load_gui_config = getattr(
            config_gui_module, "load_gui_config", qconfig.load
        )
        load_gui_config(config_path, config)
        monkeypatch.setattr(process, "configGui", config, raising=False)
        monkeypatch.setattr(featureSwitch, "configGui", config, raising=False)
        monkeypatch.setattr(window, "configGui", config, raising=False)
        return config

    yield load, config_path

    qconfig._cfg = original_config
    ConfigGui.schedulerSortMode.value = original_sort_mode


def test_loading_gui_config_removes_deprecated_scheduler_state(gui_config):
    load, config_path = gui_config

    load({
        "Scheduler": {
            "NewEventEnableState": "off",
            "SortMode": "next_tick",
        }
    })

    assert json.loads(config_path.read_text(encoding="utf-8"))[
        "Scheduler"
    ] == {"SortMode": "next_tick"}


def test_scheduler_sort_mode_round_trips_without_gui_scheduler_state(
        gui_config):
    load, config_path = gui_config
    config = load({
        "Scheduler": {
            "NewEventEnableState": "off",
            "SortMode": "priority",
        }
    })

    config.set(config.schedulerSortMode, "next_tick")
    persisted = json.loads(config_path.read_text(encoding="utf-8"))
    assert persisted["Scheduler"] == {"SortMode": "next_tick"}

    reconstructed = load()
    assert reconstructed.get(reconstructed.schedulerSortMode) == "next_tick"


def test_invalid_scheduler_sort_mode_falls_back_to_default(gui_config):
    load, _ = gui_config
    config = load({
        "Scheduler": {
            "SortMode": "alphabetical",
        }
    })

    assert config.get(config.schedulerSortMode) == "priority"


class _AccountConfig:
    def __init__(self, root, legacy_state="on"):
        self.config_dir = str(root)
        self.legacy_state = legacy_state
        self.set_calls = []

    def get(self, key, default=None):
        if key == "new_event_enable_state":
            return self.legacy_state
        return default

    def set(self, key, value):
        self.set_calls.append((key, value))
        self.legacy_state = value

    def get_main_thread(self):
        return None


def test_scheduler_combo_restores_and_writes_account_value_only(
        app, gui_config, tmp_path, monkeypatch):
    load, config_path = gui_config
    load({
        "Scheduler": {
            "SortMode": "priority",
        }
    })
    account_dir = tmp_path / "account"
    account_dir.mkdir()
    account_json = account_dir / "config.json"
    event_json = account_dir / "event.json"
    account_json.write_text(
        json.dumps({"new_event_enable_state": "on"}), encoding="utf-8")
    event_json.write_text(json.dumps([{"event_name": "keep"}]), encoding="utf-8")
    account_before = account_json.read_bytes()
    event_before = event_json.read_bytes()
    account = _AccountConfig(account_dir, legacy_state="on")

    monkeypatch.setattr(process.threading.Thread, "start", lambda self: None)
    monkeypatch.setattr(
        process.expand.__dict__["featureSwitch"], "Layout",
        lambda config: process.QWidget())

    fragment = process.ProcessFragment(None, account)
    assert fragment.scheduler_selector.currentIndex() == 0

    fragment.scheduler_selector._onItemClicked(1)
    app.processEvents()

    persisted = json.loads(config_path.read_text(encoding="utf-8"))
    assert persisted["Scheduler"] == {"SortMode": "priority"}
    assert account.legacy_state == "off"
    assert account.set_calls == [("new_event_enable_state", "off")]
    assert account_json.read_bytes() == account_before
    assert event_json.read_bytes() == event_before
    fragment.close()


@pytest.mark.parametrize(
    ("preference", "default_enabled", "expected_enabled"),
    [
        ("default", True, True),
        ("on", False, True),
        ("off", True, False),
    ],
)
def test_check_event_config_uses_account_new_event_preference(
        gui_config, tmp_path, monkeypatch, preference, default_enabled,
        expected_enabled):
    load, _ = gui_config
    load({"Scheduler": {"SortMode": "priority"}})
    monkeypatch.chdir(tmp_path)
    account_dir = Path("config") / "account"
    account_dir.mkdir(parents=True)
    existing = {
        "event_name": "existing",
        "func_name": "existing_func",
        "daily_reset": [[0, 0, 0]],
        "enabled": True,
    }
    added = {
        "event_name": "added",
        "func_name": "added_func",
        "daily_reset": [[0, 0, 0]],
        "enabled": default_enabled,
    }
    (account_dir / "event.json").write_text(
        json.dumps([existing]), encoding="utf-8")
    monkeypatch.setattr(
        window.default_config, "EVENT_DEFAULT_CONFIG",
        json.dumps([existing, added]))
    user_config = SimpleNamespace(
        server_mode="CN",
        config=SimpleNamespace(new_event_enable_state=preference),
    )

    window.check_event_config("account", user_config)

    result = json.loads(
        (account_dir / "event.json").read_text(encoding="utf-8"))
    assert result[1]["func_name"] == "added_func"
    assert result[1]["enabled"] is expected_enabled


class _UpdateSignals(QObject):
    update_signal = pyqtSignal()


class _FeatureConfig:
    def __init__(self, config_dir):
        self.config_dir = str(config_dir)
        self.signals = _UpdateSignals()

    def get_signal(self, key):
        assert key == "update_signal"
        return self.signals.update_signal


def _write_events(config_dir):
    config_dir.mkdir()
    events = [
        {
            "event_name": "priority_first",
            "func_name": "priority_first",
            "priority": 1,
            "next_tick": 200,
            "enabled": True,
        },
        {
            "event_name": "tick_first",
            "func_name": "tick_first",
            "priority": 2,
            "next_tick": 100,
            "enabled": True,
        },
    ]
    (config_dir / "event.json").write_text(
        json.dumps(events), encoding="utf-8")
    return _FeatureConfig(config_dir)


def _displayed_events(layout):
    return [label.text() for label in layout.qLabels]


def test_sort_combo_applies_persisted_mode_on_first_construction(
        app, gui_config, tmp_path):
    load, _ = gui_config
    load({
        "Scheduler": {
            "SortMode": "next_tick",
        }
    })
    layout = featureSwitch.Layout(config=_write_events(tmp_path / "account"))

    assert layout.op_3.currentIndex() == 1
    assert _displayed_events(layout) == ["tick_first", "priority_first"]
    layout.close()


def test_sort_change_updates_an_already_open_account_fragment(
        app, gui_config, tmp_path):
    load, config_path = gui_config
    load({
        "Scheduler": {
            "SortMode": "priority",
        }
    })
    first = featureSwitch.Layout(config=_write_events(tmp_path / "first"))
    second = featureSwitch.Layout(config=_write_events(tmp_path / "second"))
    assert _displayed_events(first) == ["priority_first", "tick_first"]
    assert _displayed_events(second) == ["priority_first", "tick_first"]

    first.op_3._onItemClicked(1)
    app.processEvents()

    assert first.op_3.currentIndex() == 1
    assert second.op_3.currentIndex() == 1
    assert _displayed_events(first) == ["tick_first", "priority_first"]
    assert _displayed_events(second) == ["tick_first", "priority_first"]
    assert json.loads(config_path.read_text(
        encoding="utf-8"))["Scheduler"]["SortMode"] == "next_tick"
    first.close()
    second.close()
