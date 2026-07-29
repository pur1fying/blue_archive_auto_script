"""Runtime translation coverage for the scheduler graph editor."""

from contextlib import contextmanager
from datetime import datetime
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PyQt5.QtCore import QTranslator
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication

import gui


PROJECT_ROOT = Path(__file__).resolve().parents[2]
gui.__path__.append(str(PROJECT_ROOT / "gui"))

from gui.components.scheduler_graph import SchedulerGraphView
I18N_DIR = PROJECT_ROOT / "gui" / "i18n"
LOCALES = ("en_US", "ja_JP", "ko_KR")
DISPLAY_TIME = "2024-02-03 04:05:06"
DISPLAY_TIMESTAMP = int(datetime(2024, 2, 3, 4, 5, 6).timestamp())
REQUIRED_CONTEXT_SOURCES = {
    ("ProcessFragment", "表格视图"),
    ("ProcessFragment", "图形视图"),
    ("ProcessFragment", "图形视图需要安装 NodeGraphQt"),
    ("SchedulerGraphView", "前置任务"),
    ("SchedulerGraphView", "作为前置任务"),
    ("SchedulerGraphView", "后置任务"),
    ("SchedulerGraphView", "作为后置任务"),
    ("SchedulerGraphView", "启用"),
    ("SchedulerGraphView", "下次执行时间"),
    ("SchedulerGraphView", "调度关系无效"),
    ("SchedulerGraphView", "时间格式无效，请使用 YYYY-MM-DD HH:MM:SS"),
    ("SchedulerGraphView", "调度配置保存失败"),
    ("SchedulerGraphView", "调度配置包含无法显示的任务关系"),
    ("SchedulerGraphView", "调度配置中已存在循环依赖"),
}
EXPECTED = {
    "en_US": {
        "ports": (
            "Prerequisite Task",
            "Use as Dependent Task",
            "Use as a Prerequisite Task",
            "Dependent Task",
        ),
        "enabled": "Enabled",
        "next_tick": "Next Execution Time",
        "relationship": "Invalid Scheduler Relationship",
        "time": "Invalid time format. Use YYYY-MM-DD HH:MM:SS",
        "save": "Failed to save scheduler configuration",
        "unavailable": (
            "Scheduler configuration contains task relationships that "
            "cannot be displayed"
        ),
        "cycle": "Scheduler configuration already contains a circular dependency",
    },
    "ja_JP": {
        "ports": ("前提タスク", "後続タスクとして使用", "前提タスクとして使用", "後続タスク"),
        "enabled": "有効",
        "next_tick": "次回実行時刻",
        "relationship": "スケジューラー関係が無効です",
        "time": "時刻の形式が無効です。YYYY-MM-DD HH:MM:SS を使用してください",
        "save": "スケジューラー設定の保存に失敗しました",
        "unavailable": "スケジューラー設定には表示できないタスク関係が含まれています",
        "cycle": "スケジューラー設定に循環依存が既に存在します",
    },
    "ko_KR": {
        "ports": ("선행 작업", "후속 작업으로 사용", "선행 작업으로 사용", "후속 작업"),
        "enabled": "활성화됨",
        "next_tick": "다음 실행 시간",
        "relationship": "잘못된 스케줄러 관계",
        "time": "시간 형식이 잘못되었습니다. YYYY-MM-DD HH:MM:SS 형식을 사용하세요",
        "save": "스케줄러 구성 저장에 실패했습니다",
        "unavailable": "스케줄러 구성에 표시할 수 없는 작업 관계가 포함되어 있습니다",
        "cycle": "스케줄러 구성에 이미 순환 종속성이 있습니다",
    },
}


