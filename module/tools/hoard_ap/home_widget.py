# -*- coding: utf-8 -*-
"""主页囤体区：
- 主页显示开 → 「进入囤体」按钮（点进工具大厅囤体页）
- 拦截显示开 → 四快捷开关（写 prefer_clear，并给到点清体对应项填 -1）
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter
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
    from qfluentwidgets import SwitchButton, IndicatorPosition, PrimaryPushButton, PushButton
except Exception:  # pragma: no cover
    SwitchButton = None  # type: ignore
    IndicatorPosition = None  # type: ignore
    try:
        from PyQt5.QtWidgets import QPushButton as PrimaryPushButton, QPushButton as PushButton
    except Exception:
        PrimaryPushButton = None  # type: ignore
        PushButton = None  # type: ignore

try:
    from gui.components.expand.tool_style import (
        apply_theme_to_labels,
        connect_theme_refresh,
        safe_connect_theme,
        themed_section_body_bg,
        themed_text,
    )
except Exception:  # pragma: no cover
    apply_theme_to_labels = connect_theme_refresh = None
    safe_connect_theme = None
    themed_section_body_bg = lambda: "#FFFFFF"
    themed_text = lambda: "#333333"


SWITCH_TO_DEST = {
    "normal": "mainline",
    "hard": "mainline",
    "mainline": "mainline",  # 旧兼容
    "special": "special",
    "high_value": "activity",
}


def _norm_prefer(mode: str) -> str:
    m = (mode or "").strip().lower()
    if m == "mainline":
        return "normal"
    if m in ("normal", "hard", "special", "high_value"):
        return m
    return ""


from module.tools.base import _cfg_bool


class PreferClearHomeWidget(QFrame):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("preferClearBox")
        # 一行横排：进入囤体按钮 + 四快捷开关（紧凑，不撑出右侧空白）
        root = QHBoxLayout(self)
        root.setContentsMargins(2, 4, 2, 4)  # 盒间隔=2+槽位6+2=10，与盒内 10px 一致
        root.setSpacing(10)

        self.btn_enter = None
        if PrimaryPushButton is not None or PushButton is not None:
            Btn = PrimaryPushButton or PushButton
            self.btn_enter = Btn("进入囤体", self)
            try:
                self.btn_enter.setToolTip("打开工具里的囤体页")
            except Exception:
                pass
            self.btn_enter.clicked.connect(self._open_hoard)
            root.addWidget(self.btn_enter, 0, Qt.AlignVCenter)

        # 四快捷（紧挨按钮右侧）
        self.sw_row_host = QWidget(self)
        lay = QHBoxLayout(self.sw_row_host)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self._prefer_switches = {}
        self._prefer_cells = {}

        for title, key in (
            ("普通多倍", "normal"),
            ("困难多倍", "hard"),
            ("特别委托3倍", "special"),
            ("高价值活动", "high_value"),
        ):
            cell, sw = self._mk_cell(title, key)
            self._prefer_switches[key] = sw
            self._prefer_cells[key] = cell
            lay.addWidget(cell, 0, Qt.AlignVCenter)
        root.addWidget(self.sw_row_host)

        try:
            self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        except Exception:
            pass

        self._apply_visibility()
        self._load()
        for k, sw in self._prefer_switches.items():
            try:
                sw.checkedChanged.connect(
                    lambda checked, mode=k: self._on_toggled(mode, checked)
                )
            except Exception:
                pass

        # 深色模式适配
        if apply_theme_to_labels is not None:
            apply_theme_to_labels(self)
        # safe_connect_theme 已含 sip.isdeleted 兜底，可安全连 cell 背景/文字刷新
        # （原先只连 connect_theme_refresh 刷 QLabel 文字，cell 背景不重算 → 深切浅仍深色）
        if safe_connect_theme is not None:
            safe_connect_theme(self, self._refresh_theme)

    def _refresh_theme(self):
        """切主题后重算拦截格背景 + 刷新文字色（深/浅双向）。"""
        try:
            if apply_theme_to_labels is not None:
                apply_theme_to_labels(self)
            mode = _norm_prefer(str(self._get("hoard_ap_prefer_clear", "") or ""))
            self._style(mode)
        except Exception:
            pass

    def _mk_cell(self, title: str, key: str):
        cell = QFrame(self)
        cell.setObjectName("preferClearCell")
        cell.setAttribute(Qt.WA_StyledBackground, True)
        cell._prefer_on = False  # 选中态：on 蓝 2px / off 淡灰 2px（QSS border 现算）
        # 边框由统一 prefer_cell_qss 现算（与顶栏开关格同一套），QSS 画框可靠
        try:
            from gui.components.expand.tool_style import prefer_cell_qss, attach_prefer_cell_refresh
            cell.setStyleSheet(prefer_cell_qss(False))
            attach_prefer_cell_refresh(cell)
        except Exception:
            cell.setStyleSheet(
                "QFrame#preferClearCell{border:2px solid transparent;border-radius:8px;"
                "background:%s;}" % themed_section_body_bg()
            )
        vl = QVBoxLayout(cell)
        # 与顶栏设置开关同一套：上下对称，高 52
        vl.setContentsMargins(10, 6, 10, 6)
        vl.setSpacing(2)
        lab = QLabel(title, cell)
        lab.setAlignment(Qt.AlignHCenter)
        lab.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:600;'
            f"color:{themed_text()};"
        )
        if SwitchButton is not None and IndicatorPosition is not None:
            sw = SwitchButton(cell, IndicatorPosition.RIGHT)
        else:
            sw = SwitchButton(cell) if SwitchButton else QLabel("—", cell)
        try:
            sw.setOnText("开")
            sw.setOffText("关")
        except Exception:
            pass
        try:
            sw.setToolTip("激活后拦截其它花体；并给「到点清体力」对应项填 -1")
        except Exception:
            pass
        vl.addWidget(lab, 0, Qt.AlignHCenter)
        vl.addWidget(sw, 0, Qt.AlignHCenter)
        cell.setMinimumWidth(104)
        cell.setFixedHeight(52)
        return cell, sw

    def _get(self, key, default=""):
        c = self.config
        try:
            if hasattr(c, "get"):
                return c.get(key, default)
            return getattr(c, key, default)
        except Exception:
            return default

    def _set(self, key, value):
        c = self.config
        try:
            if hasattr(c, "set"):
                c.set(key, value)
                return
            setattr(c, key, value)
        except Exception as e:
            # 配置没写进去=开关界面态与真实态脱节，必须留痕
            print("[hoard_ap] 主页格子配置写入失败:", key, e)

    def _apply_visibility(self) -> None:
        show_entry = _cfg_bool(self.config, "hoard_ap_home_entry", True)
        show_sw = _cfg_bool(self.config, "hoard_ap_home_intercept_visible", True)
        try:
            if self.btn_enter is not None:
                self.btn_enter.setVisible(show_entry)
        except Exception:
            pass
        try:
            self.sw_row_host.setVisible(show_sw)
        except Exception:
            pass
        # 全关时隐藏自己
        try:
            self.setVisible(bool(show_entry or show_sw))
        except Exception:
            pass

    def _load(self) -> None:
        mode = _norm_prefer(str(self._get("hoard_ap_prefer_clear", "") or ""))
        for k, sw in self._prefer_switches.items():
            try:
                sw.blockSignals(True)
                sw.setChecked(k == mode)
            finally:
                try:
                    sw.blockSignals(False)
                except Exception:
                    pass
        self._style(mode)

    def _style(self, mode: str = "") -> None:
        mode = _norm_prefer(mode)
        # 边框由统一 prefer_cell_qss 现算（on 蓝 2px / off 淡灰 2px），
        # 与顶栏开关格同一套；选中态设 _prefer_on 后 QSS 自动画蓝框。
        try:
            from gui.components.expand.tool_style import prefer_cell_qss
        except Exception:
            prefer_cell_qss = None
        for k, cell in self._prefer_cells.items():
            try:
                is_on = (k == mode)
                cell._prefer_on = is_on  # type: ignore[attr-defined]
                if prefer_cell_qss is not None:
                    cell.setStyleSheet(prefer_cell_qss(is_on))
                cell.update()
            except Exception:
                pass

    def _fill_spend_neg_one(self, mode: str) -> None:
        """到点清体力：对应项填 -1（不碰绿框、不改多自回）。"""
        mode = _norm_prefer(mode)
        if mode == "normal":
            if not str(self._get("hoard_ap_spend_main_normal", "") or "").strip():
                self._set("hoard_ap_spend_main_normal", "1-1--1")
        elif mode == "hard":
            if not str(self._get("hoard_ap_spend_main_hard", "") or "").strip():
                self._set("hoard_ap_spend_main_hard", "h1-1--1")
        elif mode == "special":
            self._set("hoard_ap_spend_special_exp", "-1")
            self._set("hoard_ap_spend_special_money", "-1")
        elif mode == "high_value":
            self._set("hoard_ap_spend_activity_times", "-1")

    def _on_toggled(self, mode: str, checked: bool) -> None:
        mode = _norm_prefer(mode)
        if checked:
            for k, sw in self._prefer_switches.items():
                if k == mode:
                    continue
                try:
                    sw.blockSignals(True)
                    sw.setChecked(False)
                finally:
                    try:
                        sw.blockSignals(False)
                    except Exception:
                        pass
            val = mode
            self._fill_spend_neg_one(mode)
        else:
            cur = _norm_prefer(str(self._get("hoard_ap_prefer_clear", "") or ""))
            val = "" if cur == mode else cur
        self._set("hoard_ap_prefer_clear", val)
        # 兼容旧 clear_mode（拦截仍读 prefer_clear）
        if val in ("normal", "hard"):
            self._set("hoard_ap_clear_mode", "mainline")
            self._set("hoard_ap_clear_modes", "mainline")
        elif val == "special":
            self._set("hoard_ap_clear_mode", "special")
            self._set("hoard_ap_clear_modes", "special")
        elif val == "high_value":
            self._set("hoard_ap_clear_mode", "activity")
            self._set("hoard_ap_clear_modes", "activity")
        self._style(val)

    def _open_hoard(self) -> None:
        # 找 HomeFragment.open_tool
        p = self.parent()
        while p is not None:
            if hasattr(p, "open_tool"):
                try:
                    p.open_tool("hoard_ap")
                    return
                except Exception:
                    pass
            try:
                p = p.parent()
            except Exception:
                break
        # config.window
        try:
            c = self.config
            win = c.get_window() if hasattr(c, "get_window") else None
            if win is not None and hasattr(win, "open_tool_page"):
                win.open_tool_page("hoard_ap", config=c)
        except Exception:
            pass
