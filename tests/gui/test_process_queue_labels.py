import re
from pathlib import Path

import pytest
from PyQt5.QtCore import QPoint, Qt
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

    assert fragment.listWidget.selectedItems() == []


def test_queue_refresh_does_not_retain_a_current_row(fragment):
    fragment._set_queue_items(["old task"])
    fragment.listWidget.setCurrentRow(0)
    assert fragment.listWidget.currentItem() is not None

    fragment._set_queue_items(["new task"])

    assert fragment.listWidget.currentItem() is None
    assert fragment.listWidget.selectedItems() == []


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
