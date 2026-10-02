# -*- coding: utf-8 -*-
"""主页编辑：与其它工具同一套大框样式。

顶栏两个开关：资产主页显示 / 编辑主页显示
内容区：是否显示资产条 + 去主页调顺序
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)

try:
    from qfluentwidgets import SwitchButton, PrimaryPushButton, PushButton
except Exception:  # pragma: no cover
    SwitchButton = None  # type: ignore
    try:
        from PyQt5.QtWidgets import QPushButton as PrimaryPushButton, QPushButton as PushButton
    except Exception:
        PrimaryPushButton = None  # type: ignore
        PushButton = None  # type: ignore

from gui.components.expand.tool_style import (
    set_style_dedup,
    TipLabel,
    apply_full_theme_refresh,
    safe_connect_theme,
    header_switch_css,
    themed_switch_note_bg,
    themed_text,
    themed_title_text,
)
from module.tools.base import _cfg_bool, _cfg_set


_TipLabel = TipLabel  # 从 tool_style 统一提取,主题感知(深色白字黑描边)


# 开关格常量与 QSS 工厂见 tool_style；运行时由 attach/header_switch_css 现算，
# 不留模块级浅色快照（历史遗留的 HEADER_SWITCH_OFF/ON_CSS 快照已删）。
def _switch_note_css() -> str:
    from gui.components.expand.tool_style import themed_note_border

    return (
        "QFrame#homeEditNote{"
        f"border:1px solid {themed_note_border()};border-radius:8px;"
        f"background:{themed_switch_note_bg()};}}"
    )


def _home_sec_css() -> str:
    """大框(标题栏+内容)：主题引擎统一工厂，不再自造。"""
    from gui.components.expand.tool_style import themed_section_css

    return themed_section_css("homeEditSec", "homeEditSecHead", "homeEditSecBody")


# 兼容旧引用(浅色快照);运行时请调函数
SWITCH_NOTE_CSS = _switch_note_css()


def _cfg_raw(config, key, default=None):
    """优先读 dataclass/挂载字段，避免翻译层或 get 缺省干扰。"""
    try:
        if config is None:
            return default
        inner = getattr(config, "config", None)
        if inner is not None and hasattr(inner, key):
            return getattr(inner, key)
        if hasattr(config, key) and key not in ("config", "get", "set", "save"):
            try:
                return getattr(config, key)
            except Exception:
                pass
        if hasattr(config, "get"):
            return config.get(key, default)
    except Exception:
        pass
    return default


def _home_fragments(config):
    out = []
    try:
        win = config.get_window() if config is not None and hasattr(config, "get_window") else None
        if win is None:
            return out
        for h in getattr(win, "_sub_list", [[]])[0]:
            if getattr(h, "config", None) is not config:
                continue
            out.append(h)
    except Exception as e:
        print("[home-edit] find home failed:", e)
    return out


def _refresh_home_plugins(config) -> None:
    for h in _home_fragments(config):
        try:
            if hasattr(h, "refresh_home_plugins"):
                h.refresh_home_plugins()
        except Exception as e:
            print("[home-edit] refresh plugins failed:", e)


def _sync_edit_entry(config, on: bool) -> None:
    for h in _home_fragments(config):
        try:
            if hasattr(h, "set_home_edit_entry_visible"):
                h.set_home_edit_entry_visible(bool(on))
            elif hasattr(h, "_sync_home_edit_entry_btn"):
                h._cfg_set("tool_assets_home_edit_entry", bool(on))
                h._sync_home_edit_entry_btn()
        except Exception as e:
            print("[home-edit] sync entry btn failed:", e)


def _goto_home_and_edit(config) -> None:
    _cfg_set(config, "tool_assets_home_edit", True)
    homes = _home_fragments(config)
    win = None
    try:
        win = config.get_window() if config is not None and hasattr(config, "get_window") else None
    except Exception:
        win = None
    try:
        if win is not None and hasattr(win, "onNavigationChanged"):
            win.onNavigationChanged(0)
        elif win is not None and hasattr(win, "dispatchSubView"):
            col = 0
            for i, h in enumerate(getattr(win, "_sub_list", [[]])[0]):
                if getattr(h, "config", None) is config:
                    col = i
                    break
            try:
                for ind, btn in enumerate(getattr(win, "navi_btn_list", []) or []):
                    btn.setSelected(ind == 0)
            except Exception:
                pass
            win._nav_index = 0
            win.dispatchSubView(0, col)
    except Exception as e:
        print("[home-edit] goto home failed:", e)
    for h in homes or _home_fragments(config):
        try:
            if hasattr(h, "enter_home_edit_mode"):
                h.enter_home_edit_mode()
            elif hasattr(h, "set_home_edit_mode"):
                h.set_home_edit_mode(True)
        except Exception as e:
            print("[home-edit] enter edit failed:", e)


def _mk_switch_cell(parent, title: str, checked: bool, on_change):
    """开关类：白底小框，上字下开关。"""
    cell = QFrame(parent)
    cell.setObjectName("homeEditNote")
    cell.setStyleSheet(_switch_note_css())
    vl = QVBoxLayout(cell)
    vl.setContentsMargins(14, 8, 14, 10)
    vl.setSpacing(8)
    vl.setAlignment(Qt.AlignHCenter)
    lab = QLabel(title, cell)
    lab.setObjectName("homeEditNoteTitle")
    lab.setAlignment(Qt.AlignHCenter)
    lab.setStyleSheet(
        'QLabel#homeEditNoteTitle{font-family:"Microsoft YaHei";'
        f"font-size:13px;font-weight:900;color:{themed_title_text()};}}"
    )
    try:
        f = lab.font()
        f.setBold(True)
        f.setWeight(QFont.Black)
        f.setPixelSize(13)
        lab.setFont(f)
    except Exception:
        pass
    vl.addWidget(lab, 0, Qt.AlignHCenter)
    sw = SwitchButton(cell) if SwitchButton else None
    if sw is not None:
        try:
            sw.setOnText("开")
            sw.setOffText("关")
        except Exception:
            pass
        try:
            sw.setMinimumWidth(72)
            sw.setMaximumWidth(96)
        except Exception:
            pass
        sw.setChecked(bool(checked))
        sw.checkedChanged.connect(on_change)
        vl.addWidget(sw, 0, Qt.AlignHCenter)
    cell.setMinimumWidth(140)
    return cell, sw


def _mk_section(parent, title: str, tip: str = "") -> tuple:
    """蓝标题栏 + 指定内容底，与囤体/装备同构。"""
    sec = QFrame(parent)
    sec.setObjectName("homeEditSec")
    sec.setStyleSheet(_home_sec_css())
    sec.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
    root = QVBoxLayout(sec)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    head = QFrame(sec)
    head.setObjectName("homeEditSecHead")
    hl = QHBoxLayout(head)
    hl.setContentsMargins(14, 8, 14, 8)
    hl.setSpacing(10)
    # 标题文字：近黑粗体 + 白描边（与说明文字同款画法，大一号）
    lab = _TipLabel(title, head, pixel_size=16, word_wrap=False)
    hl.addWidget(lab, 0)
    if tip:
        t = _TipLabel(tip, head)
        hl.addWidget(t, 1)
    else:
        hl.addStretch(1)
    root.addWidget(head)

    body = QFrame(sec)
    body.setObjectName("homeEditSecBody")
    bl = QVBoxLayout(body)
    bl.setContentsMargins(14, 10, 14, 12)
    bl.setSpacing(10)
    root.addWidget(body)
    return sec, bl


class Layout(QWidget):
    """主页编辑工具页。"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("homeEditLayout")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(12)
        root.setAlignment(Qt.AlignTop)

        # 单个大框（与其它工具同构）
        sec, body = _mk_section(
            self,
            "主页编辑",
            "顶栏管入口显隐；内容直接开关资产条或去主页调顺序（应用保存，离开取消）。",
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        # 以 assetsVisibility 为主；tool_assets_enabled 同步
        if _cfg_raw(config, "assetsVisibility", None) is not None:
            assets_on = _cfg_bool(config, "assetsVisibility", True)
        else:
            assets_on = _cfg_bool(config, "tool_assets_enabled", True)
        self.cell_assets, self.sw_assets = _mk_switch_cell(
            sec, "是否显示资产条", assets_on, self._on_assets_toggle
        )
        row.addWidget(self.cell_assets, 0, Qt.AlignTop)

        # 去主页调顺序：主按钮，不包小框
        self.btn_goto_edit = None
        if PrimaryPushButton is not None:
            self.btn_goto_edit = PrimaryPushButton("去主页调顺序", sec)
        elif PushButton is not None:
            self.btn_goto_edit = PushButton("去主页调顺序", sec)
        if self.btn_goto_edit is not None:
            try:
                self.btn_goto_edit.setMinimumWidth(132)
                self.btn_goto_edit.setFixedHeight(36)
            except Exception:
                pass
            self.btn_goto_edit.clicked.connect(self._on_goto_edit)
            row.addWidget(self.btn_goto_edit, 0, Qt.AlignBottom)

        row.addStretch(1)
        body.addLayout(row)
        root.addWidget(sec, 0, Qt.AlignTop)
        root.addStretch(1)

        # 打开本页清掉残留编辑态；同步入口（不覆盖用户已保存的 False）
        try:
            if _cfg_bool(config, "tool_assets_home_edit", False):
                _cfg_set(config, "tool_assets_home_edit", False)
                for h in _home_fragments(config):
                    if hasattr(h, "set_home_edit_mode"):
                        h.set_home_edit_mode(False)
            # 仅当键从未出现时才写默认开；已有 False 绝不改回 True
            raw_sw = _cfg_raw(config, "tool_assets_home_switch_entry", None)
            if raw_sw is None:
                _cfg_set(config, "tool_assets_home_switch_entry", True)
            entry_assets = _cfg_bool(config, "tool_assets_home_switch_entry", True)
            entry_edit = _cfg_bool(config, "tool_assets_home_edit_entry", False)
            _sync_edit_entry(config, entry_edit)
            self._sync_home_assets_switch_entry(entry_assets)
            _refresh_home_plugins(config)
        except Exception:
            pass

        # 深色模式适配
        if apply_full_theme_refresh is not None:
            apply_full_theme_refresh(self)
            # 主题统一由工具页容器（ToolsFragment connect_theme_refresh_full）遍历刷新；
            # 页面根不再重复注册/连接，避免一次切换多重遍历造成卡顿。

        # 大框/开关格 CSS 主题刷新(标题栏+内容底)
        try:
            from gui.util.config_gui import configGui

            if configGui is not None:
                def _refresh_secs(*_):
                    try:
                        for w in self.findChildren(QFrame):
                            try:
                                n = w.objectName()
                                if n == "homeEditSec":
                                    set_style_dedup(w, _home_sec_css())
                                elif n == "homeEditNote":
                                    set_style_dedup(w, _switch_note_css())
                                elif n == "homeEditHeaderCell":
                                    _off, _on = header_switch_css("homeEditHeaderCell")
                                    _sw = w.findChild(SwitchButton) if SwitchButton else None
                                    set_style_dedup(w, _on if (_sw and _sw.isChecked()) else _off)
                            except Exception:
                                pass
                    except Exception:
                        pass

                safe_connect_theme(self, _refresh_secs)
        except Exception:
            pass

    def header_settings_widgets(self):
        """顶栏：资产主页显示 / 编辑主页显示（控制主页入口是否出现）。

        构建一次后复用同一 host：ToolsFragment 每次打开工具页都会重挂顶栏，
        每次重建控件会产生可见「闪动」，且与其它工具页（构建一次复用）不一致。
        """
        host = getattr(self, "_header_host", None)
        if host is not None:
            return [host]
        host = QWidget()
        hl = QHBoxLayout(host)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)

        def _mini(title, checked, cb):
            # 四页统一实现（tool_style.make_header_setting_cell）
            from gui.components.expand.tool_style import make_header_setting_cell

            sw = SwitchButton(host) if SwitchButton else None
            if sw is not None:
                try:
                    sw.setOnText("开")
                    sw.setOffText("关")
                except Exception:
                    pass
                sw.setChecked(bool(checked))
                sw.checkedChanged.connect(cb)
            cell = make_header_setting_cell(title, sw, obj_name="homeEditHeaderCell")
            return cell, sw

        entry_assets = _cfg_bool(self.config, "tool_assets_home_switch_entry", True)
        entry_edit = _cfg_bool(self.config, "tool_assets_home_edit_entry", False)
        c1, self._header_sw_entry_assets = _mini(
            "资产主页显示", entry_assets, self._on_entry_assets_toggle
        )
        hl.addWidget(c1, 0, Qt.AlignVCenter)
        c2, self._header_sw_entry_edit = _mini(
            "编辑主页显示", entry_edit, self._on_entry_edit_toggle
        )
        hl.addWidget(c2, 0, Qt.AlignVCenter)
        # 主页栏位单选（第一栏=标题下 / 第二栏=启停下），靠开关右侧
        try:
            from gui.components.expand.tool_style import make_home_bar_slot_cell
            _slot = make_home_bar_slot_cell("assets_display")
            if _slot is not None:
                hl.addWidget(_slot, 0, Qt.AlignVCenter)
        except Exception:
            pass
        self._header_host = host
        return [host]

    def _sync_sw(self, sw, checked: bool):
        if sw is None:
            return
        try:
            if sw.isChecked() != bool(checked):
                sw.blockSignals(True)
                sw.setChecked(bool(checked))
                sw.blockSignals(False)
        except Exception:
            pass

    def _sync_home_assets_switch_entry(self, on: bool) -> None:
        for h in _home_fragments(self.config):
            try:
                if hasattr(h, "set_home_assets_switch_entry_visible"):
                    h.set_home_assets_switch_entry_visible(bool(on))
                else:
                    host = getattr(h, "_startup_home_host", None)
                    if host is not None:
                        host.setVisible(bool(on))
            except Exception as e:
                print("[home-edit] sync assets switch entry failed:", e)

    def _persist_entry_flag(self, key: str, checked: bool) -> None:
        """顶栏入口开关：强制写入底层字段并 save，与囤体拦截同一套。"""
        checked = bool(checked)
        c = self.config
        _cfg_set(c, key, checked)
        try:
            inner = getattr(c, "config", None) if c is not None else None
            if inner is not None:
                setattr(inner, key, checked)
            elif c is not None:
                setattr(c, key, checked)
            if c is not None and hasattr(c, "save"):
                c.save()
        except Exception as e:
            print("[home-edit] persist failed:", key, e)

    def _on_entry_assets_toggle(self, checked: bool):
        checked = bool(checked)
        self._persist_entry_flag("tool_assets_home_switch_entry", checked)
        self._sync_sw(getattr(self, "_header_sw_entry_assets", None), checked)
        self._sync_home_assets_switch_entry(checked)

    def _on_entry_edit_toggle(self, checked: bool):
        checked = bool(checked)
        self._persist_entry_flag("tool_assets_home_edit_entry", checked)
        self._sync_sw(getattr(self, "_header_sw_entry_edit", None), checked)
        _sync_edit_entry(self.config, checked)

    def _on_assets_toggle(self, checked: bool):
        checked = bool(checked)
        c = self.config
        _cfg_set(c, "assetsVisibility", checked)
        _cfg_set(c, "tool_assets_enabled", checked)
        # 再保险：直接落底层字段 + save
        try:
            inner = getattr(c, "config", None) if c is not None else None
            if inner is not None:
                setattr(inner, "assetsVisibility", checked)
                setattr(inner, "tool_assets_enabled", checked)
            if c is not None and hasattr(c, "save"):
                c.save()
        except Exception as e:
            print("[assets_display] 资产开关兜底落盘失败:", e)
        self._sync_sw(getattr(self, "sw_assets", None), checked)
        for h in _home_fragments(c):
            try:
                sw = getattr(h, "sw_assets_home", None)
                if sw is not None:
                    self._sync_sw(sw, checked)
            except Exception:
                pass
        _refresh_home_plugins(c)

    def _on_goto_edit(self):
        _goto_home_and_edit(self.config)
