# -*- coding: utf-8 -*-
"""装备刷图：简单/复杂互切；神明文字独立。布局与配色对齐囤体。"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

try:
    from gui.components.expand.tool_style import (
        TipLabel,
        apply_full_theme_refresh,
    )
except Exception:  # pragma: no cover
    TipLabel = None  # type: ignore
    apply_full_theme_refresh = None

from PyQt5.QtCore import Qt, QEvent, QTimer, QObject, QPoint
from PyQt5.QtGui import QColor, QFont, QPainter, QTextDocument, QTextOption
from PyQt5.QtWidgets import (
    QApplication,
    QStyle,
    QStyleOption,
    QAbstractItemView,
    QAbstractScrollArea,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from qfluentwidgets import (
        LineEdit,
        PrimaryPushButton,
        PushButton,
        SwitchButton,
    )
except Exception:  # pragma: no cover
    from PyQt5.QtWidgets import QLineEdit as LineEdit
    from PyQt5.QtWidgets import QPushButton as PrimaryPushButton, QPushButton as PushButton

    class SwitchButton(QWidget):  # type: ignore
        def __init__(self, parent=None):
            super().__init__(parent)
            self._on = False
            from PyQt5.QtWidgets import QPushButton

            self._btn = QPushButton("关", self)
            self._btn.clicked.connect(self._toggle)
            lay = QHBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(self._btn)
            self.checkedChanged = self._btn.clicked

        def _toggle(self):
            self.setChecked(not self._on)

        def setOnText(self, t):
            self._on_t = t

        def setOffText(self, t):
            self._off_t = t

        def setChecked(self, v):
            self._on = bool(v)
            self._btn.setText(
                getattr(self, "_on_t", "开") if self._on else getattr(self, "_off_t", "关")
            )

        def isChecked(self):
            return self._on


try:
    from gui.components.expand.hoard_goods import ExclusiveCheckRow, MultiCheckRow
except Exception:  # pragma: no cover
    ExclusiveCheckRow = None  # type: ignore
    MultiCheckRow = None  # type: ignore

from module.tools.equip_farm.calculator import (
    SLOT_UI_ORDER,
    apply_tokens_to_hard_string,
    apply_tokens_to_mainline_string,
    equip_index,
    estimate_from_run_text,
    format_plan_text,
    load_stage_table,
    needs_from_simple,
    parse_run_spec,
    parse_tier_list,
    recommend_stages,
)
from module.tools.equip_farm.secretstone import (
    COST_HELP_CN,
    load_secretstone_table,
    match_students_smart,
    plan_many,
)

from gui.components.expand.tool_style import (
    GreenFrameOption,
    REM,
    themed_accent_text,
    themed_input_bg,
    themed_input_css,
    themed_note_bg,
    themed_note_border,
    themed_scrollbar_qss,
    themed_section_body_bg,
    themed_separator,
    themed_success_fill_rgba,
    themed_switch_note_bg,
    themed_text,
    themed_title_bar_qss,
    themed_title_text,
)

# 页底透明对齐工具大厅；大框=浅蓝标题 + 透明内容（=大厅四周）；小框浅青；输入纯白
# INPUT_BG/TOP_BG 原本地字面量已收敛到 tool_style（themed_input_bg/themed_top_bg）。
PAGE_BG = "transparent"
# 开关格 on/off QSS 由 tool_style.header_switch_css 运行时现算（attach 到格子），
# 不留模块级浅色快照（历史遗留的 HEADER_SWITCH_OFF/ON_CSS 已删）。

def _note_css() -> str:
    """小框(浅青底)主题感知 QSS。"""
    return (
        "QFrame#equipNote{"
        f"border:1px solid {themed_note_border()};"
        f"border-radius:8px;background:{themed_note_bg()};}}"
    )


def _note_switch_css() -> str:
    """开关格(白底)主题感知 QSS。"""
    return (
        "QFrame#equipNote{"
        f"border:1px solid {themed_note_border()};"
        f"border-radius:8px;background:{themed_switch_note_bg()};}}"
    )


def _section_css() -> str:
    """大框(标题栏+内容)：主题引擎统一工厂，不再自造。"""
    from gui.components.expand.tool_style import themed_section_css

    return themed_section_css("equipSection", "equipSectionHeader", "equipSectionBody")


# 全部样式运行时调主题引擎工厂，不留模块级快照（用户裁定）。
# 页底透明骨架也由引擎统一发放。
def _page_css() -> str:
    from gui.components.expand.tool_style import themed_page_transparent_qss

    return themed_page_transparent_qss("equipFarmLayout", "equipBody", "equipScroll")


def _top_css() -> str:
    """顶栏：主题引擎标题栏工厂统一发放。"""
    return themed_title_bar_qss("equipTop")


def _forward_wheel_to_outer(widget, event) -> bool:
    """把滚轮交给最近的外层 QScrollArea；绝不让多行框自己吃掉。"""
    try:
        delta = event.angleDelta().y()
        if delta == 0:
            delta = event.pixelDelta().y()
        if delta == 0:
            return False
        w = widget
        while w is not None:
            if isinstance(w, QScrollArea):
                bar = w.verticalScrollBar()
                if bar is not None and bar.maximum() > 0:
                    step = bar.singleStep() or 24
                    # 触控板像素 / 鼠标角度统一
                    if abs(delta) < 120:
                        bar.setValue(bar.value() - int(delta))
                    else:
                        bar.setValue(bar.value() - int(delta / 120.0 * step * 3))
                    return True
            w = w.parentWidget() if hasattr(w, "parentWidget") else w.parent()
    except Exception:
        return False
    return False


_TipLabel = TipLabel  # 从 tool_style 统一提取,主题感知(深色白字黑描边)


class AutoHeightText(QTextEdit):
    """多行：随内容长高；禁止内滚；滚轮/触控板一律交给外层页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        try:
            self.setAutoFormatting(QTextEdit.AutoNone)
        except Exception:
            pass
        self.setStyleSheet(themed_input_css())  # 引擎同源（含 QTextEdit 段）
        self.setMinimumHeight(48)
        try:
            self.setFocusPolicy(Qt.StrongFocus)
            self.setTabChangesFocus(True)
        except Exception:
            pass
        # Fluent / Qt 内部常把 wheel 打在 viewport 上，必须两边都拦
        try:
            self.viewport().installEventFilter(self)
            self.installEventFilter(self)
        except Exception:
            pass
        try:
            # 关掉自身滚动区域的滚轮处理
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sb = self.verticalScrollBar()
            if sb is not None:
                sb.setEnabled(False)
                sb.hide()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            if event is not None and event.type() == QEvent.Wheel:
                if _forward_wheel_to_outer(self, event):
                    event.accept()
                    return True
                event.ignore()
                return True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        if _forward_wheel_to_outer(self, event):
            event.accept()
            return
        event.ignore()

    def scrollContentsBy(self, dx, dy):
        # 禁止内部内容偏移，避免"看似能滚其实夹住"
        if dx:
            super().scrollContentsBy(dx, 0)


class _NoteCell(QFrame):
    """小框：上标题下控件（浅青底）；switch_box=True 为白底开关格。"""

    def _refresh(self):
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, _note_switch_css() if getattr(self, "_switch_box", False) else _note_css())
        except Exception:
            pass

    def __init__(self, title: str, parent=None, *, switch_box: bool = False):
        super().__init__(parent)
        self.setObjectName("equipNote")
        self._switch_box = switch_box
        self.setStyleSheet(_note_switch_css() if switch_box else _note_css())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(REM, 6, REM, 8)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.title = QLabel(title, self)
        self.title.setObjectName("equipNoteTitle")
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title.setStyleSheet(
            'QLabel#equipNoteTitle{font-family:"Microsoft YaHei";'
            f"font-size:13px;font-weight:900;color:{themed_title_text()};}}"
        )
        try:
            f = self.title.font()
            f.setFamily("Microsoft YaHei")
            f.setBold(True)
            f.setWeight(QFont.Black)
            f.setPixelSize(13)
            self.title.setFont(f)
        except Exception:
            pass
        lay.addWidget(self.title, 0, Qt.AlignLeft)
        self.slot = QVBoxLayout()
        self.slot.setContentsMargins(0, 0, 0, 0)
        self.slot.setSpacing(4)
        lay.addLayout(self.slot)

    def _refresh(self):
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, _note_switch_css() if self._switch_box else _note_css())
        except Exception:
            pass

    def set_widget(self, w: QWidget):
        while self.slot.count():
            it = self.slot.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
        self.slot.addWidget(w)
        return w


