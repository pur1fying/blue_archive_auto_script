#!/usr/bin/env python3
"""Preview the real tools UI with disposable, offline demo configuration.

Example::

    QT_QPA_PLATFORM=offscreen python develop_tools/preview_tools.py \
        --screenshots /tmp/baas-tools --theme both --size 1200x800 --size 760x700

Without --screenshots, opens an interactive tools window. All configuration is
in memory or a temporary directory; network, subprocesses and device tasks are
blocked. Press F6 to switch light/dark themes. --source-root can render a
separately exported revision for comparison.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--screenshots", type=Path, help="Capture all tools and the hall, then exit")
    parser.add_argument("--theme", choices=("light", "dark", "both"), default="light")
    parser.add_argument("--size", action="append", metavar="WIDTHxHEIGHT", help="Repeat for responsive previews")
    parser.add_argument("--tool", default="hall", help="Initial tool ID for interactive mode")
    parser.add_argument("--show-settings", action="store_true", help="Expand display settings in interactive mode")
    parser.add_argument("--scroll-bottom", action="store_true", help="Start the interactive tool at the bottom of its form")
    parser.add_argument("--include-edit", action="store_true", help="Also capture the hall's edit state")
    parser.add_argument("--smoke-actions", action="store_true", help="Exercise navigation, edits, theme round trips and local calculators")
    parser.add_argument("--smoke-only", action="store_true", help="Only capture the additional action states (implies --smoke-actions)")
    return parser.parse_args()


def main():
    args = parse_args()
    source_root = args.source_root.expanduser().resolve()
    screenshot_dir = args.screenshots.expanduser().resolve() if args.screenshots else None
    if (args.smoke_actions or args.smoke_only) and not screenshot_dir:
        raise SystemExit("--smoke-actions and --smoke-only require --screenshots")
    sizes = []
    for value in args.size or ["1200x800"]:
        match = re.fullmatch(r"(\d+)x(\d+)", value)
        if not match:
            raise SystemExit("--size must be WIDTHxHEIGHT")
        sizes.append(tuple(map(int, match.groups())))
    if screenshot_dir:
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, str(source_root))
    sys.dont_write_bytecode = True

    # Run from a throwaway working directory so existing account files and GUI
    # preferences cannot enter the preview, even through relative file reads.
    sandbox = tempfile.TemporaryDirectory(prefix="baas-tools-preview-")
    preview_root = Path(sandbox.name)
    (preview_root / "config").mkdir()
    (preview_root / "config" / "gui.json").write_text(json.dumps({
        "MainWindow": {"Language": "zh_CN"},
        "QFluentWidgets": {"ThemeColor": "#0078d4", "ThemeMode": "Light"},
    }), encoding="utf-8")
    for name in ("gui", "src", "module"):
        if (source_root / name).exists():
            (preview_root / name).symlink_to(source_root / name, target_is_directory=True)
    os.chdir(preview_root)

    from PyQt5.QtCore import QObject, QProcess, Qt, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QPalette
    from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
    from qfluentwidgets import Theme, setTheme

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv[:1])
    app.setFont(QFont("Noto Sans CJK SC", 10))
    callback_errors = []

    def qt_exception_hook(exc_type, value, traceback):
        # Qt otherwise aborts the process for an exception in paintEvent or a
        # signal handler. Keep the preview alive and expose it in report.json.
        message = f"{exc_type.__name__}: {value}"
        if message not in callback_errors:
            callback_errors.append(message)
            print(f"UI callback error: {message}", file=sys.stderr, flush=True)

    sys.excepthook = qt_exception_hook
    current_theme = "dark" if args.theme == "dark" else "light"

    def blocked(*_args, **_kwargs):
        raise RuntimeError("Offline UI preview: network, subprocess and device tasks are disabled")

    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    socket.create_connection = blocked
    subprocess.Popen = blocked
    os.system = blocked
    QProcess.startDetached = blocked

    from core.config.default_config import DEFAULT_CONFIG, STATIC_DEFAULT_CONFIG
    from module.tools import registry
    from module.tools.config_registry import registered_defaults
    registry._STATE_FILE = preview_root / "config" / "tool_plugin_state.json"
    (preview_root / "config" / "event.json").write_text(json.dumps([
        {"event_name": "囤体", "func_name": "hoard_ap", "enabled": False, "next_tick": 0}
    ]), encoding="utf-8")
    tools = registry.get_registry()

    class PreviewSignals(QObject):
        changed = pyqtSignal(object)

    class DeviceTasksDisabled:
        def __getattr__(self, _name):
            return blocked

    class PreviewConfig:
        """The small ConfigSet surface used by actual widget constructors."""
        def __init__(self):
            values = json.loads(DEFAULT_CONFIG)
            values.update(registered_defaults())
            values.update({"name": "界面预览", "hoard_ap_current_ap": "160"})
            self.config = SimpleNamespace(**values)
            self.static_config = SimpleNamespace(**json.loads(STATIC_DEFAULT_CONFIG))
            self.server_mode = "CN"
            self.config_dir = str(preview_root / "config")
            self.signals = PreviewSignals()
            self.main_thread = DeviceTasksDisabled()
            self.window = None
            self._bindings = []

        def get(self, key, default=None):
            return getattr(self.config, key, default)

        def set(self, key, value):
            setattr(self.config, key, value)
            for widget, rule, attribute in self._bindings:
                if "{" + key + "}" in rule:
                    getattr(widget, attribute)(self._format(rule))

        update = set

        def has(self, key):
            return hasattr(self.config, key)

        def save(self):
            pass

        def get_window(self):
            return self.window

        def get_main_thread(self):
            return self.main_thread

        def get_signal(self, _key):
            return self.signals.changed

        def _format(self, rule):
            return re.sub(r"\{([^}]+)\}", lambda match: str(self.get(match[1], "")), rule)

        def inject(self, widget, rule, attribute="setText"):
            self._bindings.append((widget, rule, attribute))
            getattr(widget, attribute)(self._format(rule))

    from gui.fragments.tools import ToolsFragment
    from module.tools.schale_inventory.ui import Layout as InventoryLayout
    # This tool normally saves relative to its source file, rather than cwd.
    InventoryLayout._state_path = lambda self: preview_root / "config" / "schale_inventory.json"
    # ConfigGui loads qconfig at import time, so select the initial theme after
    # that import and before creating any short-lived labels.
    setTheme(Theme.DARK if current_theme == "dark" else Theme.LIGHT)

    config = PreviewConfig()
    window = QWidget()
    window.setWindowTitle("BAAS · 工具界面离线预览")
    config.window = window
    root = QVBoxLayout(window)
    root.setContentsMargins(0, 0, 0, 0)
    fragment = ToolsFragment(config=config)
    root.addWidget(fragment)
    window.toolsInterface = fragment
    window.resize(*sizes[0])
    window.show()

    def settle(seconds=0.3):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            app.processEvents()
            time.sleep(0.005)

    def apply_theme(theme):
        nonlocal current_theme
        if theme != current_theme:
            setTheme(Theme.DARK if theme == "dark" else Theme.LIGHT)
            current_theme = theme
        palette = window.palette()
        palette.setColor(QPalette.Window, QColor("#202020" if theme == "dark" else "#f5f7fa"))
        window.setPalette(palette)
        window.setAutoFillBackground(True)
        settle()

    apply_theme("dark" if args.theme == "dark" else "light")
    if not screenshot_dir:
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QShortcut

        window.setWindowTitle("BAAS · 工具界面离线预览 · F6 切换浅深色")
        window._theme_shortcut = QShortcut(QKeySequence("F6"), window)
        window._theme_shortcut.activated.connect(
            lambda: apply_theme("light" if current_theme == "dark" else "dark")
        )
        if args.tool != "hall":
            fragment.open_tool(args.tool)
        settle()
        if args.show_settings and not fragment.btn_settings.isHidden():
            fragment.btn_settings.click()
            settle()
        if args.scroll_bottom:
            from PyQt5.QtWidgets import QScrollArea

            for scroll in fragment.stack.currentWidget().findChildren(QScrollArea):
                if scroll.isVisible():
                    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        return app.exec_()

    report = {"source_root": str(source_root), "captures": [], "registry_errors": tools.errors,
              "callback_errors": callback_errors}
    themes = ("light", "dark") if args.theme == "both" else (args.theme,)
    pages = ["hall"] + [tool.id for tool in tools.list_lobby_tools()]
    if args.include_edit:
        pages.append("hall-edit")
    for theme in (() if args.smoke_only else themes):
        apply_theme(theme)
        for width, height in sizes:
            window.resize(width, height)
            settle()
            for page in pages:
                if page.startswith("hall"):
                    fragment.show_hall()
                    if page == "hall-edit":
                        fragment._enter_edit_mode()
                else:
                    fragment.open_tool(page)
                settle(0.5)
                path = screenshot_dir / f"{page}-{theme}-{width}x{height}.png"
                window.grab().save(str(path))
                errors = [label.text() for label in fragment.stack.currentWidget().findChildren(QLabel)
                          if any(word in label.text() for word in ("加载失败", "初始化失败", "未能载入", "打开失败"))]
                capture = {"page": page, "theme": theme, "requested_size": [width, height],
                           "actual_size": [window.width(), window.height()],
                           "size_matches": (window.width(), window.height()) == (width, height),
                           "path": str(path), "errors": errors}
                report["captures"].append(capture)
                print(json.dumps(capture, ensure_ascii=False), flush=True)
                if page == "hall-edit":
                    fragment._exit_edit_mode()
    if args.smoke_actions or args.smoke_only:
        from datetime import datetime, timedelta
        from PyQt5.QtTest import QTest
        from PyQt5.QtCore import QPoint, QCoreApplication, QEvent
        from PyQt5.QtWidgets import QScrollArea, QTabWidget
        from qfluentwidgets import isDarkTheme
        from gui.fragments.tools import ToolCard
        from module.tools.assets_display.ui import Layout as AssetsLayout
        from module.tools.equip_farm.ui import Layout as EquipLayout
        from gui.components.expand.hoardApConfig import Layout as HoardLayout

        smoke = report["smoke_actions"] = []

        def check(name, passed, detail=""):
            smoke.append({"name": name, "passed": bool(passed), "detail": detail})
            print(json.dumps(smoke[-1], ensure_ascii=False), flush=True)

        def capture_state(name, bottom=False):
            if bottom:
                for scroll in fragment.stack.currentWidget().findChildren(QScrollArea):
                    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
            settle()
            path = screenshot_dir / f"smoke-{name}.png"
            window.grab().save(str(path))
            report.setdefault("action_screenshots", []).append(str(path))

        def first_card():
            return next(fragment.cards_grid.itemAt(index).widget()
                        for index in range(fragment.cards_grid.count())
                        if isinstance(fragment.cards_grid.itemAt(index).widget(), ToolCard))

        window.resize(1200, 800)
        fragment.show_hall()
        settle()
        for theme in ("light", "dark", "light"):
            apply_theme(theme)
            check(f"theme-{theme}", isDarkTheme() == (theme == "dark"))
        capture_state("hall-theme-roundtrip")

        fragment.btn_tool_edit.click()
        settle()
        card = first_card()
        original_title = card.t.text()
        card.name_edit.setText("离线界面验证")
        card.tags_edit.setText("布局,预览")
        card.cb.setChecked(False)
        window.resize(760, 700)
        settle()
        card_after_resize = first_card()
        check("manage-inputs-survive-resize",
              card_after_resize.name_edit.text() == "离线界面验证"
              and card_after_resize.tags_edit.text() == "布局,预览"
              and not card_after_resize.cb.isChecked())
        capture_state("manage-resized")
        fragment.btn_tool_cancel.click()
        settle()
        check("manage-cancel", not getattr(fragment, "_edit_mode", False)
              and first_card().t.text() == original_title)
        fragment.btn_tool_edit.click()
        settle()
        check("manage-reenter-clean", first_card().name_edit.text() == original_title
              and first_card().cb.isChecked())
        fragment.btn_tool_cancel.click()
        settle()

        card = first_card()
        tool_id = card.tool_id
        QTest.mouseClick(card, Qt.LeftButton)
        settle()
        check("card-opens-tool", fragment._current_tool == tool_id)
        QTest.keyClick(fragment, Qt.Key_Escape)
        settle()
        check("escape-returns-hall", fragment._current_tool is None
              and fragment.stack.currentWidget() is fragment.hall)
        fragment.open_tool(tool_id)
        fragment.btn_back.click()
        settle()
        check("back-returns-hall", fragment.stack.currentWidget() is fragment.hall)

        fragment.open_tool("schale_inventory")
        settle()
        check("display-settings-collapsed", not fragment.settings_scroll.isVisible())
        fragment.btn_settings.click()
        settle()
        check("display-settings-expand", fragment.settings_scroll.isVisible())
        capture_state("display-settings-expanded")
        settings_count = sum(fragment.settings_lay.itemAt(index).widget() is not None
                             for index in range(fragment.settings_lay.count()))
        fragment.show_hall()
        fragment.open_tool("schale_inventory")
        settle()
        reentered_count = sum(fragment.settings_lay.itemAt(index).widget() is not None
                              for index in range(fragment.settings_lay.count()))
        check("display-settings-survive-reentry", settings_count == reentered_count and settings_count >= 2)
        fragment.btn_settings.click()
        settle()
        check("display-settings-collapse", not fragment.settings_scroll.isVisible())

        for tid in ("hoard_ap", "equip_farm", "auto_push", "assets_display", "schale_inventory"):
            fragment.open_tool(tid)
            settle()
            before_count = sum(fragment.settings_lay.itemAt(i).widget() is not None
                               for i in range(fragment.settings_lay.count()))
            fragment.show_hall()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            fragment.open_tool(tid)
            settle()
            after_count = sum(fragment.settings_lay.itemAt(i).widget() is not None
                              for i in range(fragment.settings_lay.count()))
            check(f"{tid}-settings-reentry", before_count == after_count and after_count > 0)

        inventory = fragment.stack.currentWidget().findChild(InventoryLayout)
        inventory._items[0][0].setValue(2)
        inventory._items[0][1].setValue(1)
        settle()
        QTest.mouseClick(inventory._place_buttons[0], Qt.LeftButton)
        origin = QPoint(inventory._board.cell_size // 2, inventory._board.cell_size // 2)
        QTest.mouseClick(inventory._board, Qt.LeftButton, pos=origin)
        settle()
        check("inventory-place-item", len(inventory._placed) == 1)
        QTest.mouseClick(inventory._board, Qt.LeftButton, pos=origin)
        settle()
        check("inventory-rotate-item", len(inventory._placed) == 1 and inventory._placed[0].rotated)
        capture_state("inventory-item-placed")
        QTest.mouseClick(inventory._board, Qt.RightButton, pos=origin)
        settle()
        check("inventory-remove-item", not inventory._placed)

        window.resize(1200, 800)
        fragment.open_tool("assets_display")
        settle()
        assets = fragment.stack.currentWidget().findChild(AssetsLayout)
        original_assets = config.get("assetsVisibility")
        assets.sw_assets.setChecked(not original_assets)
        settle()
        check("asset-toggle-writes-demo-config", config.get("assetsVisibility") == (not original_assets)
              and config.get("tool_assets_enabled") == (not original_assets))
        assets.sw_assets.setChecked(original_assets)

        fragment.open_tool("equip_farm")
        settle()
        equip = fragment.stack.currentWidget().findChild(EquipLayout)
        for button, mode in ((equip.btn_simple, "simple"), (equip.btn_complex, "complex"), (equip.btn_stone, "stone")):
            QTest.mouseClick(button, Qt.LeftButton)
            settle()
            check(f"equip-mode-{mode}", equip._mode == mode)
            if mode == "simple":
                next(iter(equip._slot_edits.values())).setText("9,8")
            elif mode == "stone":
                equip.ed_stone_spec.setPlainText("星野,3-5,20;白子,2-3,5")
            equip.btn_calc.click()
            settle()
            output = equip.out_stone if mode == "stone" else equip.out_equip
            check(f"equip-result-{mode}", bool(output.toPlainText().strip()), output.toPlainText()[:120])
            capture_state(f"equip-{mode}-top")
            capture_state(f"equip-{mode}-bottom", bottom=True)
        apply_theme("dark")
        capture_state("equip-stone-dark-bottom", bottom=True)
        apply_theme("light")

        fragment.open_tool("hoard_ap")
        settle()
        hoard = fragment.stack.currentWidget().findChild(HoardLayout)
        fragment.btn_settings.click()
        for theme in ("light", "dark"):
            apply_theme(theme)
            for width, height in ((1200, 800), (760, 700)):
                window.resize(width, height)
                settle()
                capture_state(f"purchase-settings-{theme}-{width}x{height}", bottom=True)
        fragment.btn_settings.click()
        apply_theme("light")
        window.resize(1200, 800)
        settle()
        hoard.edit_current_ap.setText("160")
        hoard.edit_cafe_claimable.setText("320")
        hoard.edit_mail_detail.setPlainText("120@d6,60@d5")
        hoard.edit_date.setText((datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"))
        hoard.sw_enabled.setChecked(True)
        hoard.btn_calc.click()
        settle()
        plan = hoard.txt_plan.toPlainText()
        check("hoard-plan-local-calculation", len(plan) > 120 and "Traceback" not in plan,
              plan[:160])
        capture_state("hoard-plan-top")
        capture_state("hoard-plan-bottom", bottom=True)
        apply_theme("dark")
        capture_state("hoard-plan-dark-bottom", bottom=True)
        apply_theme("light")
        hoard.sw_enabled.setChecked(False)

        fragment.open_tool("auto_push")
        settle()
        capture_state("auto-push-bottom", bottom=True)
        for tool_id in ("hoard_ap", "equip_farm", "auto_push"):
            fragment.open_tool(tool_id)
            settle()
            for workspace in fragment.stack.currentWidget().findChildren(QTabWidget):
                if not workspace.isVisible():
                    continue
                for index in range(workspace.count()):
                    workspace.setCurrentIndex(index)
                    settle()
                    capture_state(f"{tool_id}-workspace-{index}")
                check(f"{tool_id}-workspace-tabs", workspace.count() >= 2)
        fragment.show_hall()
        settle()
        check("final-hall-navigation", fragment.stack.currentWidget() is fragment.hall)
        check("no-qt-callback-errors", not callback_errors, "; ".join(callback_errors))
    (screenshot_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    window.close()
    app.processEvents()
    failed_actions = any(not item["passed"] for item in report.get("smoke_actions", []))
    return 1 if (report["registry_errors"] or callback_errors or failed_actions
                 or any(item["errors"] or not item["size_matches"] for item in report["captures"])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
