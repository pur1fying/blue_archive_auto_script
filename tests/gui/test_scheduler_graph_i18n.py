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
    ("SchedulerGraphView", "无法读取调度事件配置。"),
    ("SchedulerGraphView", "调度事件配置的格式无效。"),
    ("SchedulerGraphView", "调度事件配置缺少必需字段。"),
    ("SchedulerGraphView", "调度事件配置包含无效字段值。"),
    (
        "SchedulerGraphView",
        "调度事件配置包含重复的任务标识“{func_name}”。",
    ),
    ("SchedulerGraphView", "调度图布局包含无效的节点坐标。"),
    (
        "SchedulerGraphView",
        "调度任务“{func_name}”不存在于事件配置中。",
    ),
    ("SchedulerGraphView", "调度关系类型“{kind}”无效。"),
    (
        "SchedulerGraphView",
        "调度关系引用了不存在的任务“{func_name}”。",
    ),
    ("SchedulerGraphView", "调度任务“{func_name}”不能依赖自身。"),
    (
        "SchedulerGraphView",
        "任务“{owner_func}”与“{related_func}”之间已存在相同的调度关系。",
    ),
    (
        "SchedulerGraphView",
        "连接任务“{owner_func}”与“{related_func}”会形成循环依赖。",
    ),
    ("SchedulerGraphView", "只能连接或断开类型匹配的调度关系端口。"),
    (
        "SchedulerGraphView",
        "时间格式无效，请使用 YYYY-MM-DD HH:MM:SS。",
    ),
    ("SchedulerGraphView", "调度配置保存失败。"),
    ("SchedulerGraphView", "调度图加载失败。"),
    (
        "SchedulerGraphView",
        "任务“{owner_func}”引用了未知的调度依赖“{related_func}”，该关系无法显示。",
    ),
    ("SchedulerGraphView", "调度配置中已存在循环依赖。"),
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
        "invalid_config": (
            "Scheduler event configuration is missing required fields."
        ),
        "self_link": (
            "Scheduler task “{func_name}” cannot depend on itself."
        ),
        "duplicate": (
            "The same scheduler relationship between “{owner_func}” and "
            "“{related_func}” already exists."
        ),
        "cycle_error": (
            "Connecting tasks “{owner_func}” and “{related_func}” would "
            "create a scheduler cycle."
        ),
        "missing_task": (
            "Scheduler task “{func_name}” does not exist in the event "
            "configuration."
        ),
        "time": "Invalid time format. Use YYYY-MM-DD HH:MM:SS.",
        "save": "Failed to save scheduler configuration.",
        "unknown_dependency": (
            "Task “{owner_func}” references unknown scheduler dependency "
            "“{related_func}”; this relationship cannot be displayed."
        ),
        "existing_cycle": (
            "Scheduler configuration already contains a circular dependency."
        ),
    },
    "ja_JP": {
        "ports": ("前提タスク", "後続タスクとして使用", "前提タスクとして使用", "後続タスク"),
        "enabled": "有効",
        "next_tick": "次回実行時刻",
        "invalid_config": "スケジューラーイベント設定に必須フィールドがありません。",
        "self_link": "スケジューラータスク「{func_name}」は自身に依存できません。",
        "duplicate": (
            "「{owner_func}」と「{related_func}」の間には同じ"
            "スケジューラー関係が既に存在します。"
        ),
        "cycle_error": (
            "タスク「{owner_func}」と「{related_func}」を接続すると"
            "循環依存が発生します。"
        ),
        "missing_task": (
            "スケジューラーイベント設定にタスク「{func_name}」が"
            "存在しません。"
        ),
        "time": "時刻の形式が無効です。YYYY-MM-DD HH:MM:SS を使用してください。",
        "save": "スケジューラー設定の保存に失敗しました。",
        "unknown_dependency": (
            "タスク「{owner_func}」は不明なスケジューラー依存先"
            "「{related_func}」を参照しているため、この関係は表示できません。"
        ),
        "existing_cycle": "スケジューラー設定には循環依存が既に存在します。",
    },
    "ko_KR": {
        "ports": ("선행 작업", "후속 작업으로 사용", "선행 작업으로 사용", "후속 작업"),
        "enabled": "활성화됨",
        "next_tick": "다음 실행 시간",
        "invalid_config": "스케줄러 이벤트 구성에 필수 필드가 없습니다.",
        "self_link": (
            "스케줄러 작업 ‘{func_name}’에 자기 자신을 종속 작업으로 "
            "지정할 수 없습니다."
        ),
        "duplicate": (
            "‘{owner_func}’ 작업과 ‘{related_func}’ 작업 사이에 동일한 "
            "스케줄러 관계가 이미 있습니다."
        ),
        "cycle_error": (
            "‘{owner_func}’ 작업과 ‘{related_func}’ 작업을 연결하면 "
            "순환 종속성이 생성됩니다."
        ),
        "missing_task": (
            "스케줄러 이벤트 구성에서 ‘{func_name}’ 작업을 찾을 수 없습니다."
        ),
        "time": (
            "시간 형식이 잘못되었습니다. YYYY-MM-DD HH:MM:SS 형식을 "
            "사용하세요."
        ),
        "save": "스케줄러 구성을 저장하지 못했습니다.",
        "unknown_dependency": (
            "‘{owner_func}’ 작업에서 참조하는 스케줄러 종속성 "
            "‘{related_func}’을 찾을 수 없어 이 관계를 표시할 수 없습니다."
        ),
        "existing_cycle": "스케줄러 구성에 이미 순환 종속성이 있습니다.",
    },
}
RAW_ENGLISH_DIAGNOSTICS = (
    "Event record is missing scheduler fields.",
    "A scheduler task cannot depend on itself.",
    "The same dependency metadata already exists.",
    "The dependency would close a scheduler cycle.",
    "Unknown scheduler task",
    "Time must use YYYY-MM-DD HH:MM:SS local time.",
    "Unknown scheduler dependency",
    "Scheduler dependency cycle detected",
    "simulated",
)


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