class _Section(QFrame):
    """大框：蓝色标题栏（标题+说明+右侧控件）+ 白色内容区。"""

    def _refresh(self):
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, _section_css())
        except Exception:
            pass

    def __init__(self, title: str, parent=None, tip: str = ""):
        super().__init__(parent)
        self.setObjectName("equipSection")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(_section_css())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop)

        # —— 标题栏 ——
        self.header = QFrame(self)
        self.header.setObjectName("equipSectionHeader")
        head = QHBoxLayout(self.header)
        head.setContentsMargins(REM * 2, 8, REM * 2, 8)
        head.setSpacing(10)
        # 标题文字：近黑粗体 + 白描边（与说明文字同款画法，大一号）
        self.title_lab = _TipLabel(title, self.header, pixel_size=16, word_wrap=False)
        head.addWidget(self.title_lab, 0, Qt.AlignVCenter)
        self.tip_lab = _TipLabel(tip or "", self.header)
        if tip:
            head.addWidget(self.tip_lab, 1, Qt.AlignVCenter)
        else:
            self.tip_lab.hide()
            head.addStretch(1)
        self.head_right = QHBoxLayout()
        self.head_right.setContentsMargins(0, 0, 0, 0)
        self.head_right.setSpacing(8)
        head.addLayout(self.head_right, 0)
        root.addWidget(self.header, 0)

        # —— 白色内容 ——
        self.body_host = QFrame(self)
        self.body_host.setObjectName("equipSectionBody")
        self.body = QVBoxLayout(self.body_host)
        self.body.setContentsMargins(REM * 2, REM + 2, REM * 2, REM + 4)
        self.body.setSpacing(8)
        self.body.setAlignment(Qt.AlignTop)
        root.addWidget(self.body_host, 0)


    def _refresh(self):
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, _section_css())
        except Exception:
            pass

    def add_widget(self, w: QWidget, stretch: int = 0):
        self.body.addWidget(w, stretch)
        return w

    def add_layout(self, lay):
        self.body.addLayout(lay)
        return lay


class _ModeBtn(GreenFrameOption):
    """模式切换（简单/复杂/神名文字）：点击由 Layout 外部接管（互斥）。"""

    def __init__(self, text: str, parent=None):
        super().__init__("", text, parent, fixed_h=34, font_px=13, font_weight=600)
        self.lab.setAlignment(Qt.AlignCenter)

    def set_on(self, on):
        self.set_checked(bool(on), emit=False)

    def is_on(self) -> bool:
        return self.is_checked()


class _ToggleChip(GreenFrameOption):
    """结果区开关（万能设计图/附带详细概率）：点击自切换。"""

    def __init__(self, text: str, parent=None):
        super().__init__("", text, parent, fixed_h=32, font_px=12)
        self.setFixedHeight(32)

    def is_on(self) -> bool:
        return self.is_checked()

    def set_on(self, on):
        self.set_checked(bool(on), emit=False)


