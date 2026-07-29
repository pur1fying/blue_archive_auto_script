import json

from tests.gui.helpers import SettingsConfig


def test_minimize_to_tray_defaults_false_and_persists_to_gui_json(tmp_path):
    from gui.util.config_gui import ConfigGui
    from qfluentwidgets import qconfig

    path = tmp_path / "gui.json"
    config = ConfigGui()
    qconfig.load(path, config)

    assert config.get(config.minimizeToTray) is False
    config.set(config.minimizeToTray, True)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["MainWindow"]["MinimizeToTray"] is True
    config.set(config.minimizeToTray, False, save=False)


def test_settings_page_exposes_minimize_to_tray_switch(qapp):
    from gui.fragments.settings import SettingsFragment
    from gui.util.config_gui import configGui

    fragment = SettingsFragment(config=SettingsConfig({"name": "Test"}))

    assert fragment.minimizeToTrayCard in fragment.guiGroupItems
    assert fragment.minimizeToTrayCard.configItem is configGui.minimizeToTray
