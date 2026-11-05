"""Regression coverage for the legacy update settings card (issue #612)."""
import os
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from deploy.installer.const import get_remote_sha_methods, get_remote_sha_methods_for_channel
from gui.components.expand import baasUpdateConfig as update
from gui.components.template_card import SimpleSettingCard


class Config:
    def __init__(self, channel="stable", mirror_available=True):
        methods = get_remote_sha_methods_for_channel(channel)
        self.values = {
            "General.channel": channel,
            "General.mirrorc_cdk": "" if mirror_available else None,
            "General.current_BAAS_version": "a" * 40,
            "General.get_remote_sha_method": "github",
            "URLs.REPO_URL_HTTP": methods[0]["url"],
        }

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set_and_save(self, key, value):
        self.values[key] = value


class UpdateSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widgets = []
        self.patchers = [
            patch.object(update, "success"),
            patch.object(update, "error"),
            patch.object(update.TestGetRemoteShaMethodWorker, "github_api_get_latest_sha",
                         return_value=(True, "b" * 40)),
            patch.object(update.TestGetRemoteShaMethodWorker, "pygit2_get_latest_sha",
                         return_value=(True, "b" * 40)),
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self):
        for widget in reversed(self.widgets):
            widget.close()
            widget.deleteLater()
        QTest.qWait(300)  # let the card animation and deferred deletes finish
        for p in reversed(self.patchers):
            p.stop()

    def wait_until(self, predicate, timeout=3000):
        deadline = time.monotonic() + timeout / 1000
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate(), "timed out waiting for Qt event")

    def panel(self, config):
        card = SimpleSettingCard(sub_view=update, config=config)
        self.widgets.append(card)
        card.show()
        card.toggleExpand()
        return card, card.expand_view

    def test_expand_sources_match_channel_and_saved_selection(self):
        original_methods = [item.copy() for item in get_remote_sha_methods]
        for channel in ("stable", "dev"):
            for available in (False, True):
                with self.subTest(channel=channel, mirror_available=available):
                    config = Config(channel, available)
                    card, panel = self.panel(config)
                    expected = [item for item in get_remote_sha_methods_for_channel(channel)
                                if available or item["name"] != "mirrorc"]
                    self.assertEqual(panel.test_result_table.rowCount(), len(expected))
                    self.assertEqual(panel.get_remote_sha_method_ComboBox.count(), len(expected))
                    for index, method in enumerate(expected):
                        item = panel.test_result_table.item(index, 0)
                        self.assertEqual(item.data(Qt.UserRole), method)
                        # Fluent ComboBox emits its change signal for user selections.
                        combo = panel.get_remote_sha_method_ComboBox
                        combo._onItemClicked((index + 1) % len(expected))
                        combo._onItemClicked(index)
                        self.assertEqual(config.get("General.get_remote_sha_method"), method["name"])
                        if method.get("url"):
                            self.assertEqual(panel.REPO_URL_CHECK_UPDATE_METHOD_mapping[method["url"]], method["name"])
                    card.toggleExpand()
                    card.toggleExpand()
                    self.assertIs(card.expand_view, panel)
        self.assertEqual(get_remote_sha_methods, original_methods)

    def test_newest_detection_wins_and_updates_on_gui_thread(self):
        started = threading.Event()
        release = threading.Event()
        main_thread = threading.get_ident()
        calls = []
        delivered = []
        config = Config()
        card, panel = self.panel(config)
        self.wait_until(lambda: panel._BAAS_remote_version_label.text() == "b" * 40)
        original_update = panel._update_ui_after_detection

        def record_update():
            calls.append(threading.get_ident())
            original_update()

        def slow_github(_config):
            started.set()
            release.wait(3)
            return True, "c" * 40

        panel._update_ui_after_detection = record_update
        panel._update_detection_finished.connect(lambda generation, result: delivered.append(result["sha"]))
        try:
            with patch.object(update.TestGetRemoteShaMethodWorker, "github_api_get_latest_sha", side_effect=slow_github):
                panel._detect_update_method_and_update_ui()
                self.assertTrue(started.wait(2))
                gitee = next(item for item in get_remote_sha_methods_for_channel("stable") if item["name"] == "gitee")
                config.values["URLs.REPO_URL_HTTP"] = gitee["url"]
                panel._detect_update_method_and_update_ui()
                self.wait_until(lambda: bool(calls))
                self.assertEqual(panel._BAAS_remote_version_label.text(), "b" * 40)
                release.set()
                self.wait_until(lambda: "c" * 40 in delivered)
                self.assertEqual(panel._BAAS_remote_version_label.text(), "b" * 40)
                self.assertEqual(calls, [main_thread])
        finally:
            release.set()

    def test_manual_cdk_test_immediately_after_edit_saves_success(self):
        config = Config()
        card, panel = self.panel(config)
        response = SimpleNamespace(code=0, cdk_expired_time=None, latest_version_name="c" * 40)
        with patch.object(panel._mirrorc_inst, "get_latest_version", return_value=response):
            panel._mirrorc_cdk_TextEdit.setPlainText("new-test-cdk")
            panel._test_mirrorc_cdk_button.click()
            self.wait_until(lambda: panel._test_mirrorc_cdk_button.isEnabled())
        self.assertEqual(config.get("General.mirrorc_cdk"), "new-test-cdk")

    def test_cdk_failure_restores_controls_and_redacts_secret(self):
        config = Config()
        card, panel = self.panel(config)
        secret = "fake-test-cdk"
        panel._mirrorc_cdk_TextEdit.setPlainText(secret)
        with patch.object(panel._mirrorc_inst, "get_latest_version", side_effect=RuntimeError(secret)):
            panel._test_and_set_mirrorc_cdk_state(save=True)
            self.assertFalse(panel._test_mirrorc_cdk_button.isEnabled())
            self.wait_until(lambda: update.error.called)
        self.assertTrue(panel._test_mirrorc_cdk_button.isEnabled())
        self.assertTrue(panel._mirrorc_cdk_TextEdit.isEnabled())
        self.assertNotIn(secret, str(update.error.call_args))
        self.assertEqual(config.get("General.mirrorc_cdk"), "")


if __name__ == "__main__":
    unittest.main()