class Layout(QWidget):
    """Layout(parent, config) — 顶栏冻结；装备/神名两套结果与关卡串独立。"""

    def __init__(self, parent=None, config=None, **kwargs):
        super().__init__(parent)
        self.config = config
        self.setObjectName("equipFarmLayout")
        self.setProperty("hoardFreezeTop", True)
        self.setProperty("hoardSingleScroll", True)
        try:
            self.setMinimumWidth(0)
            self.setMinimumHeight(360)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.setStyleSheet(_page_css() + themed_input_css())
            self.setAutoFillBackground(False)
        except Exception:
            pass

        self._table = load_stage_table()
        try:
            self._stone_table = load_secretstone_table()
        except Exception as e:
            print("[equip] secretstone load failed:", e)
            self._stone_table = {"stones": [], "stages": []}

        self._slot_edits: Dict[str, LineEdit] = {}
        self._mode = "simple"
        self._last_equip_text = ""
        self._last_stone_text = ""
        self._last_equip_plan = None
        self._last_stone_result = None
        self._last_needs_key = ""
        self._run_overrides: Dict[str, int] = {}  # stage_id -> runs
        self._header_settings_cells = []
        self._loading = True
        self._stone_list = None  # type: Optional[QListWidget]

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop)

        # ===== 冻结顶栏 =====
        self._build_top_bar(root)

        # ===== 可滚内容 =====
        body = self._build_scroll_body(root)

        # 装备/神名 IO 块 + 兼容旧属性 + 脚注
        self._build_io_blocks(body)

        self._connect_signals(body)

        self._set_mode("simple")
        self._load_from_config()
        self._loading = False
        QTimer.singleShot(0, self._fit_texts)

        # 深色模式适配：统一刷（labels/输入框/QFrame白底/_Section/_NoteCell/_ModeBtn 等）
        if apply_full_theme_refresh is not None:
            apply_full_theme_refresh(self)
            # 主题统一由工具页容器（ToolsFragment connect_theme_refresh_full）遍历刷新；
            # 页面根不再重复注册/连接，避免一次切换多重遍历造成卡顿。


    def _build_top_bar(self, root):
        """冻结顶栏：主页显示开关 + 模式切换 + 计算按钮。"""
        top = QFrame(self)
        top.setObjectName("equipTop")
        top.setStyleSheet(_top_css())
        def _top_refresh(w=top):
            try:
                from PyQt5 import sip
                if sip.isdeleted(w):
                    return
                w.setStyleSheet(_top_css())
                w.update()
            except Exception:
                pass
        top._refresh = _top_refresh  # 供统一遍历刷新（深/浅双向）
        top_v = QVBoxLayout(top)
        top_v.setContentsMargins(10, 8, 10, 8)
        top_v.setSpacing(6)

        self.sw_home_entry = SwitchButton(self)
        try:
            self.sw_home_entry.setOnText("开")
            self.sw_home_entry.setOffText("关")
        except Exception:
            pass
        try:
            self.sw_home_entry.setMinimumWidth(56)
        except Exception:
            pass
        self.sw_home_entry.setToolTip("主页显示：在主页放进入装备刷图入口（预留）")
        try:
            self.sw_home_entry.checkedChanged.connect(self._on_home_entry_changed)
        except Exception:
            pass
        self._header_settings_cells.append(
            self._make_header_setting_cell("主页显示", self.sw_home_entry, 78)
        )

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.btn_simple = _ModeBtn("简单", top)
        self.btn_complex = _ModeBtn("复杂", top)
        self.btn_stone = _ModeBtn("神明文字", top)
        self.btn_simple.mousePressEvent = lambda e: self._set_mode("simple")  # type: ignore
        self.btn_complex.mousePressEvent = lambda e: self._set_mode("complex")  # type: ignore
        self.btn_stone.mousePressEvent = lambda e: self._set_mode("stone")  # type: ignore
        row2.addWidget(self.btn_simple, 0, Qt.AlignVCenter)
        row2.addWidget(self.btn_complex, 0, Qt.AlignVCenter)
        sep = QFrame(top)
        sep.setFixedWidth(1)
        sep.setFixedHeight(22)
        sep.setStyleSheet(f"background:{themed_separator()};")
        row2.addWidget(sep, 0, Qt.AlignVCenter)
        row2.addWidget(self.btn_stone, 0, Qt.AlignVCenter)
        row2.addSpacing(12)
        self.btn_calc = PrimaryPushButton("计算计划", top)
        row2.addWidget(self.btn_calc, 0, Qt.AlignVCenter)
        row2.addStretch(1)
        top_v.addLayout(row2)
        root.addWidget(top, 0)
        root.addSpacing(2)

    def _build_scroll_body(self, root) -> QWidget:
        """可滚内容容器 + 三个模式面板。"""
        scroll = QScrollArea(self)
        scroll.setObjectName("equipScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea#equipScroll{background:transparent;border:none;}"
            + themed_scrollbar_qss()
        )
        try:
            scroll.viewport().setStyleSheet("background:transparent;")
            scroll.setAutoFillBackground(False)
            scroll.viewport().setAutoFillBackground(False)
        except Exception:
            pass
        self._scroll = scroll
        body = QWidget()
        body.setObjectName("equipBody")
        body.setStyleSheet("QWidget#equipBody{background:transparent;}")
        try:
            body.setAutoFillBackground(False)
        except Exception:
            pass
        self.body = body
        self.body_lay = QVBoxLayout(body)
        self.body_lay.setContentsMargins(0, 10, 4, 12)
        self.body_lay.setSpacing(12)
        self.body_lay.setAlignment(Qt.AlignTop)

        self.panel_simple = QWidget(body)
        self.panel_complex = QWidget(body)
        self.panel_stone = QWidget(body)
        for p in (self.panel_simple, self.panel_complex, self.panel_stone):
            p.setStyleSheet("background:transparent;")
            try:
                p.setAutoFillBackground(False)
            except Exception:
                pass

        self._build_simple(self.panel_simple)
        self._build_complex(self.panel_complex)
        self._build_stone(self.panel_stone)
        self.body_lay.addWidget(self.panel_simple)
        self.body_lay.addWidget(self.panel_complex)
        self.body_lay.addWidget(self.panel_stone)

        root.addWidget(scroll, 1)
        return body

    def _build_io_blocks(self, body):
        """装备/神名两组 输入→结果 IO 块、兼容旧属性别名与脚注。"""
        # 装备 IO
        self.equip_io = self._build_io_block(
            body,
            kind="equip",
            apply_title="可刷关卡串",
            apply_tip="格式为地图-几图-次数，可通过修改次数点击上方计算计划，重算可能获取数量。",
            apply_ph="如 16-3-12,h11-3-8",
            result_title="装备刷图结果",
            result_ph="装备计算结果…",
            show_main=True,
            show_hard=True,
            show_univ=True,
        )
        self.body_lay.addWidget(self.equip_io["apply_sec"])
        self.body_lay.addWidget(self.equip_io["result_sec"])

        # 神名 IO
        self.stone_io = self._build_io_block(
            body,
            kind="stone",
            apply_title="可刷关卡串",
            apply_tip="格式为地图-几图-次数，可通过修改次数点击上方计算计划，重算可能获取数量。",
            apply_ph="如 h7-3-12,h11-3-12",
            result_title="推算刷图结果",
            result_ph="神明文字计算结果…",
            show_main=False,
            show_hard=True,
            show_univ=False,
        )
        self.body_lay.addWidget(self.stone_io["apply_sec"])
        self.body_lay.addWidget(self.stone_io["result_sec"])

        # 兼容旧属性
        self.ed_apply = self.equip_io["apply"]
        self.out_equip = self.equip_io["out"]
        self.out_stone = self.stone_io["out"]
        self.ed_apply_stone = self.stone_io["apply"]
        self.btn_apply_main = self.equip_io["btn_main"]
        self.btn_apply_hard = self.equip_io["btn_hard"]
        self.btn_copy = self.equip_io["btn_copy"]
        self.btn_apply_hard_stone = self.stone_io["btn_hard"]
        self.btn_copy_stone = self.stone_io["btn_copy"]
        self.chip_detail = self.equip_io["chip_detail"]
        self.chip_detail_stone = self.stone_io["chip_detail"]
        self.lbl_result = self.equip_io["result_sec"].title_lab
        self.result_head = self.equip_io["result_sec"]

        foot = QLabel("概率数据来自：https://schaledb.brightsu.cn/stage/", body)
        foot.setStyleSheet('font-family:"Microsoft YaHei";color:#789;font-size:11px;')
        self.body_lay.addWidget(foot)
        self.body_lay.addStretch(1)

        self._scroll.setWidget(body)

    def _connect_signals(self, body):
        """按钮/输入框信号与持久化定时器接线。"""
        self.btn_calc.clicked.connect(self._on_calc)
        self.equip_io["btn_copy"].clicked.connect(lambda: self._on_copy_apply("equip"))
        self.equip_io["btn_main"].clicked.connect(self._on_apply_mainline)
        self.equip_io["btn_hard"].clicked.connect(lambda: self._on_apply_hard("equip"))
        self.stone_io["btn_copy"].clicked.connect(lambda: self._on_copy_apply("stone"))
        self.stone_io["btn_hard"].clicked.connect(lambda: self._on_apply_hard("stone"))

        for ed in self._slot_edits.values():
            try:
                ed.editingFinished.connect(self._persist)
                ed.textChanged.connect(self._schedule_persist)
            except Exception:
                pass
        try:
            self.ed_stone_spec.textChanged.connect(self._schedule_persist)
            self.equip_io["apply"].textChanged.connect(self._schedule_persist)
            self.stone_io["apply"].textChanged.connect(self._schedule_persist)
        except Exception:
            pass

        self._persist_timer = QTimer(self)
        self._persist_timer.setSingleShot(True)
        self._persist_timer.setInterval(400)
        self._persist_timer.timeout.connect(self._persist)

        # 点空白关闭学生列表
        self.installEventFilter(self)
        body.installEventFilter(self)

        self._set_mode("simple")
        self._load_from_config()
        self._loading = False
        QTimer.singleShot(0, self._fit_texts)

    # ---------- header ----------
    def _make_header_setting_cell(self, title: str, widget: QWidget, min_w: int = 0) -> QFrame:
        """白底开关格；四页统一实现（tool_style.make_header_setting_cell）。"""
        from gui.components.expand.tool_style import make_header_setting_cell

        return make_header_setting_cell(
            title, widget, obj_name="equipHeaderSetting", min_w=min_w
        )

    def header_settings_widgets(self):
        cells = list(getattr(self, "_header_settings_cells", []) or [])
        # 主页栏位单选（第一栏=标题下 / 第二栏=启停下），绿框样式，全页通用
        try:
            from gui.components.expand.tool_style import make_home_bar_slot_cell
            _slot = make_home_bar_slot_cell("equip_farm")
            if _slot is not None:
                cells.append(_slot)
        except Exception as e:
            print("[equip_farm] home slot cell failed:", e)
        return cells

    def _on_home_entry_changed(self, v: bool = False):
        try:
            on = (
                bool(self.sw_home_entry.isChecked())
                if hasattr(self.sw_home_entry, "isChecked")
                else bool(v)
            )
        except Exception:
            on = bool(v)
        self._cfg_set("tool_equip_farm_home_entry", on)
        self._persist()
        # 即时刷新主页入口
        try:
            cfg = self.config
            win = cfg.get_window() if cfg is not None and hasattr(cfg, "get_window") else None
            homes = []
            if win is not None:
                for h in getattr(win, "_sub_list", [[]])[0]:
                    if getattr(h, "config", None) is cfg or True:
                        homes.append(h)
            for h in homes:
                if hasattr(h, "refresh_home_plugins"):
                    try:
                        h.refresh_home_plugins()
                    except Exception:
                        pass
        except Exception as e:
            print("[equip_farm] refresh home failed:", e)

    def _schedule_persist(self, *_):
        if getattr(self, "_loading", False):
            return
        try:
            self._persist_timer.start()
        except Exception:
            self._persist()

    # ---------- builders ----------
    def _mk_auto_text(self, parent, *, placeholder: str = "", readonly: bool = False) -> AutoHeightText:
        ed = AutoHeightText(parent)
        if placeholder:
            ed.setPlaceholderText(placeholder)
        if readonly:
            ed.setReadOnly(True)
        ed.textChanged.connect(self._fit_texts)
        return ed

    def _build_io_block(
        self,
        parent,
        *,
        kind: str,
        apply_title: str,
        apply_tip: str,
        apply_ph: str,
        result_title: str,
        result_ph: str,
        show_main: bool,
        show_hard: bool,
        show_univ: bool,
    ) -> dict:
        # —— 可刷关卡串 大框（蓝标题栏 + 白内容，输入纯白）——
        apply_sec = _Section(apply_title, parent, tip=apply_tip)
        apply_ed = self._mk_auto_text(apply_sec, placeholder=apply_ph)
        apply_sec.add_widget(apply_ed)

        brow = QHBoxLayout()
        brow.setSpacing(8)
        btn_main = PrimaryPushButton("写入普通扫荡", apply_sec)
        btn_hard = PrimaryPushButton("写入困难扫荡", apply_sec)
        btn_copy = PushButton("复制关卡串", apply_sec)
        btn_main.setVisible(show_main)
        btn_hard.setVisible(show_hard)
        if show_main:
            brow.addWidget(btn_main)
        if show_hard:
            brow.addWidget(btn_hard)
        brow.addWidget(btn_copy)
        brow.addStretch(1)
        apply_sec.add_layout(brow)

        # —— 结果 大框 ——
        result_sec = _Section(result_title, parent, tip="")
        # 右侧：倍率 + 开关（绿色选框）
        mult_host = QWidget(result_sec)
        mh = QHBoxLayout(mult_host)
        mh.setContentsMargins(0, 0, 0, 0)
        mh.setSpacing(6)
        lab_m = QLabel("当前掉落倍率", mult_host)
        lab_m.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:600;color:#234;'
        )
        mh.addWidget(lab_m, 0, Qt.AlignVCenter)
        mult_row = None
        if ExclusiveCheckRow is not None:
            mult_row = ExclusiveCheckRow(
                [("1", "1倍"), ("2", "2倍"), ("3", "3倍")],
                mult_host,
            )
            self._patch_exclusive_allow_empty(mult_row)
            try:
                mult_row.set_selected("")
            except Exception:
                pass
            try:
                mult_row.changed.connect(lambda *_: self._on_mult_changed(kind))
            except Exception:
                pass
            mh.addWidget(mult_row, 0, Qt.AlignVCenter)
            # 倍率行与右侧开关之间一条分隔线（引擎统一色）
            mult_sep = QFrame(mult_host)
            mult_sep.setFixedWidth(1)
            mult_sep.setFixedHeight(20)
            mult_sep.setStyleSheet(f"background:{themed_separator()};")
            mh.addWidget(mult_sep, 0, Qt.AlignVCenter)

        chip_univ = None
        if show_univ:
            chip_univ = _ToggleChip("显示万能设计图", mult_host)
            chip_univ.set_on(True)
            chip_univ.mousePressEvent = self._wrap_chip_click(  # type: ignore
                chip_univ.mousePressEvent, lambda: self._on_univ_changed()
            )
            mh.addWidget(chip_univ, 0, Qt.AlignVCenter)

        chip_detail = _ToggleChip("附带详细概率", mult_host)
        chip_detail.mousePressEvent = self._wrap_chip_click(  # type: ignore
            chip_detail.mousePressEvent, lambda: self._on_detail_toggled(kind)
        )
        mh.addWidget(chip_detail, 0, Qt.AlignVCenter)
        result_sec.head_right.addWidget(mult_host, 0, Qt.AlignVCenter)

        out_ed = self._mk_auto_text(result_sec, placeholder=result_ph, readonly=True)
        out_ed.setMinimumHeight(100)
        result_sec.add_widget(out_ed)

        return {
            "apply_sec": apply_sec,
            "result_sec": result_sec,
            "apply": apply_ed,
            "out": out_ed,
            "btn_main": btn_main,
            "btn_hard": btn_hard,
            "btn_copy": btn_copy,
            "chip_detail": chip_detail,
            "chip_univ": chip_univ,
            "mult_row": mult_row,
            "kind": kind,
        }

    def _build_simple(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # 最缺装备
        need_sec = _Section(
            "最缺装备",
            page,
            tip="建议按缺口从低到高填（靠前优先算）。部位填 T 阶，如 9 或 9,8。游戏内可调「持有数量，从低到高」。",
        )
        grid_host = QWidget(need_sec)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for i, (slot, cn) in enumerate(SLOT_UI_ORDER):
            r, c = divmod(i, 3)
            cell = _NoteCell(cn, grid_host)
            ed = LineEdit(cell)
            ed.setPlaceholderText("如 9,8")
            ed.setMinimumWidth(120)
            ed.setMaximumWidth(220)
            try:
                ed.setClearButtonEnabled(False)
            except Exception:
                pass
            ed.setStyleSheet(themed_input_css())
            ed.setMaxLength(32)
            self._slot_edits[slot] = ed
            cell.set_widget(ed)
            grid.addWidget(cell, r, c)
        need_sec.add_widget(grid_host)
        lay.addWidget(need_sec)

        # 计算设置
        opt_sec = _Section(
            "计算设置",
            page,
            tip="含低级装备时：选「高级图概率掉落」优先从最高级图里找概率掉落所缺低级装备；选「低级图确定掉落」优先用一定掉落该低级装备的低级图。两种策略选出的图与排列顺序不同。",
        )
        row = QHBoxLayout()
        row.setSpacing(10)
        strat_cell = _NoteCell("计算策略", opt_sec)
        if ExclusiveCheckRow is not None:
            self.strategy_row = ExclusiveCheckRow(
                [
                    ("high_random", "高级图概率掉落"),
                    ("low_fixed", "低级图确定掉落"),
                ],
                strat_cell,
            )
            self.strategy_row.set_selected("high_random")
            try:
                self.strategy_row.changed.connect(lambda *_: self._schedule_persist())
            except Exception:
                pass
            strat_cell.set_widget(self.strategy_row)
        else:
            self.strategy_row = None
            strat_cell.set_widget(QLabel("—", strat_cell))
        row.addWidget(strat_cell, 1)

        diff_cell = _NoteCell("关卡范围", opt_sec)
        if MultiCheckRow is not None:
            self.diff_row = MultiCheckRow(
                [("normal", "普通图"), ("hard", "困难图")],
                diff_cell,
            )
            self.diff_row.set_selected(["normal"])
            try:
                self.diff_row.changed.connect(lambda *_: self._schedule_persist())
            except Exception:
                pass
            diff_cell.set_widget(self.diff_row)
        else:
            self.diff_row = None
            diff_cell.set_widget(QLabel("—", diff_cell))
        row.addWidget(diff_cell, 1)
        opt_sec.add_layout(row)
        lay.addWidget(opt_sec)
        self.opt_box = opt_sec

        # 兼容：倍率/万能改到结果区，这里保留引用占位
        self.mult_row = None  # 真正挂在 equip_io
        self.sw_univ = None

    def _build_complex(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        box = _Section("复杂模式", page, tip="用于按库存精算，OCR 即将推出。")
        self.btn_ocr = PushButton("OCR 录入（即将推出）", box)
        self.btn_ocr.setEnabled(False)
        box.add_widget(self.btn_ocr)
        lay.addWidget(box)

    def _build_stone(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        cost_lines = COST_HELP_CN.replace("。专1", "。\n专1")
        tip = (
            "填写格式：学生名字,当前星级/专武-目标专武,已拥有碎片数量。"
            "不写 Z 时左侧数字表示星级。\n"
            "例：星野,3-Z4,1 表示星野从 3 星升专 4，当前 1 碎。"
            "多名学生用 ; 分隔；中文标点会自动转换。\n"
            + cost_lines
        )
        search_sec = _Section("学生检索", page, tip=tip)

        self.ed_stone_q = LineEdit(search_sec)
        self.ed_stone_q.setPlaceholderText("输入单字或名字后点选（仅主线掉落）")
        try:
            self.ed_stone_q.setClearButtonEnabled(False)
        except Exception:
            pass
        self.ed_stone_q.setStyleSheet(themed_input_css())
        self.ed_stone_q.setMinimumWidth(280)
        self.ed_stone_q.textChanged.connect(self._on_stone_query)
        self.ed_stone_q.installEventFilter(self)
        search_sec.add_widget(self.ed_stone_q)

        # 内嵌列表：不另开窗口，不抢焦点
        self._stone_list = QListWidget(search_sec)
        self._stone_list.setFocusPolicy(Qt.NoFocus)
        self._stone_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._stone_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._stone_list.setMaximumHeight(180)
        self._stone_list.hide()
        self._stone_list.setStyleSheet(
            f"QListWidget{{border:1px solid {themed_note_border()};border-radius:6px;"
            f'background:{themed_input_bg()};font-family:"Microsoft YaHei";font-size:13px;}}'
            "QListWidget::item{padding:6px 10px;}"
            f"QListWidget::item:selected{{background:{themed_success_fill_rgba(40)};color:#123;}}"
            f"QListWidget::item:hover{{background:{themed_success_fill_rgba(22)};}}"
        )
        self._stone_list.itemClicked.connect(self._on_stone_pick)
        search_sec.add_widget(self._stone_list)

        self.ed_stone_spec = self._mk_auto_text(
            search_sec, placeholder="星野,3-Z4,1;白子,Z2-Z3,20"
        )
        self.ed_stone_spec.setMinimumHeight(72)
        # 已选与输入同色纯白底
        spec_wrap = QFrame(search_sec)
        spec_wrap.setObjectName("equipNote")

        def _refresh(_w=spec_wrap):
            # 挂进主题引擎刷新链（apply_full_theme_refresh 遍历调 _refresh），
            # 深/浅切换时边线与底色都会跟上（修复浅色模式没带上它的问题）
            _w.setStyleSheet(
                "QFrame#equipNote{"
                f"border:1px solid {themed_note_border()};border-radius:8px;background:{themed_input_bg()};}}"
            )

        spec_wrap._refresh = _refresh
        _refresh()
        sw = QVBoxLayout(spec_wrap)
        sw.setContentsMargins(REM, 6, REM, 8)
        lab = QLabel("已选学生（可手改）", spec_wrap)
        lab.setStyleSheet('font-family:"Microsoft YaHei";font-size:13px;color:#222;')
        sw.addWidget(lab)
        sw.addWidget(self.ed_stone_spec)
        search_sec.add_widget(spec_wrap)
        lay.addWidget(search_sec)

        self.stone_mult_row = None  # 挂在结果区

    def eventFilter(self, obj, event):
        try:
            # 学生检索：Esc 关列表；失焦延迟关（给点击列表留时间）
            if obj is getattr(self, "ed_stone_q", None):
                if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                    self._hide_stone_list()
                    return True
                if event.type() == QEvent.FocusOut:
                    QTimer.singleShot(120, self._maybe_hide_stone_list)
            # 点页面其它处关列表
            if event.type() == QEvent.MouseButtonPress:
                if self._stone_list is not None and self._stone_list.isVisible():
                    w = obj
                    if w is not self.ed_stone_q and w is not self._stone_list:
                        # 若点在列表项上，由 itemClicked 处理
                        if not self._is_under(self._stone_list, obj):
                            self._hide_stone_list()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _is_under(self, ancestor, w) -> bool:
        try:
            while w is not None:
                if w is ancestor:
                    return True
                w = w.parent() if hasattr(w, "parent") else None
        except Exception:
            pass
        return False

    def _maybe_hide_stone_list(self):
        try:
            if self.ed_stone_q and self.ed_stone_q.hasFocus():
                return
            if self._stone_list and self._stone_list.underMouse():
                return
            self._hide_stone_list()
        except Exception:
            self._hide_stone_list()

    def _show_stone_list(self):
        if self._stone_list is None:
            return
        self._refresh_stone_list(self.ed_stone_q.text() if self.ed_stone_q else "")
        if self._stone_list.count() <= 0:
            self._hide_stone_list()
            return
        h = min(180, 32 * self._stone_list.count() + 8)
        self._stone_list.setFixedHeight(h)
        self._stone_list.show()

    def _hide_stone_list(self):
        try:
            if self._stone_list is not None:
                self._stone_list.hide()
                self._stone_list.clear()
        except Exception:
            pass

    def _patch_exclusive_allow_empty(self, row) -> None:
        if row is None:
            return

        def _on(key: str, checked: bool):
            if checked:
                for k, c in row.cards.items():
                    if k != key:
                        c.set_checked(False, emit=False)
                row._cur = key
            else:
                if key == getattr(row, "_cur", ""):
                    row._cur = ""
            try:
                row.changed.emit(row._cur)
            except Exception:
                pass

        try:
            for c in row.cards.values():
                try:
                    c.toggled.disconnect()
                except Exception:
                    pass
                c.toggled.connect(_on)
        except Exception:
            pass

    def _set_mode(self, mode: str):
        if mode not in ("simple", "complex", "stone"):
            mode = "simple"
        self._mode = mode
        self.btn_simple.set_on(mode == "simple")
        self.btn_complex.set_on(mode == "complex")
        self.btn_stone.set_on(mode == "stone")

        self.panel_simple.setVisible(mode == "simple")
        self.panel_complex.setVisible(mode == "complex")
        self.panel_stone.setVisible(mode == "stone")
        if hasattr(self, "opt_box") and self.opt_box is not None:
            self.opt_box.setVisible(mode == "simple")

        self.equip_io["apply_sec"].setVisible(mode in ("simple", "complex"))
        self.equip_io["result_sec"].setVisible(mode in ("simple", "complex"))
        self.stone_io["apply_sec"].setVisible(mode == "stone")
        self.stone_io["result_sec"].setVisible(mode == "stone")

        # 同步 mult_row 引用
        if mode == "stone":
            self.stone_mult_row = self.stone_io.get("mult_row")
            if self._last_stone_text:
                self.stone_io["out"].setPlainText(self._last_stone_text)
        else:
            self.mult_row = self.equip_io.get("mult_row")
            if self._last_equip_text:
                self.equip_io["out"].setPlainText(self._last_equip_text)

        self._hide_stone_list()
        self._fit_texts()
        if not getattr(self, "_loading", False):
            self._persist()

    # ---------- stone search ----------
    def _refresh_stone_list(self, query: str):
        if self._stone_list is None:
            return
        self._stone_list.clear()
        hits = match_students_smart(self._stone_table, query, limit=40)
        for s in hits:
            name = s["name"]
            has = bool(s.get("has_drop"))
            if not has:
                # 无主线掉落：列出但标灰，点击时忽略
                item = QListWidgetItem("%s　（无主线掉落）" % name)
                item.setData(Qt.UserRole, name)
                item.setData(Qt.UserRole + 1, False)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                try:
                    from PyQt5.QtGui import QColor

                    # 中性灰：深浅色背景上都比可选项暗一档，区分不可选
                    item.setForeground(QColor(120, 130, 145))
                except Exception:
                    pass
            else:
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, name)
                item.setData(Qt.UserRole + 1, True)
                try:
                    from PyQt5.QtGui import QColor

                    # 可选项用主题文字色：深色白字、浅色深字，别用默认黑（深色看不见）
                    item.setForeground(QColor(themed_text()))
                except Exception:
                    pass
            self._stone_list.addItem(item)

    def _on_stone_query(self, text: str):
        # 始终保持输入框可编辑；列表仅展示
        if not (text or "").strip():
            self._hide_stone_list()
            return
        if self.ed_stone_q and self.ed_stone_q.hasFocus():
            self._show_stone_list()
        else:
            self._refresh_stone_list(text or "")

    def _on_stone_pick(self, item: QListWidgetItem):
        if item is None:
            return
        has = item.data(Qt.UserRole + 1)
        if has is False:
            # 无主线掉落：直接忽略
            return
        name = item.data(Qt.UserRole)
        if not name:
            return
        cur = (self.ed_stone_spec.toPlainText() or "").strip()
        piece = "%s,3-Z4,0" % name
        if not cur:
            self.ed_stone_spec.setPlainText(piece)
        else:
            from module.tools.equip_farm.secretstone import parse_student_list

            names = {p["name"] for p in parse_student_list(cur)}
            if name in names:
                self._hide_stone_list()
                return
            self.ed_stone_spec.setPlainText(cur.rstrip(";") + ";" + piece)
        try:
            self._hide_stone_list()
            self.ed_stone_q.blockSignals(True)
            self.ed_stone_q.clear()
            self.ed_stone_q.blockSignals(False)
            self.ed_stone_q.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass
        self._persist()

    # ---------- config ----------
    def _cfg_get(self, key, default=""):
        c = self.config
        if c is None:
            return default
        try:
            if hasattr(c, "get"):
                v = c.get(key, default)
                if v is not None:
                    return v
        except Exception:
            pass
        try:
            if hasattr(c, "config") and hasattr(c.config, key):
                v = getattr(c.config, key)
                return default if v is None else v
        except Exception:
            pass
        return default

    def _cfg_set(self, key, value):
        from module.tools.base import _cfg_set as _base_cfg_set

        _base_cfg_set(self.config, key, value)

    def _load_from_config(self):
        raw = self._cfg_get("tool_equip_farm_inputs_json", "") or ""
        try:
            data = json.loads(raw) if isinstance(raw, str) and raw else (raw if isinstance(raw, dict) else {})
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}

        simple = data.get("simple") or {}
        for slot, ed in self._slot_edits.items():
            if slot in simple:
                ed.setText(str(simple[slot]))

        mult = str(data.get("drop_mult") or "")
        er = self.equip_io.get("mult_row")
        if er is not None and mult in ("1", "2", "3"):
            er.set_selected(mult)
        sm = str(data.get("stone_drop_mult") or mult or "")
        sr = self.stone_io.get("mult_row")
        if sr is not None and sm in ("1", "2", "3"):
            sr.set_selected(sm)

        strat = str(data.get("strategy") or "high_random")
        if self.strategy_row is not None:
            if strat not in ("high_random", "low_fixed"):
                strat = "high_random"
            self.strategy_row.set_selected(strat)

        diffs = data.get("diffs") or ["normal"]
        if self.diff_row is not None:
            self.diff_row.set_selected(list(diffs) or ["normal"])

        include_univ = data.get("include_univ")
        if include_univ is None:
            include_univ = True
        chip_u = self.equip_io.get("chip_univ")
        if chip_u is not None:
            chip_u.set_on(bool(include_univ))

        detailed = bool(data.get("detailed") or False)
        self.equip_io["chip_detail"].set_on(detailed)
        self.stone_io["chip_detail"].set_on(bool(data.get("stone_detailed") or detailed))

        if data.get("apply_text"):
            self.equip_io["apply"].setPlainText(str(data.get("apply_text")))
        if data.get("stone_apply_text"):
            self.stone_io["apply"].setPlainText(str(data.get("stone_apply_text")))
        elif data.get("apply_text") and (data.get("mode") == "stone"):
            self.stone_io["apply"].setPlainText(str(data.get("apply_text")))

        if data.get("stone_spec"):
            self.ed_stone_spec.setPlainText(str(data.get("stone_spec")))

        self._last_equip_text = str(data.get("last_equip_text") or "")
        self._last_stone_text = str(data.get("last_stone_text") or "")
        self._last_needs_key = str(data.get("last_needs_key") or "")
        ov = data.get("run_overrides") or {}
        if isinstance(ov, dict):
            self._run_overrides = {str(k): int(v) for k, v in ov.items() if str(k)}

        home = data.get("home_entry")
        if home is None:
            home = self._cfg_get("tool_equip_farm_home_entry", True)
        try:
            self.sw_home_entry.blockSignals(True)
            self.sw_home_entry.setChecked(bool(home if home is not None else True))
            self.sw_home_entry.blockSignals(False)
            # blockSignals 不会触发 checkedChanged，手动刷主页蓝框
            try:
                for cell in getattr(self, "_header_settings_cells", []) or []:
                    fn = getattr(cell, "_apply_header_on", None)
                    if callable(fn):
                        fn(bool(self.sw_home_entry.isChecked()))
            except Exception:
                pass
        except Exception:
            pass

        mode = data.get("mode") or "simple"
        if mode not in ("simple", "complex", "stone"):
            mode = "simple"
        self._set_mode(mode)
        if self._last_equip_text and mode != "stone":
            self.equip_io["out"].setPlainText(self._last_equip_text)
        if self._last_stone_text and mode == "stone":
            self.stone_io["out"].setPlainText(self._last_stone_text)

    def _snapshot(self) -> dict:
        simple = {}
        for slot, ed in self._slot_edits.items():
            t = (ed.text() or "").strip()
            if t:
                simple[slot] = t
        mult = self._current_mult_key(self.equip_io.get("mult_row"))
        stone_mult = self._current_mult_key(self.stone_io.get("mult_row"))
        strat = "high_random"
        if self.strategy_row is not None:
            try:
                strat = self.strategy_row.selected_key() or "high_random"
            except Exception:
                pass
        diffs = ["normal"]
        if self.diff_row is not None:
            try:
                diffs = self.diff_row.selected_keys() or ["normal"]
            except Exception:
                pass
        try:
            home = bool(self.sw_home_entry.isChecked())
        except Exception:
            home = True
        return {
            "simple": simple,
            "drop_mult": mult,
            "stone_drop_mult": stone_mult,
            "strategy": strat,
            "diffs": diffs,
            "include_univ": self._include_univ(),
            "detailed": self.equip_io["chip_detail"].is_on(),
            "stone_detailed": self.stone_io["chip_detail"].is_on(),
            "apply_text": self.equip_io["apply"].toPlainText() if self.equip_io else "",
            "stone_apply_text": self.stone_io["apply"].toPlainText() if self.stone_io else "",
            "stone_spec": self.ed_stone_spec.toPlainText()
            if hasattr(self, "ed_stone_spec")
            else "",
            "mode": self._mode,
            "last_equip_text": self._last_equip_text,
            "last_stone_text": self._last_stone_text,
            "last_needs_key": self._last_needs_key,
            "run_overrides": dict(self._run_overrides or {}),
            "home_entry": home,
        }

    def _persist(self):
        if getattr(self, "_loading", False):
            return
        try:
            payload = json.dumps(self._snapshot(), ensure_ascii=False)
            self._cfg_set("tool_equip_farm_inputs_json", payload)
        except Exception as e:
            print("[equip] persist failed:", e)

    def _current_mult_key(self, row) -> str:
        if row is None:
            return ""
        try:
            return str(row.selected_key() or "")
        except Exception:
            return ""

    def _drop_mult_value(self) -> float:
        if self._mode == "stone":
            k = self._current_mult_key(self.stone_io.get("mult_row"))
        else:
            k = self._current_mult_key(self.equip_io.get("mult_row"))
        if k in ("1", "2", "3"):
            return float(k)
        return 1.0

    def _include_univ(self) -> bool:
        chip = self.equip_io.get("chip_univ")
        if chip is None:
            return True
        return bool(chip.is_on())

    def _detailed(self, kind: str = "") -> bool:
        kind = kind or ("stone" if self._mode == "stone" else "equip")
        chip = self.stone_io["chip_detail"] if kind == "stone" else self.equip_io["chip_detail"]
        return bool(chip.is_on())

    # ---------- fit ----------
    def _fit_one(self, edit: QTextEdit, min_h: int = 48, max_h: int = 20000):
        try:
            edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            try:
                sb = edit.verticalScrollBar()
                if sb is not None:
                    sb.setEnabled(False)
                    sb.setValue(0)
                    sb.hide()
            except Exception:
                pass
            edit.setMinimumWidth(0)
            edit.setMaximumWidth(16777215)
            # 宽度优先取 viewport，其次父级，再次页面
            tw = 0
            try:
                tw = int(edit.viewport().width()) - 8
            except Exception:
                tw = 0
            if tw < 120:
                try:
                    pw = edit.parentWidget()
                    if pw is not None:
                        tw = int(pw.width()) - 24
                except Exception:
                    pass
            if tw < 120:
                tw = max(280, int(self.width() or 480) - 80)
            doc = edit.document()
            doc.setTextWidth(float(tw))
            # idealWidth 有时为 0，强制再算一次
            h = int(doc.size().height()) + 24
            # 空内容也给 min
            plain = ""
            try:
                plain = edit.toPlainText() or ""
            except Exception:
                plain = ""
            if not plain.strip():
                h = min_h
            h = max(min_h, min(h, max_h))
            edit.setMinimumHeight(h)
            edit.setMaximumHeight(h)
            edit.setFixedHeight(h)
            try:
                # 复位任何内部滚动偏移
                edit.verticalScrollBar().setValue(0)
            except Exception:
                pass
            try:
                edit.updateGeometry()
            except Exception:
                pass
        except Exception:
            pass

    def _fit_texts(self):
        try:
            self._fit_one(self.equip_io["apply"], 48, 20000)
            self._fit_one(self.equip_io["out"], 100, 20000)
            self._fit_one(self.stone_io["apply"], 48, 20000)
            self._fit_one(self.stone_io["out"], 80, 20000)
            if hasattr(self, "ed_stone_spec"):
                self._fit_one(self.ed_stone_spec, 72, 20000)
            # 通知外层 scroll 重新计算内容高度
            try:
                if getattr(self, "body", None) is not None:
                    self.body.adjustSize()
                    self.body.updateGeometry()
                if getattr(self, "_scroll", None) is not None:
                    self._scroll.widget().updateGeometry()
                    self._scroll.updateGeometry()
            except Exception:
                pass
        except Exception:
            pass

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit_texts()

    def _wrap_chip_click(self, orig, extra):
        def _fn(e):
            try:
                orig(e)
            except Exception:
                pass
            try:
                extra()
            except Exception:
                pass

        return _fn

    def _on_detail_toggled(self, kind: str = "equip"):
        self._rerender_last(kind)
        self._persist()

    def _on_univ_changed(self):
        self._rerender_last("equip")
        self._persist()

    def _on_mult_changed(self, kind: str = "equip"):
        self._schedule_persist()
        # 神明：改 1/2/3 倍必须重算「还需/总需刷」紧凑文案，不是按关卡串简略
        if kind == "stone":
            spec = (self.ed_stone_spec.toPlainText() or "").strip() if getattr(self, "ed_stone_spec", None) else ""
            if spec:
                self._calc_stone(scroll_to="result")
            else:
                QTimer.singleShot(0, lambda: self._scroll_to_section("stone", "result"))
            return
        io = self.equip_io
        text = (io["apply"].toPlainText() or "").strip()
        if text and re_has_runs(text):
            self._reestimate("equip")
        QTimer.singleShot(0, lambda: self._scroll_to_section("equip", "result"))

    def _rerender_last(self, kind: str = ""):
        kind = kind or ("stone" if self._mode == "stone" else "equip")
        if kind == "stone":
            res = getattr(self, "_last_stone_result", None)
            if res is not None:
                text = (
                    res.get("copy_text_detailed")
                    if self._detailed("stone")
                    else res.get("copy_text")
                ) or ""
                self._last_stone_text = text
                self.stone_io["out"].setPlainText(text)
                self._fit_texts()
            return
        plan = getattr(self, "_last_equip_plan", None)
        if plan is not None:
            eq = plan.get("eq") or equip_index(self._table)
            remaining = {}
            for k, v in (plan.get("remaining") or {}).items():
                try:
                    slot, tpart = str(k).split(":T", 1)
                    remaining[(slot, int(tpart))] = float(v)
                except Exception:
                    pass
            need_st = {}
            for k, v in (plan.get("needs") or {}).items():
                try:
                    slot, tpart = str(k).split(":T", 1)
                    need_st[(slot, int(tpart))] = float(v)
                except Exception:
                    pass
            text = format_plan_text(
                plan.get("plan") or [],
                eq,
                drop_mult=float(plan.get("drop_mult") or 1.0),
                strategy=str(plan.get("strategy") or "high_random"),
                total_ap=int(plan.get("total_ap") or 0),
                remaining=remaining,
                need_st=need_st or {("x", 1): 1},
                include_univ=self._include_univ(),
                detailed=self._detailed("equip"),
            )
            self._last_equip_text = text
            self.equip_io["out"].setPlainText(text)
            self._fit_texts()

    def _scroll_to_section(self, kind: str = "equip", which: str = "result"):
        """which: result → 结果大框标题栏顶；apply → 可刷关卡串标题栏顶。"""
        try:
            io = self.stone_io if kind == "stone" else self.equip_io
            target = io["apply_sec"] if which == "apply" else io["result_sec"]
            sa = getattr(self, "_scroll", None)
            if sa is None or target is None:
                return
            # 把目标大框顶对齐到视口顶部（标题栏可见）
            try:
                header = getattr(target, "header", None) or target
                y = header.mapTo(sa.widget(), QPoint(0, 0)).y()
                bar = sa.verticalScrollBar()
                if bar is not None:
                    bar.setValue(max(0, int(y) - 4))
                    return
            except Exception:
                pass
            sa.ensureWidgetVisible(target, 0, 8)
        except Exception:
            pass

    def _scroll_to_result(self, kind: str = "equip"):
        self._scroll_to_section(kind, "result")

    def _scroll_to_apply(self, kind: str = "equip"):
        self._scroll_to_section(kind, "apply")

    def _set_result_text(self, text: str, kind: str = "equip"):
        if kind == "stone":
            self._last_stone_text = text
            self.stone_io["out"].setPlainText(text)
        else:
            self._last_equip_text = text
            self.equip_io["out"].setPlainText(text)
        self._fit_texts()
        # 默认不抢滚动；计算计划走 _scroll_to_apply

    # ---------- run overrides / calc ----------
    def _needs_key(self) -> str:
        """缺口 + 关卡范围 + 策略：任一变都算「需求变更」。"""
        parts = []
        for slot, _cn in SLOT_UI_ORDER:
            ed = self._slot_edits.get(slot)
            t = (ed.text() if ed else "") or ""
            parts.append("%s=%s" % (slot, t.strip()))
        diffs = ["normal"]
        if self.diff_row is not None:
            try:
                diffs = self.diff_row.selected_keys() or ["normal"]
            except Exception:
                diffs = ["normal"]
        parts.append("diff=" + ",".join(sorted(str(x) for x in diffs)))
        strategy = "high_random"
        if self.strategy_row is not None:
            try:
                strategy = self.strategy_row.selected_key() or "high_random"
            except Exception:
                strategy = "high_random"
        parts.append("strat=" + str(strategy))
        return "|".join(parts)

    def _collect_overrides_from_text(self, text: str) -> Dict[str, int]:
        """普通/困难默认都是 1；非默认次数记为覆盖。"""
        out: Dict[str, int] = {}
        for sid, runs in parse_run_spec(text or ""):
            sid = str(sid)
            default = 1
            try:
                n = int(runs)
            except Exception:
                continue
            if n != default:
                out[sid] = n
        return out

    def _apply_overrides_to_plan(self, plan_rows: list, overrides: Dict[str, int]) -> Tuple[list, str]:
        """把覆盖次数写回 plan，并生成 apply_text。"""
        if not plan_rows:
            return plan_rows, ""
        used = set()
        for r in plan_rows:
            sid = str(r.get("stage_id") or "")
            # 兼容 h 前缀
            key = sid
            alt = sid[1:] if sid.lower().startswith("h") else ("h" + sid)
            if sid in overrides:
                key = sid
            elif alt in overrides:
                key = alt
            else:
                continue
            n = int(overrides[key])
            r["runs"] = n
            ap = max(1, int(r.get("ap_cost") or 10))
            r["ap_cost_total"] = n * ap
            used.add(key)
            used.add(sid)
        # 只保留 plan 内图；覆盖仅判断/生成
        apply_parts = []
        for r in plan_rows:
            sid = str(r.get("stage_id") or "")
            tok = str(r.get("apply_token") or "")
            runs = int(r.get("runs") or 1)
            if tok.endswith("-"):
                apply_parts.append("%s%d" % (tok, runs))
            elif tok:
                apply_parts.append("%s-%d" % (tok, runs))
            else:
                apply_parts.append("%s-%d" % (sid, runs))
        return plan_rows, ",".join(apply_parts)

    def _on_calc(self):
        self._persist()
        if self._mode == "stone":
            text = (self.stone_io["apply"].toPlainText() or "").strip()
            ov = self._collect_overrides_from_text(text)
            if ov and not (self.ed_stone_spec.toPlainText() or "").strip():
                self._reestimate("stone")
            elif ov and self._last_stone_result is not None:
                self._reestimate("stone")
            else:
                self._calc_stone()
            return
        if self._mode == "complex":
            self._set_result_text(
                "复杂模式即将推出。刷图请用「简单」或「神明文字」。", "equip"
            )
            self._persist()
            return
        self._calc_simple()

    def _has_any_need(self) -> bool:
        for ed in self._slot_edits.values():
            if parse_tier_list(ed.text()):
                return True
        return False

    def _calc_simple(self):
        text = (self.equip_io["apply"].toPlainText() or "").strip()
        # 先记下关卡串里的非默认次数
        overrides = self._collect_overrides_from_text(text)
        if overrides:
            self._run_overrides = dict(overrides)

        needs_key = self._needs_key()
        needs_changed = needs_key != (self._last_needs_key or "")

        # 缺口没变 + 有覆盖次数 → 只按串重算产出
        if (not needs_changed) and overrides and self._last_equip_plan is not None:
            self._reestimate("equip")
            self._persist()
            return
        if (not needs_changed) and overrides and not self._has_any_need():
            self._reestimate("equip")
            self._persist()
            return

        slot_tiers = {}
        for slot, _cn in SLOT_UI_ORDER:
            ed = self._slot_edits.get(slot)
            if not ed:
                continue
            tiers = parse_tier_list(ed.text())
            if tiers:
                slot_tiers[slot] = tiers
        needs = needs_from_simple(slot_tiers, each=1)
        strategy = "high_random"
        if self.strategy_row is not None:
            strategy = self.strategy_row.selected_key() or "high_random"
        diffs = ["normal"]
        if self.diff_row is not None:
            diffs = self.diff_row.selected_keys() or ["normal"]
        include_normal = "normal" in diffs
        include_hard = "hard" in diffs
        if not include_normal and not include_hard:
            include_normal = True
        mult = self._drop_mult_value()
        if not needs:
            self._set_result_text(
                "还没有填写缺口。\n请在各部位输入框填写所缺 T 阶，例如项链填 9,8。",
                "equip",
            )
            self._persist()
            return

        result, plan = self._simple_recommend(
            needs, strategy, include_normal, include_hard, mult
        )

        # 全部默认 1 次；覆盖次数后写
        apply_text = self._normalize_plan_runs(plan, overrides, result)

        # 缺口/范围变了：新结果若包含改过次数的图，保留该次数；否则只用新结果
        if overrides:
            plan, kept_text = self._keep_overrides_for_new_plan(plan, overrides, result)
            if kept_text:
                apply_text = kept_text

        text_out = self._render_plan_text(result, needs, mult, strategy)
        self._last_equip_plan = result
        self._last_needs_key = needs_key
        self.equip_io["apply"].setPlainText(result.get("apply_text") or apply_text)
        self._set_result_text(text_out, "equip")
        self._persist()
        QTimer.singleShot(0, lambda: self._scroll_to_apply("equip"))

    def _simple_recommend(self, needs, strategy, include_normal, include_hard, mult):
        """基础推荐；勾了困难却一张困难都没有时再单独推一轮困难图补上。"""
        result = recommend_stages(
            needs,
            self._table,
            strategy=strategy,
            include_normal=include_normal,
            include_hard=include_hard,
            drop_mult=mult,
            each_run_cap=1,  # 计划默认每图只刷 1 次
        )

        plan = list(result.get("plan") or [])

        def _is_hard_row(r) -> bool:
            sid = str(r.get("stage_id") or "").lower()
            diff = str(r.get("difficulty") or "").lower()
            return sid.startswith("h") or diff == "hard"

        if include_hard and not any(_is_hard_row(r) for r in plan):
            hard_only = recommend_stages(
                needs,
                self._table,
                strategy=strategy,
                include_normal=False,
                include_hard=True,
                drop_mult=mult,
                each_run_cap=1,
                max_stages=6,
            )
            seen = {str(r.get("stage_id") or "") for r in plan}
            for r in list(hard_only.get("plan") or []):
                sid = str(r.get("stage_id") or "")
                if sid and sid not in seen:
                    plan.append(r)
                    seen.add(sid)
        return result, plan

    def _normalize_plan_runs(self, plan, overrides, result) -> str:
        """未被覆盖的行统一 1 次，并重建 apply_text / total_ap。"""
        for r in plan:
            sid = str(r.get("stage_id") or "")
            if overrides and (sid in overrides or sid.lower() in {k.lower() for k in overrides}):
                continue
            r["runs"] = 1
            ap = max(1, int(r.get("ap_cost") or 10))
            r["ap_cost_total"] = ap
        apply_parts = []
        for r in plan:
            tok = str(r.get("apply_token") or "")
            sid = str(r.get("stage_id") or "")
            runs = int(r.get("runs") or 1)
            if tok.endswith("-"):
                apply_parts.append("%s%d" % (tok, runs))
            elif tok:
                apply_parts.append("%s-%d" % (tok, runs))
            else:
                apply_parts.append("%s-%d" % (sid, runs))
        apply_text = ",".join(apply_parts)
        result["plan"] = plan
        result["apply_text"] = apply_text
        result["total_ap"] = sum(int(r.get("ap_cost_total") or 0) for r in plan)
        return apply_text

    def _keep_overrides_for_new_plan(self, plan, overrides, result):
        """新结果包含改过次数的图则保留该次数；不包含的覆盖直接丢弃。"""
        plan_ids = set()
        for r in plan:
            sid = str(r.get("stage_id") or "")
            plan_ids.add(sid)
            if sid.lower().startswith("h"):
                plan_ids.add(sid[1:])
            else:
                plan_ids.add("h" + sid)
        keep = {
            k: v
            for k, v in overrides.items()
            if k in plan_ids or k.lower() in {x.lower() for x in plan_ids}
        }
        apply_text = ""
        if keep:
            plan, apply_text = self._apply_overrides_to_plan(plan, keep)
            result["plan"] = plan
            result["apply_text"] = apply_text
            result["total_ap"] = sum(int(r.get("ap_cost_total") or 0) for r in plan)
        # 不包含的覆盖直接丢弃（只输出新结果）
        self._run_overrides = dict(keep)
        return plan, apply_text

    def _render_plan_text(self, result, needs, mult, strategy) -> str:
        """把推荐结果渲染成展示文案。"""
        eq = result.get("eq") or equip_index(self._table)
        remaining = {}
        for k, v in (result.get("remaining") or {}).items():
            try:
                slot, tpart = str(k).split(":T", 1)
                remaining[(slot, int(tpart))] = float(v)
            except Exception:
                pass
        need_st = {}
        for k, v in (result.get("needs") or {}).items():
            try:
                slot, tpart = str(k).split(":T", 1)
                need_st[(slot, int(tpart))] = float(v)
            except Exception:
                pass
        return format_plan_text(
            result.get("plan") or [],
            eq,
            drop_mult=mult,
            strategy=strategy,
            total_ap=int(result.get("total_ap") or 0),
            remaining=remaining,
            need_st=need_st or needs,
            include_univ=self._include_univ(),
            detailed=self._detailed("equip"),
        )

    def _calc_stone(self, scroll_to: str = "apply"):
        text = self.ed_stone_spec.toPlainText() or ""
        mult = self._drop_mult_value()
        result = plan_many(self._stone_table, text, default_runs=1, drop_mult=mult)
        # 若关卡串有非默认次数且新结果含该图，保留次数
        apply_cur = (self.stone_io["apply"].toPlainText() or "").strip()
        overrides = self._collect_overrides_from_text(apply_cur)
        apply_text = result.get("apply_text") or ""
        if overrides and apply_text:
            # stone apply_text 是 hX-Y-N 串，合并覆盖
            specs = parse_run_spec(apply_text)
            parts = []
            for sid, runs in specs:
                n = overrides.get(sid, overrides.get(sid.lower(), runs))
                if sid.lower().startswith("h"):
                    # 困难默认 3
                    parts.append("%s-%d" % (sid, int(n)))
                else:
                    parts.append("h%s-%d" % (sid, int(n)))
            if parts:
                apply_text = ",".join(parts)
                result["apply_text"] = apply_text
        self._last_stone_result = result
        out = (
            result.get("copy_text_detailed")
            if self._detailed("stone")
            else result.get("copy_text")
        ) or ""
        self.stone_io["apply"].setPlainText(result.get("apply_text") or apply_text)
        self._set_result_text(out, "stone")
        self._persist()
        which = scroll_to if scroll_to in ("apply", "result") else "apply"
        QTimer.singleShot(0, lambda w=which: self._scroll_to_section("stone", w))

    def _reestimate(self, kind: str = "equip"):
        io = self.stone_io if kind == "stone" else self.equip_io
        text = (io["apply"].toPlainText() or "").strip()
        mult = self._drop_mult_value()
        if kind == "stone":
            block = _stone_reestimate(
                text,
                self._stone_table,
                mult,
                detailed=self._detailed("stone"),
            )
        else:
            result = estimate_from_run_text(
                text,
                self._table,
                drop_mult=mult,
                include_univ=self._include_univ(),
                detailed=self._detailed("equip"),
            )
            block = result.get("copy_text") or ""
        self._set_result_text(block, kind)
        self._persist()

    def _on_copy_apply(self, kind: str = "equip"):
        io = self.stone_io if kind == "stone" else self.equip_io
        text = (io["apply"].toPlainText() or "").strip()
        if not text:
            return
        try:
            QApplication.clipboard().setText(text)
        except Exception:
            pass

    def _on_apply_mainline(self):
        text = (self.equip_io["apply"].toPlainText() or "").strip()
        main_s = apply_tokens_to_mainline_string(text)
        if not main_s:
            self.equip_io["out"].append("\n（关卡串里没有可应用的普通图）")
            self._fit_texts()
            return
        self._write_priority("mainlinePriority", "unfinished_normal_tasks", main_s, True)
        self.equip_io["out"].append("\n已写入普通图：%s" % main_s)
        self._fit_texts()
        self._persist()

    def _on_apply_hard(self, kind: str = "equip"):
        io = self.stone_io if kind == "stone" else self.equip_io
        text = (io["apply"].toPlainText() or "").strip()
        if kind == "stone":
            hard_s = apply_tokens_to_hard_string(text) or _plain_as_hard(text)
        else:
            hard_s = apply_tokens_to_hard_string(text)
        if not hard_s:
            io["out"].append("\n（关卡串里没有可应用的困难图）")
            self._fit_texts()
            return
        self._write_priority("hardPriority", "unfinished_hard_tasks", hard_s, False)
        io["out"].append("\n已写入困难图：%s" % hard_s)
        self._fit_texts()
        self._persist()

    def _write_priority(self, key: str, unfinished_key: str, value: str, is_normal: bool):
        c = self.config
        if c is None or not hasattr(c, "set"):
            return
        try:
            from module.explore_tasks.sweep_task import read_task

            temp = []
            for part in value.split(","):
                part = part.strip()
                if not part:
                    continue
                temp.append(read_task(part, is_normal))
            c.set(key, value)
            c.set(unfinished_key, temp)
        except Exception:
            try:
                c.set(key, value)
            except Exception as e:
                # 未通关任务串没写进去=用户填的关卡丢失，必须留痕
                print("[equip_farm] 未通关任务写入失败:", e)


def re_has_runs(text: str) -> bool:
    return bool(re.search(r"\d+-\d+(?:-\d+)?", text or ""))


def re_has_nondefault_runs(text: str) -> bool:
    """普通/困难默认都是 1；任一非默认 → True。"""
    found = re.findall(r"([hH])?(\d+)-(\d+)-(\d+)", text or "")
    if not found:
        return False
    for _hard, _a, _b, n in found:
        try:
            if int(n) != 1:
                return True
        except Exception:
            return True
    return False


def _plain_as_hard(text: str) -> str:
    specs = parse_run_spec(text)
    parts = []
    for sid, runs in specs:
        s = str(sid)
        if s.startswith("h"):
            s = s[1:]
        parts.append("%s-%d" % (s, int(runs)))
    return ",".join(parts)


def _stone_reestimate(text: str, table: dict, mult: float, *, detailed: bool = False) -> str:
    specs = parse_run_spec(text)
    lines = ["【按当前次数估算】"]
    if not specs:
        lines.append("尚未识别到关卡次数。可写：h7-3-12,h11-3-12")
        return "\n".join(lines)
    by_id = {str(s.get("id")): s for s in table.get("stages") or []}
    totals = {}
    for sid, runs in specs:
        st = by_id.get(sid) or by_id.get(sid.lower())
        if not st:
            lines.append("· %s ×%s：表中无此关" % (sid, runs))
            continue
        ap = max(1, int(st.get("ap_cost") or 20))
        lines.append("· %s  ×%s %d体" % (sid, runs, ap * int(runs)))
        for fd in st.get("fixed_drops") or []:
            name = fd.get("student_name") or fd.get("name") or "?"
            ch = float(fd.get("chance") or 0.4)
            exp = float(fd.get("expected") or ch) * mult * runs
            totals[name] = totals.get(name, 0.0) + exp
            if detailed:
                lines.append(
                    "  %s %s%% / 次  期望 %.2f"
                    % (name, int(ch * 100), float(fd.get("expected") or ch))
                )
            lines.append("  约可获得：%s≈%.2f" % (name, exp))
    if totals:
        lines.append(
            "合计约："
            + "，".join(
                "%s≈%.2f" % (n, v)
                for n, v in sorted(totals.items(), key=lambda x: -x[1])
            )
        )
    return "\n".join(lines)