def _catalog_messages(path: Path):
    root = ElementTree.parse(path).getroot()
    return {
        (context.findtext("name"), message.findtext("source")): message.find(
            "translation"
        )
        for context in root.findall("context")
        for message in context.findall("message")
    }


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_catalog_entries_are_complete(locale):
    """Missing or unfinished graph strings would leak Chinese into the UI."""
    messages = _catalog_messages(I18N_DIR / f"{locale}.ts")

    for context_source in REQUIRED_CONTEXT_SOURCES:
        translation = messages.get(context_source)
        assert translation is not None, (
            f"{locale} is missing {context_source!r}"
        )
        assert translation.text and translation.text.strip(), (
            f"{locale} leaves {context_source!r} blank"
        )
        assert translation.get("type") != "unfinished", (
            f"{locale} leaves {context_source!r} unfinished"
        )
        assert translation.text.strip() != context_source[1], (
            f"{locale} copies the Chinese source for {context_source!r}"
        )


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


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
        json.dumps(records, ensure_ascii=False), encoding="utf-8"
    )


@contextmanager
def _installed_translator(app, locale):
    translator = QTranslator(app)
    assert translator.load(str(I18N_DIR / f"{locale}.qm"))
    app.installTranslator(translator)
    try:
        yield
    finally:
        app.removeTranslator(translator)


def _close_view(view, app):
    view.close()
    view.deleteLater()
    app.processEvents()


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_qm_translates_rendered_port_and_embedded_labels(
    app, tmp_path, locale
):
    """A graph built under a QM must not render source-language controls."""
    _write_events(tmp_path, [_record("a", "Task A")])
    with _installed_translator(app, locale):
        view = SchedulerGraphView(tmp_path)
    try:
        node = view.node_for_func("a")
        assert tuple(node.inputs()) + tuple(node.outputs()) == EXPECTED[locale]["ports"]
        enabled = node.get_widget("enabled")
        next_tick = node.get_widget("next_tick")
        assert enabled.get_label() == EXPECTED[locale]["enabled"]
        assert enabled.get_custom_widget().text() == EXPECTED[locale]["enabled"]
        assert next_tick.get_label() == EXPECTED[locale]["next_tick"]
        assert next_tick.get_custom_widget().text() == DISPLAY_TIME
    finally:
        _close_view(view, app)


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_qm_categorizes_real_mutation_failures(
    app, tmp_path, locale
):
    """Store failures must reach the real graph message label in the active UI language."""
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", post_task=["b"]),
            _record("b", "Task B"),
        ],
    )
    with _installed_translator(app, locale):
        view = SchedulerGraphView(tmp_path)
        try:
            errors = QSignalSpy(view.error_occurred)
            view.port_for("b", "post_output").connect_to(
                view.port_for("a", "post_input")
            )
            app.processEvents()
            assert len(errors) == 1
            assert view._message_label.text().startswith(
                EXPECTED[locale]["relationship"]
            )

            line_edit = view.node_for_func("a").get_widget(
                "next_tick"
            ).get_custom_widget()
            line_edit.setText("not a scheduler time")
            line_edit.editingFinished.emit()
            app.processEvents()
            assert len(errors) == 2
            assert view._message_label.text().startswith(
                EXPECTED[locale]["time"]
            )

            blocked_path = tmp_path / "blocked-save-target"
            blocked_path.mkdir()
            view._store.graph_path = blocked_path
            view.save_layout()
            assert len(errors) == 3
            assert view._message_label.text().startswith(
                EXPECTED[locale]["save"]
            )
        finally:
            _close_view(view, app)


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_qm_categorizes_existing_configuration_warnings(
    app, tmp_path, locale
):
    """Existing unknown and cyclic dependencies must render translated warning categories."""
    _write_events(
        tmp_path,
        [
            _record("a", "Task A", post_task=["b", "missing"]),
            _record("b", "Task B", post_task=["a"]),
        ],
    )
    with _installed_translator(app, locale):
        view = SchedulerGraphView(tmp_path)
    try:
        unavailable, cycle = view._message_label.text().splitlines()
        assert unavailable.startswith(EXPECTED[locale]["unavailable"])
        assert cycle.startswith(EXPECTED[locale]["cycle"])
    finally:
        _close_view(view, app)
