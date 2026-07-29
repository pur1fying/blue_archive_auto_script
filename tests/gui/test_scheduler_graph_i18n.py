"""Translation coverage for the scheduler graph editor."""

from pathlib import Path
from xml.etree import ElementTree

import pytest
from PyQt5.QtCore import QCoreApplication, QTranslator
from PyQt5.QtWidgets import QApplication


PROJECT_ROOT = Path(__file__).resolve().parents[2]
I18N_DIR = PROJECT_ROOT / "gui" / "i18n"
LOCALES = ("en_US", "ja_JP", "ko_KR")
REQUIRED_SOURCES = (
    "表格视图",
    "图形视图",
    "前置任务",
    "作为前置任务",
    "后置任务",
    "作为后置任务",
    "启用",
    "下次执行时间",
    "调度关系无效",
    "时间格式无效，请使用 YYYY-MM-DD HH:MM:SS",
    "调度配置保存失败",
    "调度配置包含无法显示的任务关系",
    "调度配置中已存在循环依赖",
    "图形视图需要安装 NodeGraphQt",
)
CONTEXTS = {
    "表格视图": "ProcessFragment",
    "图形视图": "ProcessFragment",
    "图形视图需要安装 NodeGraphQt": "ProcessFragment",
    "前置任务": "SchedulerGraphView",
    "作为前置任务": "SchedulerGraphView",
    "后置任务": "SchedulerGraphView",
    "作为后置任务": "SchedulerGraphView",
    "启用": "SchedulerGraphView",
    "下次执行时间": "SchedulerGraphView",
    "调度关系无效": "SchedulerGraphView",
    "时间格式无效，请使用 YYYY-MM-DD HH:MM:SS": "SchedulerGraphView",
    "调度配置保存失败": "SchedulerGraphView",
    "调度配置包含无法显示的任务关系": "SchedulerGraphView",
    "调度配置中已存在循环依赖": "SchedulerGraphView",
}


def _catalog_messages(path: Path):
    root = ElementTree.parse(path).getroot()
    return {
        message.findtext("source"): message.find("translation")
        for message in root.iter("message")
    }


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_catalog_entries_are_complete(locale):
    """Missing or unfinished graph strings would leak Chinese into the UI."""
    messages = _catalog_messages(I18N_DIR / f"{locale}.ts")

    for source in REQUIRED_SOURCES:
        translation = messages.get(source)
        assert translation is not None, f"{locale} is missing {source!r}"
        assert translation.text and translation.text.strip(), (
            f"{locale} leaves {source!r} blank"
        )
        assert translation.get("type") != "unfinished", (
            f"{locale} leaves {source!r} unfinished"
        )
        assert translation.text.strip() != source, (
            f"{locale} copies the Chinese source for {source!r}"
        )


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("locale", LOCALES)
def test_scheduler_graph_qm_translates_representative_labels_and_errors(
    app, locale
):
    """Compiled catalogs must translate graph UI strings in a real QApplication."""
    translator = QTranslator(app)
    assert translator.load(str(I18N_DIR / f"{locale}.qm"))
    app.installTranslator(translator)
    try:
        for source, context in CONTEXTS.items():
            translated = QCoreApplication.translate(context, source)
            assert translated and translated != source, (
                f"{locale} returns raw Chinese for {context}:{source}"
            )
    finally:
        app.removeTranslator(translator)
