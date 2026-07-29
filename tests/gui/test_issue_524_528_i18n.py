from pathlib import Path
from xml.etree import ElementTree

import pytest
from PyQt5.QtCore import QTranslator


ROOT = Path(__file__).parents[2]
I18N_DIR = ROOT / "gui" / "i18n"

EXPECTED = {
    "en_US": {
        "ConfigTranslation": {
            "好友清理设置": "Friend Cleanup Settings",
            "设置好友清理条件及需要保留的好友码": (
                "Configure cleanup conditions and friend codes to keep"
            ),
            "无限制决战": "Restriction Release Battle",
            "设置编队方式及复制通关队伍限制": (
                "Configure formation and cleared-team copy limits"
            ),
        },
        "Layout": {
            "使用当前编队": "Use current formation",
            "复制通关队伍": "Copy cleared team",
            "编队方式": "Formation method",
            "最多允许不可用学生数": "Maximum unavailable students",
            "通关队伍最大刷新次数": "Maximum cleared-team refreshes",
            "以下清理条件设为 -1 时表示禁用。": (
                "Set a cleanup condition to -1 to disable it."
            ),
            "好友等级清理阈值": "Friend level cleanup threshold",
            "最后登录天数阈值": "Last login days threshold",
            "上次总力战排名阈值": (
                "Previous Total Assault rank threshold"
            ),
        },
        "SettingsFragment": {
            "最小化到托盘": "Minimize to tray",
            "最小化窗口时隐藏到系统托盘": (
                "Hide the window in the system tray when minimized"
            ),
        },
        "TrayController": {
            "显示主窗口": "Show main window",
            "隐藏主窗口": "Hide main window",
            "退出": "Exit",
        },
    },
    "ja_JP": {
        "ConfigTranslation": {
            "好友清理设置": "フレンド整理設定",
            "设置好友清理条件及需要保留的好友码": (
                "フレンド整理条件と保持するフレンドコードを設定します"
            ),
            "无限制决战": "制約解除決戦",
            "设置编队方式及复制通关队伍限制": (
                "編成方法とクリア編成のコピー制限を設定します"
            ),
        },
        "Layout": {
            "使用当前编队": "現在の編成を使用",
            "复制通关队伍": "クリア編成をコピー",
            "编队方式": "編成方法",
            "最多允许不可用学生数": "使用不可生徒の最大人数",
            "通关队伍最大刷新次数": "クリア編成の最大更新回数",
            "以下清理条件设为 -1 时表示禁用。": (
                "以下の整理条件は -1 に設定すると無効になります。"
            ),
            "好友等级清理阈值": "フレンドレベル整理しきい値",
            "最后登录天数阈值": "最終ログイン日数しきい値",
            "上次总力战排名阈值": "前回総力戦順位しきい値",
        },
        "SettingsFragment": {
            "最小化到托盘": "トレイに最小化",
            "最小化窗口时隐藏到系统托盘": (
                "最小化時にウィンドウをシステムトレイへ隠します"
            ),
        },
        "TrayController": {
            "显示主窗口": "メインウィンドウを表示",
            "隐藏主窗口": "メインウィンドウを隠す",
            "退出": "終了",
        },
    },
    "ko_KR": {
        "ConfigTranslation": {
            "好友清理设置": "친구 정리 설정",
            "设置好友清理条件及需要保留的好友码": (
                "친구 정리 조건과 유지할 친구 코드를 설정합니다"
            ),
            "无限制决战": "제약 해제 결전",
            "设置编队方式及复制通关队伍限制": (
                "편성 방식과 클리어 편성 복사 제한을 설정합니다"
            ),
        },
        "Layout": {
            "使用当前编队": "현재 편성 사용",
            "复制通关队伍": "클리어 편성 복사",
            "编队方式": "편성 방식",
            "最多允许不可用学生数": "사용 불가 학생 최대 인원",
            "通关队伍最大刷新次数": "클리어 편성 최대 새로고침 횟수",
            "以下清理条件设为 -1 时表示禁用。": (
                "다음 정리 조건을 -1로 설정하면 비활성화됩니다."
            ),
            "好友等级清理阈值": "친구 레벨 정리 기준",
            "最后登录天数阈值": "마지막 로그인 일수 기준",
            "上次总力战排名阈值": "이전 총력전 순위 기준",
        },
        "SettingsFragment": {
            "最小化到托盘": "시스템 트레이로 최소화",
            "最小化窗口时隐藏到系统托盘": (
                "창을 최소화할 때 시스템 트레이로 숨깁니다"
            ),
        },
        "TrayController": {
            "显示主窗口": "메인 창 표시",
            "隐藏主窗口": "메인 창 숨기기",
            "退出": "종료",
        },
    },
}

CASES = [
    (language, context, source, expected)
    for language, contexts in EXPECTED.items()
    for context, messages in contexts.items()
    for source, expected in messages.items()
]


def catalog_messages(path):
    root = ElementTree.parse(path).getroot()
    result = {}
    for context in root.findall("context"):
        name = context.findtext("name")
        for message in context.findall("message"):
            source = message.findtext("source")
            translation = message.find("translation")
            result[(name, source)] = (
                "" if translation is None else "".join(translation.itertext()),
                None if translation is None else translation.get("type"),
            )
    return result


@pytest.mark.parametrize(
    ("language", "context", "source", "expected"),
    CASES,
)
def test_ts_catalog_contains_finished_exact_translation(
    language, context, source, expected
):
    messages = catalog_messages(I18N_DIR / f"{language}.ts")

    translation, translation_type = messages[(context, source)]
    assert translation == expected
    assert translation_type != "unfinished"


@pytest.mark.parametrize(
    ("language", "context", "source", "expected"),
    CASES,
)
def test_qm_catalog_loads_exact_translation(
    language, context, source, expected
):
    translator = QTranslator()

    assert translator.load(str(I18N_DIR / f"{language}.qm"))
    assert translator.translate(
        context.encode("utf-8"), source.encode("utf-8")
    ) == expected