def _assert_no_raw_english_diagnostic(locale, message):
    if locale == "en_US":
        return
    assert all(text not in message for text in RAW_ENGLISH_DIAGNOSTICS)


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
            assert view._message_label.text() == EXPECTED[locale][
                "cycle_error"
            ].format(
                owner_func="b",
                related_func="a",
            )
            _assert_no_raw_english_diagnostic(
                locale, view._message_label.text()
            )

            line_edit = view.node_for_func("a").get_widget(
                "next_tick"
            ).get_custom_widget()
            line_edit.setText("not a scheduler time")
            line_edit.editingFinished.emit()
            app.processEvents()
            assert len(errors) == 2
            assert view._message_label.text() == EXPECTED[locale]["time"]
            _assert_no_raw_english_diagnostic(
                locale, view._message_label.text()
            )

            blocked_path = tmp_path / "blocked-save-target"
            blocked_path.mkdir()
            view._store.graph_path = blocked_path
            view.save_layout()
            assert len(errors) == 3
            assert view._message_label.text() == EXPECTED[locale]["save"]
            _assert_no_raw_english_diagnostic(
                locale, view._message_label.text()
            )
        finally:
            _close_view(view, app)


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_qm_translates_complete_structured_store_errors(
    app, tmp_path, locale
):
    _write_events(
        tmp_path,
        [_record("a", "Task A"), _record("b", "Task B")],
    )
    with _installed_translator(app, locale):
        view = SchedulerGraphView(tmp_path)
        try:
            errors = QSignalSpy(view.error_occurred)

            view.port_for("a", "post_output").connect_to(
                view.port_for("a", "post_input")
            )
            app.processEvents()
            assert len(errors) == 1
            assert view._message_label.text() == EXPECTED[locale][
                "self_link"
            ].format(func_name="a")

            view.port_for("a", "post_output").connect_to(
                view.port_for("b", "post_input")
            )
            with pytest.raises(Exception) as duplicate:
                view._store.add_relationship("post", "a", "b")
            view._show_error(duplicate.value)
            assert len(errors) == 2
            assert view._message_label.text() == EXPECTED[locale][
                "duplicate"
            ].format(owner_func="a", related_func="b")

            with pytest.raises(Exception) as missing:
                view._store.update_enabled("missing", False)
            view._show_error(missing.value)
            assert len(errors) == 3
            assert view._message_label.text() == EXPECTED[locale][
                "missing_task"
            ].format(func_name="missing")

            _assert_no_raw_english_diagnostic(
                locale, "\n".join(str(item[0]) for item in errors)
            )
        finally:
            _close_view(view, app)


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_qm_translates_complete_invalid_config_error(
    app, tmp_path, locale
):
    _write_events(tmp_path, [{"func_name": "broken"}])

    with _installed_translator(app, locale):
        view = SchedulerGraphView(tmp_path)
    try:
        message = view._message_label.text()
        assert message == EXPECTED[locale]["invalid_config"]
        _assert_no_raw_english_diagnostic(locale, message)
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
        unknown_dependency, existing_cycle = (
            view._message_label.text().splitlines()
        )
        assert unknown_dependency == EXPECTED[locale][
            "unknown_dependency"
        ].format(owner_func="a", related_func="missing")
        assert existing_cycle == EXPECTED[locale]["existing_cycle"]
        _assert_no_raw_english_diagnostic(
            locale, view._message_label.text()
        )
    finally:
        _close_view(view, app)
