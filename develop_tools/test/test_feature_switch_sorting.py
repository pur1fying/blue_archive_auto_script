"""Regression tests for the scheduler sorting view (featureSwitch).

Covers the crash fix: switching the sort mode must update the existing
cell widgets in place rather than recreating the table or its widgets.

Background of the crash (exit code 0xC0000409 = STATUS_STACK_BUFFER_OVERRUN,
raised by Qt's Q_ASSERT / __fastfail):

* The old `_sort()` called `self.tableView.deleteLater()` and then created
  a fresh `TableWidget(self)`. The old table and its cell widgets were
  kept alive by the deferred-deletion queue until the event loop ran.
* Switching theme calls `setTheme`, which (a) emits `themeChanged` and
  then (b) calls `updateStyleSheet()`. `updateStyleSheet` walks every
  widget registered in qfluentwidgets' global `styleSheetManager`
  (a `WeakKeyDictionary`) and calls `setStyleSheet` on it.
* The OLD widgets were still in that manager, so `updateStyleSheet`
  touched them mid-deferred-deletion and Qt aborted with a stack-buffer
  overrun.

The current fix keeps one set of cell widgets for the whole lifetime of
the table. `_sort()` only rewrites their text/state -- it never
allocates a new widget per sort, so there are no stale widgets to leak
into the style-sheet manager and nothing can race with `setTheme`.

These tests guard against regressing back into the old behaviour (any
attempt to recreate widgets on sort will trip the leak guard below).
"""

import json
import os
import shutil
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import Theme, qconfig, setTheme

from gui.components.expand.featureSwitch import Layout
from gui.util.config_gui import COLOR_THEME
from gui.util.translator import baasTranslator as bt


class _Config(QObject):
    update_signal = pyqtSignal()

    def __init__(self, config_dir):
        super().__init__()
        self.config_dir = config_dir

    def get_signal(self, name):
        assert name == "update_signal"
        return self.update_signal


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "feature_switch_test_cfg")


def _write_fixture():
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    events = [
        {
            "event_name": "first",
            "enabled": True,
            "next_tick": 1_700_000_000,
            "priority": 2,
            "interval": 0,
            "daily_reset": [],
            "disabled_time_range": [],
            "pre_task": [],
            "post_task": [],
            "func_name": "first",
        },
        {
            "event_name": "second",
            "enabled": False,
            "next_tick": 1_600_000_000,
            "priority": 1,
            "interval": 0,
            "daily_reset": [],
            "disabled_time_range": [],
            "pre_task": [],
            "post_task": [],
            "func_name": "second",
        },
    ]
    with open(os.path.join(FIXTURE_DIR, "event.json"), "w", encoding="utf-8") as file:
        json.dump(events, file)


class FeatureSwitchSortingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        _write_fixture()
        self.layout = Layout(config=_Config(FIXTURE_DIR))

    def tearDown(self):
        self.layout.close()
        self.layout.deleteLater()
        self.app.processEvents()
        shutil.rmtree(FIXTURE_DIR, ignore_errors=True)

    def _select_sort_mode(self, index):
        """Mirror the combo box user-selection signal."""
        self.layout.op_3.setCurrentIndex(index)
        self.layout.op_3.currentIndexChanged.emit(index)
        self.app.processEvents()

    def test_sort_rewrites_widgets_in_place(self):
        table_before_sort = self.layout.tableView
        qLabels_before = list(self.layout.qLabels)
        times_before = list(self.layout.times)
        check_boxes_before = list(self.layout.check_boxes)
        config_buttons_before = list(self.layout.config_buttons)

        self._select_sort_mode(1)

        # Same widgets (no rebuild on sort)
        self.assertIs(table_before_sort, self.layout.tableView)
        self.assertIs(qLabels_before[0], self.layout.qLabels[0])
        self.assertIs(qLabels_before[1], self.layout.qLabels[1])
        self.assertIs(times_before[0], self.layout.times[0])
        self.assertIs(times_before[1], self.layout.times[1])
        self.assertIs(check_boxes_before[0], self.layout.check_boxes[0])
        self.assertIs(check_boxes_before[1], self.layout.check_boxes[1])
        self.assertIs(config_buttons_before[0], self.layout.config_buttons[0])
        self.assertIs(config_buttons_before[1], self.layout.config_buttons[1])

        # Their text/state was rewritten to reflect the new ordering.
        self.assertEqual(['first', 'second'], [
            bt.undo(label.text()) for label in self.layout.qLabels
        ])
        self.assertEqual([True, False], [
            cb.isChecked() for cb in self.layout.check_boxes
        ])
        self.assertEqual(2, self.layout.tableView.rowCount())
        self.assertEqual(2, len(self.layout.qLabels))
        self.assertEqual(2, len(self.layout.times))
        self.assertEqual(2, len(self.layout.check_boxes))
        self.assertEqual(2, len(self.layout.config_buttons))
        self.assertEqual(2, len(self.layout.boxes))
        self.assertEqual(['first', 'second'], [
            item['event_name'] for item in self.layout._crt_order_config
        ])
        self.assertEqual([True, False], self.layout.enable_list)
        self.assertEqual(['first', 'second'], self.layout.labels)

        # labels inside a QTableWidget need an explicit color stylesheet
        # to stay readable in dark mode
        for label in self.layout.qLabels:
            self.assertIn(
                COLOR_THEME[qconfig.theme.value]['text'],
                label.styleSheet(),
            )

        self._select_sort_mode(0)
        self.assertIs(table_before_sort, self.layout.tableView)
        # In-place rewrite: text/state swapped, but still the same widgets
        self.assertEqual(['second', 'first'], [
            bt.undo(label.text()) for label in self.layout.qLabels
        ])
        self.assertEqual([False, True], [
            cb.isChecked() for cb in self.layout.check_boxes
        ])
        self.assertEqual(['second', 'first'], [
            item['event_name'] for item in self.layout._crt_order_config
        ])
        self.assertEqual(['second', 'first'], self.layout.labels)

    def test_sort_repeatedly_keeps_widgets_alive_and_does_not_leak(self):
        """Regression guard for the crash bug.

        Every sort must reuse the same set of widgets -- no new widgets may
        be allocated and none may be destroyed. If the implementation ever
        regresses to recreating widgets on sort, the assertion below
        catches it before the leaked widgets can crash a later
        ``setTheme`` call.
        """
        table = self.layout.tableView
        labels = list(self.layout.qLabels)
        times = list(self.layout.times)
        check_boxes = list(self.layout.check_boxes)
        boxes = list(self.layout.boxes)

        # CaptionLabel connects a lambda to qconfig.themeChanged in its
        # constructor; any widget leak will inflate this number.
        from qfluentwidgets import qconfig as _qconfig
        receivers_before = _qconfig.receivers(_qconfig.themeChanged)

        for _ in range(10):
            self._select_sort_mode(1)
            self._select_sort_mode(0)
            self.assertIs(table, self.layout.tableView)
            # No widgets were created or destroyed across 10 sort toggles.
            self.assertEqual(labels, list(self.layout.qLabels))
            self.assertEqual(times, list(self.layout.times))
            self.assertEqual(check_boxes, list(self.layout.check_boxes))
            self.assertEqual(boxes, list(self.layout.boxes))
            for label in self.layout.qLabels:
                label.text()  # widgets stay alive -> no stale C++ objects
            self.app.processEvents()

        self.assertEqual(2, self.layout.tableView.rowCount())

        # No extra widgets registered in qfluentwidgets' style sheet
        # manager -- this is the exact condition that used to race with
        # setTheme() and crash the app.
        receivers_after = _qconfig.receivers(_qconfig.themeChanged)
        self.assertEqual(receivers_before, receivers_after,
                         'sort must not register new widgets with the '
                         'global style sheet manager')

    def test_theme_change_updates_label_colors(self):
        current_theme = Theme(qconfig.theme.value)
        next_theme = Theme.DARK if current_theme is Theme.LIGHT else Theme.LIGHT
        self.addCleanup(setTheme, current_theme)
        setTheme(next_theme)
        self.app.processEvents()

        expected_color = COLOR_THEME[next_theme.value]['text'].lower()
        for label in self.layout.qLabels:
            self.assertIn(expected_color, label.styleSheet().lower())
            self.assertEqual(
                QColor(expected_color),
                QColor(label.palette().color(QPalette.WindowText)),
            )

    def test_sort_then_theme_change_does_not_crash(self):
        """End-to-end regression for the original user-reported crash:
        switching the sort order on the scheduler page and then changing
        the theme in the settings page must not crash the app.
        """
        # Trigger a sort
        self._select_sort_mode(1)
        self._select_sort_mode(0)
        self._select_sort_mode(1)

        # Now change theme a few times -- the exact sequence that used to
        # produce exit code 0xC0000409 (STATUS_STACK_BUFFER_OVERRUN).
        for theme in (Theme.DARK, Theme.LIGHT, Theme.DARK, Theme.LIGHT):
            setTheme(theme)
            self.app.processEvents()

        # All labels are still alive and styled correctly.
        for label in self.layout.qLabels:
            label.text()  # accessing the wrapper must not raise


if __name__ == "__main__":
    unittest.main()
