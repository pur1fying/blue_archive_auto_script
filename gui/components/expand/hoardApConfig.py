# -*- coding: utf-8 -*-
"""囤体配置页：三列便签并排（现状|目标|已领），小框随内容+1rem，窗高对齐咖啡厅。"""

from __future__ import annotations

import json
import os
import time
import traceback
from datetime import datetime

from PyQt5.QtCore import Qt, QDate, QPoint, QThread, pyqtSignal, QSize, QTimer, QEvent
from PyQt5.QtGui import QColor, QFont, QIntValidator, QPainter, QTextDocument, QTextOption
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QDialog,
    QCalendarWidget,
    QTextEdit,
    QGridLayout,
    QScrollArea,
    QStyle,
    QStyleOption,
)

from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, SwitchButton

from gui.util import notification

try:
    from gui.components.expand.hoard_goods import MultiCheckRow, ExclusiveCheckRow
except Exception:
    from .hoard_goods import MultiCheckRow, ExclusiveCheckRow  # type: ignore

from gui.components.expand.tool_style import (
    REM,
    SWITCH_CELL_H,
    SWITCH_CELL_PAD_X,
    SWITCH_CELL_PAD_Y,
    TipLabel,
    attach_header_switch_refresh,
    header_switch_css,
    themed_accent,
    themed_accent_text,
    themed_input_bg,
    themed_input_css,
    themed_input_border,
    themed_note_bg,
    themed_note_border,
    themed_page_bg,
    themed_page_transparent_qss,
    themed_separator,
    themed_title_bar_qss,
    themed_scrollbar_qss,
    themed_section_body_bg,
    themed_soft_border_rgba,
    themed_switch_note_bg,
    themed_text,
    themed_title_text,
)

try:
    from gui.util.config_gui import configGui
except Exception:  # pragma: no cover
    configGui = None

PAGE_W = 780
PAGE_H = 480
CONTENT_MAX_W = 744
# ── 主题感知 CSS 构建 ──
def _build_input_css():
    return themed_input_css()

def _build_note_css():
    return (
        "QFrame#hoardNote{"
        f"border:1px solid {themed_note_border()};"
        f"border-radius:8px;background:{themed_note_bg()};}}"
    )

def _build_note_switch_css():
    return (
        "QFrame#hoardNote{"
        f"border:1px solid {themed_note_border()};"
        f"border-radius:8px;background:{themed_switch_note_bg()};}}"
    )

def _build_page_bg():
    return themed_page_bg()

def _build_header_switch_css():
    return header_switch_css("hoardHeaderSetting", "spendDestCell")

# 兼容旧引用：模块加载时初始化浅色默认值，_refresh_theme_css() 会动态刷新
INPUT_WHITE_CSS = _build_input_css()
NOTE_WHITE_CSS = _build_note_css()
NOTE_SWITCH_CSS = _build_note_switch_css()
NOTE_BLUE_CSS = NOTE_WHITE_CSS
NOTE_CYAN_CSS = NOTE_WHITE_CSS
PAGE_SURROUND_BG = _build_page_bg()
HEADER_SWITCH_OFF_CSS, HEADER_SWITCH_ON_CSS = _build_header_switch_css()
SPEND_DEST_OFF_CSS = HEADER_SWITCH_OFF_CSS
SPEND_DEST_ON_CSS = HEADER_SWITCH_ON_CSS


def _refresh_theme_css():
    """主题变化时刷新所有 CSS 常量（已设样式的组件仍需 Layout._apply_theme 重设）。"""
    import sys
    mod = sys.modules.get(__name__)
    if mod is None:
        return
    mod.INPUT_WHITE_CSS = _build_input_css()
    mod.NOTE_WHITE_CSS = _build_note_css()
    mod.NOTE_SWITCH_CSS = _build_note_switch_css()
    mod.NOTE_BLUE_CSS = mod.NOTE_WHITE_CSS
    mod.NOTE_CYAN_CSS = mod.NOTE_WHITE_CSS
    mod.PAGE_SURROUND_BG = _build_page_bg()
    mod.HEADER_SWITCH_OFF_CSS, mod.HEADER_SWITCH_ON_CSS = _build_header_switch_css()
    mod.SPEND_DEST_OFF_CSS = mod.HEADER_SWITCH_OFF_CSS
    mod.SPEND_DEST_ON_CSS = mod.HEADER_SWITCH_ON_CSS

# 囤体使用方法（点「使用方法」按钮 toggle 显示/隐藏的面板，随时可关，无确定键）
USAGE_TEXT = (
    "本工具目的，是让你在高价值活动，多倍主线的时候，能获得更多体力。\n"
    "为此它的运作方式是这样的：\n"
    "当囤体启用后，它会接管所有一切花费体力，以及获得体力的程序活动。\n"
    "同时根据你能否接受钻石买体以及是否买了体力卡，计算出来最好的方式，"
    "让你在最少消耗的情况下，在设定的日子到来前，尽可能多地保留体力以及邮件体力。\n"
    "为此你需要做的是：\n\n"
    "【第1步·填写角色体力，咖啡厅上限，以及当前现状】\n"
    "如果计算时，已经被程序自动做了某些任务等，请务必打开\n"
    "今日是否已领里，任务 / 竞技场商店 / 小组 / 免费买体的开关。\n\n"
    "【第2步·生成计划】\n"
    "填好现状后点「计算计划」，随后程序会自动计算完毕。\n\n"
    "【第3步·核对计划】\n"
    "仔细看计划里的步骤和时刻：\n"
    "·必须保持开启里，会有请保持程序在该段期间开启的建议。\n"
    "重点在，看清体部分的设置是否足够邮箱中9xx+的体力领取完毕。\n"
    "如果哪步不对，回配置卡改现状或策略，重新点「计算计划」即可。\n\n"
    "【第4步·启动执行】\n"
    "启动程序即可。请保证计划里所写的时间内，程序是开启状态，以及当天记得登录即可。"
)


def _cfg_get(config, key, default=None):
    try:
        if hasattr(config, "config") and hasattr(config.config, key):
            v = getattr(config.config, key)
            if v is not None:
                return v
    except Exception:
        pass
    try:
        if hasattr(config, "config"):
            return getattr(config.config, key, default)
    except Exception:
        pass
    return default


def _cfg_set(config, key, value):
    try:
        if hasattr(config, "set"):
            config.set(key, value)
            return
    except Exception:
        pass
    try:
        if hasattr(config, "config"):
            setattr(config.config, key, value)
            if hasattr(config, "save"):
                config.save()
    except Exception as e:
        # 两条写路径都失败=用户改动没保存，整页配置写入都过这里，必须留痕
        print("[hoard_ap] 配置写入失败:", key, e)


def _as_bool(v, default=False):
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off", ""):
        return False
    return bool(v)


def _as_str(v, default=""):
    return default if v is None else str(v).strip()



def _forward_wheel_to_outer(widget, event) -> bool:
    """多行框滚轮交给最近外层 QScrollArea。"""
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
                    if abs(delta) < 120:
                        bar.setValue(bar.value() - int(delta))
                    else:
                        bar.setValue(bar.value() - int(delta / 120.0 * step * 3))
                    return True
            w = w.parentWidget() if hasattr(w, "parentWidget") else w.parent()
    except Exception:
        return False
    return False


# 标题栏/说明文字统一用 tool_style.TipLabel（粗体 + 白描边 + 主题感知，
# pixel_size=16 + word_wrap=False 作大框标题栏单行标题）。
# 历史遗留的本地复制品 _TipLabel 类已收敛为别名。
_TipLabel = TipLabel


class _NoInnerScrollText(QTextEdit):
    """计划/多行：高度随内容，滚轮交给外层页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        try:
            self.viewport().installEventFilter(self)
            self.installEventFilter(self)
        except Exception:
            pass
        try:
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
        if dx:
            super().scrollContentsBy(dx, 0)

    def sizeHint(self):
        # 有界提示：宽度不随文档理想宽（长行/长串）膨胀，锁在当前宽度附近，
        # 高度按文档现算——杜绝 Section(Maximum 策略) 被撑出视口
        try:
            w = max(280, min(int(self.width() or 480), 1600))
            h = int(self.document().size().height()) + 24
            from PyQt5.QtCore import QSize as _QS

            return _QS(w, max(120, min(h, 20000)))
        except Exception:
            return super().sizeHint()

    def minimumSizeHint(self):
        # 允许收缩到 0：宽度唯一真源是 _fit 的视口现算，不让旧 sizeHint 卡死页面
        try:
            from PyQt5.QtCore import QSize as _QS

            h = int(self.document().size().height()) + 24
            return _QS(0, max(120, min(h, 20000)))
        except Exception:
            return super().minimumSizeHint()


class NoteCell(QFrame):
    """便签小框：上标题下控件；宽随内容，左右 0.5rem，靠左不居中。

    switch_box=True → 开关类白底小框；否则大框内浅青小框。
    """

    def __init__(self, title: str, parent=None, *, white: bool = True, switch_box: bool = False):
        super().__init__(parent)
        self._switch_box = bool(switch_box)
        self.setObjectName("hoardNote")
        # 必须开 StyledBackground，否则部分样式下 QFrame 底色/边框画不出来
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(NOTE_SWITCH_CSS if switch_box else NOTE_WHITE_CSS)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        lay = QVBoxLayout(self)
        # 开关小框上下更匀；普通便签略紧
        if switch_box:
            lay.setContentsMargins(REM, 6, REM, 8)
        else:
            lay.setContentsMargins(REM, 4, REM, 6)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.title = QLabel(title, self)
        self.title.setObjectName("hoardNoteTitle")
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title.setStyleSheet(
            'QLabel#hoardNoteTitle{font-family:"Microsoft YaHei";'
            f"font-size:13px;font-weight:900;color:{themed_title_text()};background:transparent;}}"
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
        self.slot.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lay.addLayout(self.slot)

    def paintEvent(self, event):
        # 让 QSS 的 background / border-radius 真正生效（与商店 GoodsCard 同套路）
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def set_widget(self, w: QWidget):
        while self.slot.count():
            it = self.slot.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
        self.slot.addWidget(w, 0, Qt.AlignLeft)
        return w


class Section(QFrame):
    """大框：浅蓝标题栏 + 大厅同色实心底（非透明）。"""

    def __init__(self, title: str, parent=None, tip: str = ""):
        super().__init__(parent)
        self.setObjectName("hoardSection")
        # 实心底必须 StyledBackground + 强制填色，禁止透明穿透
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        try:
            from PyQt5.QtGui import QPalette
            _pal = self.palette()
            _bg = QColor(themed_section_body_bg())
            _pal.setColor(QPalette.Window, _bg)
            _pal.setColor(QPalette.Base, _bg)
            self.setPalette(_pal)
        except Exception:
            pass
        self.setStyleSheet(self._section_qss())
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # 标题栏
        self.header = QFrame(self)
        self.header.setObjectName("hoardSectionHeader")
        self.header.setAttribute(Qt.WA_StyledBackground, True)
        self.header.setAutoFillBackground(False)
        head = QHBoxLayout(self.header)
        head.setContentsMargins(REM * 2, 8, REM * 2, 8)
        head.setSpacing(8)
        head.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # 标题文字：近黑粗体 + 白描边（与说明文字同款画法，大一号）
        self.title_lab = _TipLabel(title, self.header, pixel_size=16, word_wrap=False)
        head.addWidget(self.title_lab, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.tip_lab = _TipLabel(tip or "", self.header)
        if tip:
            head.addWidget(self.tip_lab, 1, Qt.AlignVCenter)
        else:
            self.tip_lab.hide()
            head.addStretch(1)
        self.head_right = QHBoxLayout()
        self.head_right.setContentsMargins(0, 0, 0, 0)
        self.head_right.setSpacing(6)
        head.addLayout(self.head_right, 0)
        # 兼容旧代码读 lab
        self._title = self.title_lab
        root.addWidget(self.header, 0)

        # 白内容
        self.body_host = QFrame(self)
        self.body_host.setObjectName("hoardSectionBody")
        self.body_host.setAttribute(Qt.WA_StyledBackground, True)
        self.body_host.setAutoFillBackground(True)
        try:
            from PyQt5.QtGui import QPalette
            _pal = self.body_host.palette()
            _bg = QColor(themed_section_body_bg())
            _pal.setColor(QPalette.Window, _bg)
            _pal.setColor(QPalette.Base, _bg)
            self.body_host.setPalette(_pal)
        except Exception:
            pass
        body_l = QVBoxLayout(self.body_host)
        body_l.setContentsMargins(REM * 2, REM + 2, REM * 2, REM + 4)
        body_l.setSpacing(REM)
        body_l.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # 小框容器：横向流式换行，靠左
        self._flow_host = QWidget(self.body_host)
        self._flow = QHBoxLayout(self._flow_host)
        self._flow.setContentsMargins(0, 0, 0, 0)
        self._flow.setSpacing(6)
        self._flow.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        body_l.addWidget(self._flow_host, 0, Qt.AlignLeft)
        # 纵向备用
        self.col = QVBoxLayout()
        self.col.setContentsMargins(0, 0, 0, 0)
        self.col.setSpacing(6)
        self.col.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        body_l.addLayout(self.col)
        self._extra = QVBoxLayout()
        self._extra.setContentsMargins(0, 0, 0, 0)
        self._extra.setSpacing(6)
        body_l.addLayout(self._extra)
        root.addWidget(self.body_host, 0)
        self._use_flow = True

    def _section_qss(self) -> str:
        """Section 主题感知 QSS：主题引擎统一工厂，不再自造。"""
        from gui.components.expand.tool_style import themed_section_css

        return themed_section_css("hoardSection", "hoardSectionHeader", "hoardSectionBody")

    def _refresh(self):
        """_refresh() 别名 → 转发 _refresh_theme，供 equip_farm/auto_push 的 w._refresh() 调用。"""
        self._refresh_theme()

    def _refresh_theme(self):
        """主题变化时刷新 Section 样式。"""
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, self._section_qss())
            from PyQt5.QtGui import QPalette
            _pal = self.palette()
            _bg = QColor(themed_section_body_bg())
            _pal.setColor(QPalette.Window, _bg)
            _pal.setColor(QPalette.Base, _bg)
            self.setPalette(_pal)
        except Exception:
            pass



    def set_vertical(self, on: bool = True):
        """True=小框竖排（现状/目标）；False=小框横排流式（今日已领）。"""
        self._use_flow = not on
        try:
            self._flow_host.setVisible(self._use_flow)
        except Exception:
            pass

    def add_note(self, note: "NoteCell"):
        if self._use_flow:
            self._flow.addWidget(note, 0, Qt.AlignLeft | Qt.AlignTop)
        else:
            self.col.addWidget(note, 0, Qt.AlignLeft | Qt.AlignTop)
        return note

    def add_extra(self, w: QWidget):
        self._extra.addWidget(w)
        return w

    def add_extra_layout(self, lay):
        self._extra.addLayout(lay)
        return lay


class _CalendarPopup(QDialog):
    def __init__(self, parent=None, current=None, minimum=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self._chosen = current or QDate.currentDate()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        self.cal = QCalendarWidget(self)
        self.cal.setSelectedDate(self._chosen)
        if minimum:
            self.cal.setMinimumDate(minimum)
        self.cal.clicked.connect(self._pick)
        lay.addWidget(self.cal)

    def _pick(self, qd):
        self._chosen = qd
        self.accept()

    def chosen(self):
        return self._chosen


class _Worker(QThread):
    ok = pyqtSignal(object)
    fail = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.ok.emit(self._fn(self.status.emit))
        except Exception as e:
            self.fail.emit(str(e))


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self._mail_bags = []
        self._worker = None
        self.setObjectName("hoardApLayout")
        try:
            from gui.components.expand.tool_style import themed_page_transparent_qss

            self.setStyleSheet(themed_page_transparent_qss("hoardApLayout", "hoardScroll"))
            self.setAutoFillBackground(False)
        except Exception:
            pass
        # 外层 Dialog 负责整页滚动时：顶栏用 sticky 模拟——页内顶栏 + 可滚 body
        # 属性给 Dialog：识别囤体，视口 480，内容更高则滚
        self.setProperty("hoardCafeSized", True)
        self.setProperty("hoardFreezeTop", True)
        try:
            # 跟随工具页默认宽度，不强制比窗口更宽
            self.setMinimumWidth(0)
            self.setMinimumHeight(360)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        except Exception:
            pass

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop)

        # ===== 冻结顶栏：两行式 =====
        self._build_top_bar(root)

        # ===== 仅内容区滚动；外层 Dialog 对囤体关竖滚 → 顶栏冻结 =====
        self.setProperty("hoardSingleScroll", True)
        self._build_scroll(root)

        try:
            self._build()
            self._load()
            self._load_plan()
            self._fit()
            QTimer.singleShot(0, self._sync_claimed_height)
            self._proj_timer = QTimer(self)
            self._proj_timer.setInterval(30 * 1000)
            self._proj_timer.timeout.connect(self._tick_project)
            # 仅启用且有计划才跑；关闭时彻底停表
            self._sync_proj_timer()
            QTimer.singleShot(200, self._tick_project)
        except Exception as e:
            self.body.addWidget(QLabel("初始化失败：%s" % e))

    def _build_top_bar(self, root):
        """冻结顶栏：拦截状态 + 去向开关 + 一键清除/计算 + 上限/日期输入。"""
        top = QFrame(self)
        top.setObjectName("hoardTop")
        top.setStyleSheet(self._top_bar_qss())
        top_v = QVBoxLayout(top)
        top_v.setContentsMargins(10, 6, 10, 6)
        top_v.setSpacing(2)  # 紧密：约 0.1rem

        # 设置相关开关：挂到 ToolsFragment 标题栏右侧（名称旁），不在此占行
        self._build_header_switches()

        # 行1：左=使用囤体开关；中=状态+花体去向；最右=清除配置
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(8)
        row2.setAlignment(Qt.AlignVCenter)

        # 使用囤体总开关（自设置栏移入）：与花体去向格同画法，开=蓝框
        en_cell = QFrame(top)
        en_cell.setObjectName("spendDestCell")
        en_cell.setAttribute(Qt.WA_StyledBackground, True)
        en_cell.setStyleSheet(SPEND_DEST_OFF_CSS)
        attach_header_switch_refresh(en_cell)
        env = QVBoxLayout(en_cell)
        env.setContentsMargins(
            SWITCH_CELL_PAD_X, SWITCH_CELL_PAD_Y, SWITCH_CELL_PAD_X, SWITCH_CELL_PAD_Y
        )
        env.setSpacing(2)
        env.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        en_lab = QLabel("使用囤体", en_cell)
        en_lab.setAlignment(Qt.AlignHCenter)
        en_lab.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:900;'
            "color:#222;background:transparent;"
        )
        env.addWidget(en_lab, 0, Qt.AlignHCenter)
        env.addWidget(self.sw_enabled, 0, Qt.AlignHCenter)
        en_cell.setMinimumWidth(88)
        en_cell.setFixedHeight(SWITCH_CELL_H)
        en_cell.setMinimumHeight(SWITCH_CELL_H)
        row2.addWidget(en_cell, 0, Qt.AlignVCenter)

        def _sync_enabled(on, c=en_cell):
            try:
                _state_fn = getattr(c, "_apply_switch_state", None)
                if callable(_state_fn):
                    _state_fn(bool(on))
                else:
                    from gui.components.expand.tool_style import _switch_qss

                    c.setStyleSheet(_switch_qss("spendDestCell", bool(on)))
                c.update()
            except Exception:
                pass

        self.sw_enabled.checkedChanged.connect(_sync_enabled)
        try:
            _sync_enabled(bool(self.sw_enabled.isChecked()))
        except Exception:
            pass

        # 弹性空白1：把「说明+四开关」组推离左侧使用囤体开关
        row2.addStretch(1)

        self.lbl_status = QLabel("激活右侧开关\n会拦截选项以外的花体力事件", top)
        self.lbl_status.setWordWrap(True)
        # 组内左端；宽度以「激活右侧开关」行为准，长句自动折成三行
        # （wordWrap QLabel 的 sizeHint 宽度虚大，必须锁死）
        self.lbl_status.setFixedWidth(94)
        self.lbl_status.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.lbl_status.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:700;color:#345;'
        )
        row2.addWidget(self.lbl_status, 0, Qt.AlignVCenter)

        self._build_spend_dest_cells(top, row2)

        # 弹性空白2：四开关之后再弹开，清除配置贴最右；将来要加的东西放这
        row2.addStretch(1)

        # 最右：清除配置（原「计算囤体计划」位置；计算/使用方法移入第二栏）
        self.btn_new_plan = PrimaryPushButton("清除配置", top)
        self.btn_new_plan.setMinimumWidth(100)
        self.btn_new_plan.setToolTip(
            "仅清除可变数值配置。清空执行记录、今日已领、当前现状与旧计划；"
            "保留体力/咖啡上限、氪金、清体配置、花体时刻。"
        )
        self.btn_new_plan.clicked.connect(self._on_new_plan)
        row2.addWidget(self.btn_new_plan, 0, Qt.AlignVCenter)
        top_v.addLayout(row2)

        # 细分隔线
        sep = QFrame(top)
        sep.setObjectName("hoardTopSep")
        sep.setFixedHeight(1)
        top_v.addWidget(sep)

        # 行3：上限 / 消费日 / 花体时刻（可换行流式）
        self._build_top_row3(top, top_v)

        root.addWidget(top, 0)
        root.addSpacing(2)

    def _top_bar_qss(self) -> str:
        """顶栏：标题栏工厂统一发放（与 equipTop 同线同底）+ 引擎分隔线。"""
        return (
            themed_title_bar_qss("hoardTop")
            + "QFrame#hoardTopMini{"
            + f"border:1px solid {themed_soft_border_rgba(50)};"
            + f"border-radius:8px;background:{themed_input_bg()};}}"
            + "QFrame#hoardTopSep{"
            + f"background:{themed_separator()};max-height:1px;min-height:1px;}}"
        )

    def _build_header_switches(self):
        """标题栏侧设置开关：主页显示 / 拦截显示（纯设置，不含插件启停）。
        使用囤体总开关移入页面顶栏第一栏最左（见顶栏构建处）。"""
        self._header_settings_cells = []
        self.sw_enabled = SwitchButton(self)
        try:
            self.sw_enabled.setOnText("开")
            self.sw_enabled.setOffText("关")
        except Exception:
            pass
        self.sw_enabled.setMinimumWidth(56)
        self.sw_enabled.setToolTip("使用囤体：计划开启与否，将拦截原有事件")
        self.sw_enabled.checkedChanged.connect(self._on_enabled_changed)

        self.sw_home_entry = SwitchButton(self)
        try:
            self.sw_home_entry.setOnText("开")
            self.sw_home_entry.setOffText("关")
        except Exception:
            pass
        self.sw_home_entry.setMinimumWidth(56)
        self.sw_home_entry.setToolTip("主页显示：在主页放「进入囤体」按钮")
        self.sw_home_entry.checkedChanged.connect(self._on_home_entry_changed)
        self._header_settings_cells.append(
            self._make_header_setting_cell("主页显示", self.sw_home_entry, 78)
        )

        self.sw_home_intercept = SwitchButton(self)
        try:
            self.sw_home_intercept.setOnText("开")
            self.sw_home_intercept.setOffText("关")
        except Exception:
            pass
        self.sw_home_intercept.setMinimumWidth(56)
        self.sw_home_intercept.setToolTip("拦截显示：主页显示三个优先清体开关")
        self.sw_home_intercept.checkedChanged.connect(self._on_home_intercept_changed)
        self._header_settings_cells.append(
            self._make_header_setting_cell("拦截显示", self.sw_home_intercept, 78)
        )

    def _build_spend_dest_cells(self, top, row2):
        """4 项花体去向拦截开关：普通多倍 / 困难多倍 / 特别委托3倍 / 高价值活动。"""
        self._spend_dest_switches = {}
        self._spend_dest_cells = {}
        for title, key in (
            ("普通多倍", "normal"),
            ("困难多倍", "hard"),
            ("特别委托3倍", "special"),
            ("高价值活动", "high_value"),
        ):
            cell = QFrame(top)
            cell.setObjectName("spendDestCell")
            cell.setAttribute(Qt.WA_StyledBackground, True)
            cell.setStyleSheet(SPEND_DEST_OFF_CSS)
            attach_header_switch_refresh(cell)  # 现算 _refresh + 统一 paintEvent 画框
            vl = QVBoxLayout(cell)
            # 与顶栏设置开关同一套边距/高度
            vl.setContentsMargins(SWITCH_CELL_PAD_X, SWITCH_CELL_PAD_Y, SWITCH_CELL_PAD_X, SWITCH_CELL_PAD_Y)
            vl.setSpacing(2)
            vl.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            lab = QLabel(title, cell)
            lab.setAlignment(Qt.AlignHCenter)
            lab.setStyleSheet(
                'font-family:"Microsoft YaHei";font-size:12px;font-weight:900;color:#222;background:transparent;'
            )
            sw = SwitchButton(cell)
            try:
                sw.setOnText("开")
                sw.setOffText("关")
            except Exception:
                pass
            sw.setToolTip("激活拦截其它花体；并给「到点清体力」对应项自动填 -1")
            vl.addWidget(lab, 0, Qt.AlignHCenter)
            vl.addWidget(sw, 0, Qt.AlignHCenter)
            cell.setMinimumWidth(88)
            cell.setFixedHeight(SWITCH_CELL_H)
            cell.setMinimumHeight(SWITCH_CELL_H)
            self._spend_dest_cells[key] = cell
            self._spend_dest_switches[key] = sw
            row2.addWidget(cell, 0, Qt.AlignVCenter)
            # 开启 = 蓝框（现算 CSS，切主题后再拨仍正确）
            def _sync_spend(on, c=cell):
                try:
                    _state_fn = getattr(c, "_apply_switch_state", None)
                    if callable(_state_fn):
                        _state_fn(bool(on))
                    else:
                        from gui.components.expand.tool_style import _switch_qss

                        c.setStyleSheet(_switch_qss("spendDestCell", bool(on)))
                    c.update()
                except Exception:
                    pass
            sw.checkedChanged.connect(_sync_spend)
            try:
                _sync_spend(bool(sw.isChecked()))
            except Exception:
                pass
            sw.checkedChanged.connect(
                lambda checked, mode=key: self._on_spend_dest_toggled(mode, checked)
            )

    def _build_top_row3(self, top, top_v):
        """行3：上限 / 消费日 / 花体时刻（可换行流式）。"""
        def _top_cell(title: str, widget: QWidget, min_w: int = 0) -> QFrame:
            cell = QFrame(top)
            cell.setObjectName("hoardTopMini")
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(8, 4, 8, 4)
            cl.setSpacing(2)
            cl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            lab = QLabel(title, cell)
            lab.setAlignment(Qt.AlignHCenter)
            lab.setStyleSheet(
                'font-family:"Microsoft YaHei";font-size:12px;font-weight:600;color:#222;'
            )
            cl.addWidget(lab, 0, Qt.AlignHCenter)
            cl.addWidget(widget, 0, Qt.AlignHCenter)
            if min_w:
                cell.setMinimumWidth(min_w)
            cell.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            return cell

        row3_host = QWidget(top)
        row3 = QHBoxLayout(row3_host)
        row3.setContentsMargins(0, 0, 0, 0)
        row3.setSpacing(8)
        self.edit_soft = LineEdit(top)
        self.edit_soft.setFixedWidth(56)
        self.edit_soft.setAlignment(Qt.AlignCenter)
        self.edit_soft.setValidator(QIntValidator(1, 999, top))
        self.edit_soft.editingFinished.connect(
            lambda: self._save("hoard_ap_soft_cap", self.edit_soft.text().strip() or "160")
        )
        row3.addWidget(_top_cell("体力上限", self.edit_soft, 88), 0, Qt.AlignVCenter)

        self.edit_cafe_cap = LineEdit(top)
        self.edit_cafe_cap.setFixedWidth(56)
        self.edit_cafe_cap.setAlignment(Qt.AlignCenter)
        self.edit_cafe_cap.setValidator(QIntValidator(1, 9999, top))
        self.edit_cafe_cap.editingFinished.connect(
            lambda: self._save(
                "hoard_ap_cafe_ap_full_cap", self.edit_cafe_cap.text().strip() or "740"
            )
        )
        row3.addWidget(_top_cell("咖啡厅上限", self.edit_cafe_cap, 100), 0, Qt.AlignVCenter)

        dw = QWidget(top)
        dh = QHBoxLayout(dw)
        dh.setContentsMargins(0, 0, 0, 0)
        dh.setSpacing(6)
        self.edit_date = LineEdit(top)
        self.edit_date.setFixedWidth(118)
        self.edit_date.setAlignment(Qt.AlignCenter)
        self.edit_date.setPlaceholderText("yyyy-MM-dd")
        self._bind(self.edit_date, "hoard_ap_target_date")
        self.btn_cal = PushButton("📅", top)
        self.btn_cal.setFixedSize(36, 30)
        self.btn_cal.setToolTip("选择消费日")
        self.btn_cal.clicked.connect(self._popup_cal)
        dh.addWidget(self.edit_date)
        dh.addWidget(self.btn_cal)
        row3.addWidget(_top_cell("消费日", dw, 180), 0, Qt.AlignVCenter)

        self.edit_spend_time = LineEdit(top)
        self.edit_spend_time.setFixedWidth(64)
        self.edit_spend_time.setAlignment(Qt.AlignCenter)
        self.edit_spend_time.setPlaceholderText("18:30")
        self._bind(self.edit_spend_time, "hoard_ap_spend_time")
        row3.addWidget(_top_cell("花体时刻", self.edit_spend_time, 96), 0, Qt.AlignVCenter)
        # 第二栏最右：计算囤体计划 + 使用方法 上下排（自第一栏移入；
        # 使用方法面板点开时插在「使用方法」紧邻下方，类下拉菜单）
        self._top_right_v = QVBoxLayout()
        self._top_right_v.setContentsMargins(0, 0, 0, 0)
        self._top_right_v.setSpacing(4)
        self.btn_calc = PrimaryPushButton("计算囤体计划", top)
        self.btn_calc.setFixedWidth(120)
        self.btn_calc.clicked.connect(self._on_calculate)
        self._top_right_v.addWidget(self.btn_calc, 0, Qt.AlignLeft)
        self.btn_usage = PushButton("使用方法", top)
        self.btn_usage.setFixedWidth(120)
        self.btn_usage.clicked.connect(self._show_usage_menu)
        self._top_right_v.addWidget(self.btn_usage, 0, Qt.AlignLeft)
        right_host = QWidget(top)
        right_host.setLayout(self._top_right_v)
        row3.addStretch(1)
        row3.addWidget(right_host, 0, Qt.AlignVCenter)
        top_v.addWidget(row3_host)

    def _build_scroll(self, root):
        """仅内容区滚动容器；外层 Dialog 对囤体关竖滚 → 顶栏冻结。"""
        scroll = QScrollArea(self)
        scroll.setObjectName("hoardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea#hoardScroll{background:transparent;border:none;}"
            + themed_scrollbar_qss()
        )
        try:
            scroll.viewport().setStyleSheet("background:transparent;")
            scroll.setAutoFillBackground(False)
            scroll.viewport().setAutoFillBackground(False)
        except Exception:
            pass
        self._scroll = scroll
        try:
            sb = scroll.verticalScrollBar()
            if sb is not None:
                # 竖滚动条出现/消失会改变视口宽 → 重算计划框宽度（防横向溢出）
                sb.rangeChanged.connect(lambda *_a: self._fit())
        except Exception:
            pass
        body = QWidget()
        body.setObjectName("hoardBody")
        body.setStyleSheet("QWidget#hoardBody{background:transparent;}")
        try:
            body.setAutoFillBackground(False)
        except Exception:
            pass
        self.body = QVBoxLayout(body)
        # 右边距 0：计划框右缘到 Section 边框的距离=左侧(16px)，左右对称
        self.body.setContentsMargins(0, 0, 0, 8)
        self.body.setSpacing(10)  # 大框间距再紧一点，避免横向溢出观感
        self.body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)


    def _style_input_white(self, w):
        """输入控件统一纯白底。"""
        try:
            if w is None:
                return
            w.setStyleSheet(INPUT_WHITE_CSS)
        except Exception:
            pass

    def _num(self, lo, hi, w=56):
        e = LineEdit(self)
        e.setFixedWidth(w)
        e.setAlignment(Qt.AlignCenter)
        self._style_input_white(e)
        e.setValidator(QIntValidator(lo, hi, self))
        return e

    def _save(self, k, v):
        try:
            _cfg_set(self.config, k, v)
        except Exception:
            pass

    def _bind(self, e, k):
        e.editingFinished.connect(lambda: self._save(k, e.text().strip()))
        return e

    def _mail_detail_text(self) -> str:
        try:
            return (self.edit_mail_detail.toPlainText() or "").replace("\n", ",").replace("，", ",")
        except Exception:
            return ""

    def _set_mail_detail_text(self, s: str):
        """写入邮箱明细：逗号串折成最多两行显示。"""
        raw = (s or "").replace("，", ",").replace("\n", ",").strip()
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts:
            show = ""
        elif len(parts) <= 3:
            show = ",".join(parts)
        else:
            mid = (len(parts) + 1) // 2
            show = ",".join(parts[:mid]) + "\n" + ",".join(parts[mid:])
        try:
            w = self.edit_mail_detail
            w.blockSignals(True)
            w.setPlainText(show)
            w.blockSignals(False)
        except Exception:
            pass

    def _mail_detail_focus_out(self, event):
        try:
            from PyQt5.QtWidgets import QTextEdit as _QTE
            _QTE.focusOutEvent(self.edit_mail_detail, event)
        except Exception:
            pass
        try:
            self._on_mail_detail()
        except Exception:
            pass

    def _build(self):
        # ----- 行1：当前现状整行 -----
        self._build_status_section()

        # ----- 行2：氪金相关 整行 -----
        self._build_pay_section()

        # ----- 多自回清体 / 到点清体力：独立配置，不绑原扫荡设置 -----
        self._build_clear_panels()

        # ----- 计划全文（不截断）-----
        self._build_plan_section()

        # 主题感知：初始化 + 注册主题引擎（引擎 0ms+150ms 双刷，页面不再另连 themeChanged）
        self._apply_theme()
        if configGui is not None:
            try:
                from gui.components.expand.tool_style import register_theme_managed

                register_theme_managed(self, self._apply_theme)
            except Exception:
                pass

    def _apply_theme(self):
        """主题变化时刷新关键组件样式（深色/浅色切换）。"""
        try:
            _refresh_theme_css()
        except Exception:
            pass
        try:
            from PyQt5.QtWidgets import QLineEdit as _QLE
            from PyQt5.QtGui import QPalette
            import re as _re
            # 全局 QPalette：设默认背景和文字色（影响未设样式的组件）
            _pal = self.palette()
            _bg = QColor(themed_page_bg())
            _txt = QColor(themed_text())
            _pal.setColor(QPalette.Window, _bg)
            _pal.setColor(QPalette.Base, _bg)
            _pal.setColor(QPalette.Text, _txt)
            _pal.setColor(QPalette.WindowText, _txt)
            self.setPalette(_pal)
            # 输入框 / 文本框统一刷新
            css_input = INPUT_WHITE_CSS
            from gui.components.expand.tool_style import set_style_dedup as _dedup
            for w in self.findChildren(_QLE):
                try:
                    _dedup(w, css_input)
                except Exception:
                    pass
            for w in self.findChildren(QTextEdit):
                try:
                    _dedup(w, css_input)
                except Exception:
                    pass
            # 便签框 + 顶栏刷新
            note_css = NOTE_WHITE_CSS
            sw_css = NOTE_SWITCH_CSS
            top_qss = self._top_bar_qss()
            for w in self.findChildren(QFrame):
                try:
                    name = w.objectName()
                    if name == "hoardNote":
                        # switch_box 用白底(与设置栏开关格同款),普通便签用浅青底
                        _dedup(w, sw_css if getattr(w, "_switch_box", False) else note_css)
                    elif name == "hoardTop":
                        _dedup(w, top_qss)
                    elif name in ("spendDestCell", "hoardHeaderSetting"):
                        # 开关格：调 attach_header_switch_refresh 挂的现算 _refresh
                        # （深/浅双向正确，不依赖浅色常量快照）
                        _fn = getattr(w, "_refresh", None)
                        if callable(_fn):
                            _fn()
                        else:
                            _accent = themed_accent()
                            _on = _accent in (w.styleSheet() or "")
                            _dedup(w, SPEND_DEST_ON_CSS if _on else SPEND_DEST_OFF_CSS)
                except Exception:
                    pass
            # Section 大框刷新
            for w in self.findChildren(Section):
                try:
                    w._refresh_theme()
                except Exception:
                    pass
            # QLabel 深灰文字色 → 主题感知（保留蓝色强调色 #1a5fb4 不动）
            txt = themed_text()
            # 含 themed 值(e0e0e0/e8e8e8/333333/111111):切回浅色能逆向匹配→双向可逆
            dark_re = _re.compile(
                r'color:#(222|223|234|333|334|345|456|622|678|789|'
                r'142433|2A3A4A|1a3a7a|'
                r'e0e0e0|e8e8e8|333333|111111);',
                _re.IGNORECASE,
            )
            for w in self.findChildren(QLabel):
                try:
                    old = w.styleSheet() or ""
                    if dark_re.search(old):
                        _dedup(w, dark_re.sub(f'color:{txt};', old))
                except Exception:
                    pass
            # 竞技场统计字(蓝色强调)跟主题刷新
            try:
                if getattr(self, "lbl_jjc", None) is not None:
                    _dedup(
                        self.lbl_jjc,
                        'font-family:"Microsoft YaHei";color:%s;font-size:14px;font-weight:700;'
                        % themed_accent_text(),
                    )
            except Exception:
                pass
            self.update()
        except Exception:
            pass

    def _build_status_ap_row(self) -> QWidget:
        """现状上排：当前体力 + 咖啡可领。"""
        row_ap = QHBoxLayout()
        row_ap.setContentsMargins(0, 0, 0, 0)
        row_ap.setSpacing(8)
        row_ap.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        n = NoteCell("当前体力", self)
        self.edit_current_ap = self._num(0, 999, 72)
        self._style_input_white(self.edit_current_ap)
        self._bind(self.edit_current_ap, "hoard_ap_current_ap")
        self.edit_current_ap.editingFinished.connect(self._resnap_inventory_from_form)
        n.set_widget(self.edit_current_ap)
        row_ap.addWidget(n, 0, Qt.AlignLeft | Qt.AlignTop)
        n = NoteCell("咖啡可领", self)
        self.edit_cafe_claimable = self._num(0, 9999, 72)
        self._style_input_white(self.edit_cafe_claimable)
        self._bind(self.edit_cafe_claimable, "hoard_ap_cafe_claimable_manual")
        self.edit_cafe_claimable.editingFinished.connect(self._resnap_inventory_from_form)
        n.set_widget(self.edit_cafe_claimable)
        row_ap.addWidget(n, 0, Qt.AlignLeft | Qt.AlignTop)
        row_ap.addStretch(1)
        wrap_ap = QWidget(self)
        wrap_ap.setLayout(row_ap)
        try:
            wrap_ap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        except Exception:
            pass
        return wrap_ap

    def _build_mail_detail_cell(self) -> "NoteCell":
        """邮箱明细：输入框 + 合计行 + 识别按钮。"""
        n_mail = NoteCell("邮箱明细", self)
        try:
            n_mail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            n_mail.setMaximumWidth(16777215)
            n_mail.setMinimumWidth(280)
        except Exception:
            pass
        mail_host = QWidget(n_mail)
        mv = QVBoxLayout(mail_host)
        mv.setContentsMargins(0, 0, 0, 0)
        mv.setSpacing(6)
        self.edit_mail_detail = _NoInnerScrollText(self)
        self.edit_mail_detail.setPlaceholderText(
            "@后为该体力写着的持续时间，如10@d6为这个10体力持续6天，数字为小时，小数点会自走。"
        )
        self.edit_mail_detail.setMinimumHeight(72)
        self.edit_mail_detail.setMinimumWidth(260)
        self.edit_mail_detail.setMaximumWidth(16777215)
        self.edit_mail_detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.edit_mail_detail.setAcceptRichText(False)
        self.edit_mail_detail.setLineWrapMode(QTextEdit.WidgetWidth)
        self.edit_mail_detail.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.edit_mail_detail.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._style_input_white(self.edit_mail_detail)
        try:
            self.edit_mail_detail.focusOutEvent = self._mail_detail_focus_out  # type: ignore
        except Exception:
            pass
        mv.addWidget(self.edit_mail_detail)

        self.lbl_mail = QLabel("", mail_host)
        self.lbl_mail.setWordWrap(True)
        self.lbl_mail.setStyleSheet(
            'font-family:"Microsoft YaHei";color:#456;font-size:12px;'
        )
        self.lbl_mail.setMinimumHeight(16)
        mv.addWidget(self.lbl_mail)

        sum_row = QHBoxLayout()
        sum_row.setContentsMargins(0, 0, 0, 0)
        sum_row.setSpacing(8)
        sum_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lab_sum = QLabel("合计：", mail_host)
        lab_sum.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:13px;color:#222;font-weight:600;'
        )
        sum_row.addWidget(lab_sum, 0)
        self.edit_mail_ap = self._num(0, 99999, 80)
        self.edit_mail_ap.setReadOnly(True)
        self._style_input_white(self.edit_mail_ap)
        try:
            self.edit_mail_ap.setStyleSheet(
                self.edit_mail_ap.styleSheet()
                + "QLineEdit{background:%s;}" % themed_note_bg()
            )
        except Exception:
            pass
        self._bind(self.edit_mail_ap, "hoard_ap_mail_ap")
        sum_row.addWidget(self.edit_mail_ap, 0)
        self.btn_mail_ocr = PrimaryPushButton("识别邮箱", mail_host)
        self.btn_mail_ocr.setMinimumWidth(96)
        self.btn_mail_ocr.setToolTip(
            "只识别邮箱写入明细，不跑清体/囤体计划。\n"
            "需已连上模拟器；不必为了识别去开一整套囤体。"
        )
        self.btn_mail_ocr.clicked.connect(self._on_mail_ocr)
        sum_row.addWidget(self.btn_mail_ocr, 0)
        sum_row.addStretch(1)
        mv.addLayout(sum_row)
        n_mail.set_widget(mail_host)
        return n_mail

    def _build_claimed_grid(self) -> "NoteCell":
        """今天是否已领：5 个白色开关小框（登陆/日程/小组/礼包/竞技场商店）。"""
        n_claimed = NoteCell("今天是否已领（影响计算）", self)
        try:
            n_claimed.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            n_claimed.setMinimumWidth(280)
            n_claimed.setMaximumWidth(440)
        except Exception:
            pass
        items = [
            ("登陆100体", "sw_task", "hoard_ap_task_claimed", 0, 0),
            ("日程50体", "sw_lesson", "hoard_ap_lesson_claimed", 0, 1),
            ("小组10体", "sw_group", "hoard_ap_group_claimed", 1, 0),
            ("礼包10体", "sw_free", "hoard_ap_free_buy_claimed", 1, 1),
            ("竞技场商店", "sw_jjc", "hoard_ap_jjc_claimed", 2, 0),
        ]
        grid_host = QWidget(n_claimed)
        grid_host.setAttribute(Qt.WA_StyledBackground, True)
        grid_host.setStyleSheet("background:transparent;")
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(2, 2, 2, 2)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        for title, attr, key, row, col in items:
            # 每个开关 = 独立白底小框（上字下开关），与标题栏/设置栏开关格同视觉语言
            cell = NoteCell(title, grid_host, switch_box=True)
            try:
                cell.setMinimumWidth(118)
            except Exception:
                pass
            sw = SwitchButton(cell)
            try:
                sw.setOnText("已领")
                sw.setOffText("未领")
            except Exception:
                pass
            sw.setMinimumWidth(72)
            sw.setMaximumWidth(88)
            sw.setChecked(False)
            sw.checkedChanged.connect(lambda v, k=key, s=sw: self._on_claimed_switch(k, v, s))
            cell.set_widget(sw)
            setattr(self, attr, sw)
            span = 2 if row == 2 else 1
            grid.addWidget(cell, row, col, 1, span, Qt.AlignLeft)
        n_claimed.set_widget(grid_host)
        return n_claimed

    def _build_status_section(self):
        """行1：当前现状整行；内部：上排体力/咖啡，下排邮箱+今天是否已领。"""
        sec = Section(
            "当前现状",
            self,
            tip="请填写当前体力以及咖啡厅可领体力，邮箱明细可自填可识别后修改",
        )
        sec.set_vertical(True)
        try:
            sec.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            sec.setMaximumWidth(16777215)
            sec.setMinimumWidth(0)
        except Exception:
            pass

        # 上排：当前体力 + 咖啡可领
        sec.col.addWidget(self._build_status_ap_row(), 0, Qt.AlignLeft | Qt.AlignTop)

        # 下排：邮箱明细 | 今天是否已领（顶部与邮箱小框顶对齐，形成错位）
        row_mail = QHBoxLayout()
        row_mail.setContentsMargins(0, 0, 0, 0)
        row_mail.setSpacing(10)
        row_mail.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        row_mail.addWidget(self._build_mail_detail_cell(), 3)
        n_claimed = self._build_claimed_grid()
        row_mail.addWidget(n_claimed, 0, Qt.AlignTop)

        wrap_mail = QWidget(self)
        wrap_mail.setLayout(row_mail)
        try:
            wrap_mail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        except Exception:
            pass
        sec.col.addWidget(wrap_mail, 0, Qt.AlignLeft | Qt.AlignTop)

        self.edit_daily_xy = LineEdit(self)
        self.edit_daily_xy.hide()
        self.btn_pick = PushButton("点选", self)
        self.btn_pick.hide()
        self.lbl_pick = QLabel("", self)
        self.lbl_pick.hide()
        # 兼容旧代码：_sec_claimed 指向现状内已领小框
        self._sec_status = sec
        self._sec_claimed = n_claimed
        self.body.addWidget(sec, 0)

    def _build_pay_section(self):
        """行2：氪金相关（买管上限 / 竞技场商店 / 体力礼包）。"""
        sec = Section(
            "氪金相关",
            self,
            tip="请填写体力不满时愿意如何买体。",
        )
        sec.set_vertical(False)
        try:
            sec.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        except Exception:
            pass

        def _lab(t):
            _l = QLabel(t, self)
            _l.setStyleSheet(
                'color:%s;font-family:"Microsoft YaHei";font-size:12px;'
                "font-weight:700;background:transparent;" % themed_text()
            )
            return _l

        n = NoteCell("买管上限（按缺口适度）", self)
        bw = QWidget(self)
        bl = QHBoxLayout(bw)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)
        bl.addWidget(_lab("数量"))
        self.edit_tubes = self._num(0, 6, 44)
        self._bind(self.edit_tubes, "hoard_ap_tubes")
        bl.addWidget(self.edit_tubes)
        bl.addWidget(_lab("天数"))
        self.edit_tube_days = self._num(0, 3, 44)
        self._bind(self.edit_tube_days, "hoard_ap_tube_days")
        bl.addWidget(self.edit_tube_days)
        # 保留隐藏刷新逻辑，但不展示勤奋/上限小字
        self.lbl_strategy = QLabel("", self)
        self.lbl_strategy.hide()
        try:
            self.edit_tubes.textChanged.connect(self._upd_strategy)
            self.edit_tube_days.textChanged.connect(self._upd_strategy)
        except Exception:
            pass
        n.set_widget(bw)
        sec.add_note(n)

        n = NoteCell("竞技场商店（按缺口适度）", self)
        self._jjc_note = n
        # 标题右侧挂统计数字
        try:
            head_l = n.layout()
            # NoteCell 内部 title 在 layout 第 0 项；改成 标题+数字 横排
            title_row = QHBoxLayout()
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.setSpacing(8)
            n.title.setParent(None)
            title_row.addWidget(n.title, 0, Qt.AlignLeft | Qt.AlignVCenter)
            self.lbl_jjc = QLabel("0", n)
            self.lbl_jjc.setStyleSheet(
                'font-family:"Microsoft YaHei";color:%s;font-size:14px;font-weight:700;'
                % themed_accent_text()
            )
            title_row.addWidget(self.lbl_jjc, 0, Qt.AlignLeft | Qt.AlignVCenter)
            title_row.addStretch(1)
            # 原 title 位置替换
            head_l.insertLayout(0, title_row)
        except Exception:
            self.lbl_jjc = QLabel("0", self)
            self.lbl_jjc.setStyleSheet("color:%s;font-size:14px;font-weight:700;" % themed_accent_text())
        try:
            # 统计数字（如 120/360）定宽，变化时不挤动标题行
            self.lbl_jjc.setMinimumWidth(44)
        except Exception:
            pass
        jw = QWidget(self)
        jh = QHBoxLayout(jw)
        jh.setContentsMargins(0, 0, 0, 0)
        jh.setSpacing(8)
        self.jjc_row = MultiCheckRow([("30", "30"), ("60", "60")], self)
        self.jjc_row.changed.connect(self._on_jjc)
        jh.addWidget(self.jjc_row)
        jh.addWidget(_lab("刷新"))
        self.edit_jjc_refresh = self._num(0, 3, 40)
        self._bind(self.edit_jjc_refresh, "hoard_ap_jjc_refresh")
        self.edit_jjc_refresh.textChanged.connect(self._upd_jjc)
        jh.addWidget(self.edit_jjc_refresh)
        jh.addStretch(1)
        n.set_widget(jw)
        sec.add_note(n)

        n = NoteCell("体力礼包", self)
        self.gift_row = MultiCheckRow(
            [("0", "0"), ("130", "130"), ("150", "150")], self
        )
        # 0 与 130/150 双向互斥（后点者优先）：点 0 → 立即清 130/150；
        # 点 130/150 → 立即清 0；全取消时回落 0。逐卡连接拿得到"刚点的是谁"。
        for _k, _c in self.gift_row.cards.items():
            _c.toggled.connect(
                lambda k, ck, _card=None: self._on_gift_card(str(k), ck)
            )
        n.set_widget(self.gift_row)
        sec.add_note(n)
        self.body.addWidget(sec)

    def _build_plan_section(self):
        """计划全文（不截断）。"""
        sec = Section("计划", self)
        try:
            sec.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            sec.set_vertical(True)
        except Exception:
            pass
        self.txt_plan = _NoInnerScrollText(self)
        self.txt_plan.setReadOnly(True)
        self.txt_plan.setAcceptRichText(False)
        self.txt_plan.setLineWrapMode(QTextEdit.WidgetWidth)
        try:
            self.txt_plan.setWordWrapMode(1)  # QTextOption.WordWrap if available
        except Exception:
            pass
        self.txt_plan.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.txt_plan.setFont(QFont("Microsoft YaHei", 10))
        self.txt_plan.setMinimumHeight(160)
        self.txt_plan.setMaximumWidth(16777215)
        self.txt_plan.setPlaceholderText(
            "点「计算计划」。勤奋：主堆近满→咖啡/日替进邮→邮≈980→清0；"
            "买管数=上限，只在不够近满时按缺口买；花体日 03:50 整包领邮。"
        )
        self.txt_plan.setStyleSheet(INPUT_WHITE_CSS)
        self.txt_plan.textChanged.connect(self._fit)
        sec.add_extra(self.txt_plan)
        self.body.addWidget(sec)

    def _show_usage_menu(self):
        """toggle 使用方法浮层：点按钮在使用方法右下方弹出独立小窗口，
        不挤占顶栏布局、不改样式，随时点按钮收起。"""
        try:
            pan = getattr(self, "_usage_panel", None)
            if pan is None:
                pan = QWidget(self, Qt.Tool | Qt.FramelessWindowHint)
                pan.setWindowTitle("使用方法")
                lay = QVBoxLayout(pan)
                lay.setContentsMargins(0, 0, 0, 0)
                te = QTextEdit()
                te.setReadOnly(True)
                te.setPlainText(USAGE_TEXT)
                te.setStyleSheet(
                    "QTextEdit{background:%s;color:%s;border:1px solid %s;border-radius:6px;padding:8px;}"
                    % (themed_note_bg(), themed_text(), themed_input_border())
                )
                lay.addWidget(te)
                pan.setMinimumWidth(360)
                pan.setMinimumHeight(280)
                pan.setMaximumHeight(420)
                self._usage_panel = pan
                self._usage_te = te
            if pan.isVisible():
                pan.hide()
                return
            btn = self.btn_usage
            gp = btn.mapToGlobal(btn.rect().bottomRight())
            w = max(360, pan.sizeHint().width() or 360)
            h = max(280, pan.sizeHint().height() or 280)
            pan.resize(w, h)
            # 右对齐按钮右边、紧贴按钮下方
            pan.move(gp.x() - w, gp.y() + 2)
            pan.show()
        except Exception:
            pass

    def _mk_hint_edit(self, placeholder: str, width: int = 220):
        e = LineEdit(self)
        e.setPlaceholderText(placeholder)
        e.setMinimumWidth(120)
        e.setMaximumWidth(width)
        e.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._style_input_white(e)
        return e

    def _mk_count_edit(self, placeholder: str = "0", width: int = 56):
        e = LineEdit(self)
        e.setPlaceholderText(placeholder)
        e.setFixedWidth(width)
        e.setAlignment(Qt.AlignCenter)
        e.setValidator(QIntValidator(-1, 999, self))
        self._style_input_white(e)
        return e

    def _build_clear_block(self, *, title: str, tip: str, prefix: str, with_manual: bool, notes_horizontal: bool = False):
        sec = Section(title, self, tip=tip)
        try:
            sec.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            sec.setMaximumWidth(16777215)
        except Exception:
            pass
        # notes_horizontal=True → 小框左右流式；False → 小框竖排
        sec.set_vertical(not notes_horizontal)

        edit_main_n = self._mk_hint_edit("1-1-1 或 1-1--1", 280)
        edit_main_h = self._mk_hint_edit("h1-1-1 或空", 280)
        try:
            edit_main_n.setMaximumWidth(360)
            edit_main_h.setMaximumWidth(360)
        except Exception:
            pass
        self._clear_v_note(
            sec,
            "主线",
            self._labeled_edit_cell("普通", edit_main_n),
            self._labeled_edit_cell("困难", edit_main_h),
        )

        edit_sp_exp = self._mk_count_edit("0/-1", 56)
        edit_sp_money = self._mk_count_edit("0/-1", 56)
        self._clear_v_note(
            sec,
            "特别委托",
            self._labeled_edit_cell("经验本", edit_sp_exp),
            self._labeled_edit_cell("钱本", edit_sp_money),
        )

        # 活动：关卡与次数左右并列
        edit_act_stage = self._mk_count_edit("1", 48)
        edit_act_times = self._mk_count_edit("0/-1", 56)
        self._clear_h_note(
            sec,
            "活动",
            self._labeled_edit_cell("关卡", edit_act_stage),
            self._labeled_edit_cell("次数", edit_act_times),
        )

        # 交流会小框 + 手动清（在交流会小框之外、右侧）
        edits_scr, manual_sw = self._build_scrimmage_row(sec, with_manual)

        return {
            "sec": sec,
            "manual": manual_sw,
            "main_normal": edit_main_n,
            "main_hard": edit_main_h,
            "sp_exp": edit_sp_exp,
            "sp_money": edit_sp_money,
            "act_stage": edit_act_stage,
            "act_times": edit_act_times,
            "scr": edits_scr,
            "prefix": prefix,
        }

    def _labeled_edit_cell(self, label: str, edit: QWidget) -> QWidget:
        """上标签下输入框的小格。"""
        cell = QWidget(self)
        cl = QVBoxLayout(cell)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(2)
        lab = QLabel(label, cell)
        lab.setStyleSheet('font-family:"Microsoft YaHei";font-size:12px;color:#334;')
        cl.addWidget(lab, 0, Qt.AlignLeft)
        cl.addWidget(edit, 0, Qt.AlignLeft)
        return cell

    def _clear_v_note(self, sec: "Section", title_txt: str, *rows):
        """上文字下控件的竖排便签。"""
        n = NoteCell(title_txt, self)
        host = QWidget(self)
        vl = QVBoxLayout(host)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)
        vl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        for row in rows:
            vl.addWidget(row, 0, Qt.AlignLeft)
        n.set_widget(host)
        try:
            n.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        except Exception:
            pass
        sec.add_note(n)
        return n

    def _clear_h_note(self, sec: "Section", title_txt: str, *cells):
        """便签内控件左右并列。"""
        n = NoteCell(title_txt, self)
        host = QWidget(self)
        hl = QHBoxLayout(host)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        hl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        for cell in cells:
            hl.addWidget(cell, 0, Qt.AlignTop)
        hl.addStretch(1)
        n.set_widget(host)
        try:
            n.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        except Exception:
            pass
        sec.add_note(n)
        return n

    def _build_scrimmage_row(self, sec: "Section", with_manual: bool):
        """交流会三校次数行；可选右侧「手动清」开关。"""
        edits_scr = {}
        scr_rows = []
        for lab_t, key in (
            ("圣三一", "trinity"),
            ("千禧年", "millennium"),
            ("歌赫娜", "gehenna"),
        ):
            e = self._mk_count_edit("0/-1", 56)
            edits_scr[key] = e
            scr_rows.append(self._labeled_edit_cell(lab_t, e))
        n_scr = NoteCell("交流会", self)
        try:
            # 标题旁短说明
            n_scr.title.setText("交流会　请根据票数调整")
        except Exception:
            pass
        host = QWidget(self)
        hl2 = QHBoxLayout(host)
        hl2.setContentsMargins(0, 0, 0, 0)
        hl2.setSpacing(10)
        for w in scr_rows:
            hl2.addWidget(w, 0, Qt.AlignTop)
        hl2.addStretch(1)
        n_scr.set_widget(host)
        try:
            n_scr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        except Exception:
            pass
        manual_sw = None
        if with_manual:
            row_scr = QWidget(self)
            rsl = QHBoxLayout(row_scr)
            rsl.setContentsMargins(0, 0, 0, 0)
            rsl.setSpacing(10)
            rsl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            rsl.addWidget(n_scr, 0, Qt.AlignTop)
            manual_sw = SwitchButton(self)
            try:
                manual_sw.setOnText("开")
                manual_sw.setOffText("关")
            except Exception:
                pass
            manual_sw.setToolTip("开启后，到花体时刻买完体再按本栏扫荡并领邮续清")
            man_note = NoteCell("手动清", self, switch_box=True)
            man_note.set_widget(manual_sw)
            try:
                man_note.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            except Exception:
                pass
            rsl.addWidget(man_note, 0, Qt.AlignTop)
            rsl.addStretch(1)
            try:
                row_scr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            except Exception:
                pass
            if getattr(sec, "_use_flow", True):
                sec._flow.addWidget(row_scr, 0, Qt.AlignLeft | Qt.AlignTop)
            else:
                sec.col.addWidget(row_scr, 0, Qt.AlignLeft | Qt.AlignTop)
        else:
            sec.add_note(n_scr)
        return edits_scr, manual_sw

    def _wire_clear_block(self, blk: dict) -> None:
        pfx = blk["prefix"]
        mapping = [
            (blk["main_normal"], "hoard_ap_%s_main_normal" % pfx),
            (blk["main_hard"], "hoard_ap_%s_main_hard" % pfx),
            (blk["sp_exp"], "hoard_ap_%s_special_exp" % pfx),
            (blk["sp_money"], "hoard_ap_%s_special_money" % pfx),
            (blk["act_stage"], "hoard_ap_%s_activity_stage" % pfx),
            (blk["act_times"], "hoard_ap_%s_activity_times" % pfx),
            (blk["scr"]["trinity"], "hoard_ap_%s_scr_trinity" % pfx),
            (blk["scr"]["millennium"], "hoard_ap_%s_scr_millennium" % pfx),
            (blk["scr"]["gehenna"], "hoard_ap_%s_scr_gehenna" % pfx),
        ]
        for e, k in mapping:
            self._bind(e, k)
        if blk.get("manual") is not None:
            blk["manual"].checkedChanged.connect(
                lambda v: self._save("hoard_ap_spend_manual", bool(v))
            )
            blk["manual"].checkedChanged.connect(
                lambda v: self._save("hoard_ap_spend_auto_clear", bool(v))
            )

    def _load_clear_block(self, blk: dict) -> None:
        c = self.config
        pfx = blk["prefix"]
        pairs = [
            (blk["main_normal"], "hoard_ap_%s_main_normal" % pfx, ""),
            (blk["main_hard"], "hoard_ap_%s_main_hard" % pfx, ""),
            (blk["sp_exp"], "hoard_ap_%s_special_exp" % pfx, "0"),
            (blk["sp_money"], "hoard_ap_%s_special_money" % pfx, "0"),
            (blk["act_stage"], "hoard_ap_%s_activity_stage" % pfx, "1"),
            (blk["act_times"], "hoard_ap_%s_activity_times" % pfx, "0"),
            (blk["scr"]["trinity"], "hoard_ap_%s_scr_trinity" % pfx, "0"),
            (blk["scr"]["millennium"], "hoard_ap_%s_scr_millennium" % pfx, "0"),
            (blk["scr"]["gehenna"], "hoard_ap_%s_scr_gehenna" % pfx, "0"),
        ]
        legacy_fill = False
        if pfx == "overnight":
            if not any(str(_cfg_get(c, k, "") or "").strip() for _, k, _ in pairs[:2]):
                legacy_fill = True
        for e, k, d in pairs:
            val = _as_str(_cfg_get(c, k, d) or d)
            if legacy_fill and pfx == "overnight":
                if k.endswith("main_normal"):
                    val = _as_str(_cfg_get(c, "mainlinePriority", "") or val)
                elif k.endswith("main_hard"):
                    val = _as_str(_cfg_get(c, "hardPriority", "") or val)
                elif k.endswith("special_exp"):
                    raw = _as_str(_cfg_get(c, "special_task_times", "0,0") or "0,0")
                    parts = [x.strip() for x in raw.replace("，", ",").split(",")]
                    val = parts[0] if parts else "0"
                elif k.endswith("special_money"):
                    raw = _as_str(_cfg_get(c, "special_task_times", "0,0") or "0,0")
                    parts = [x.strip() for x in raw.replace("，", ",").split(",")]
                    val = parts[1] if len(parts) > 1 else "0"
                elif k.endswith("activity_stage"):
                    val = _as_str(_cfg_get(c, "activity_sweep_task_number", "1") or "1")
                elif k.endswith("activity_times"):
                    val = _as_str(_cfg_get(c, "activity_sweep_times", "0") or "0")
                elif k.endswith("scr_trinity"):
                    raw = _as_str(_cfg_get(c, "scrimmage_times", "0,0,0") or "0,0,0")
                    parts = [x.strip() for x in raw.replace("，", ",").split(",")]
                    val = parts[0] if parts else "0"
                elif k.endswith("scr_millennium"):
                    raw = _as_str(_cfg_get(c, "scrimmage_times", "0,0,0") or "0,0,0")
                    parts = [x.strip() for x in raw.replace("，", ",").split(",")]
                    val = parts[1] if len(parts) > 1 else "0"
                elif k.endswith("scr_gehenna"):
                    raw = _as_str(_cfg_get(c, "scrimmage_times", "0,0,0") or "0,0,0")
                    parts = [x.strip() for x in raw.replace("，", ",").split(",")]
                    val = parts[2] if len(parts) > 2 else "0"
            try:
                e.setText(val)
            except Exception:
                pass
        if blk.get("manual") is not None:
            on = _cfg_get(c, "hoard_ap_spend_manual", None)
            if on is None or str(on).strip() == "":
                on = _as_bool(_cfg_get(c, "hoard_ap_spend_auto_clear", False), False)
            else:
                on = _as_bool(on, False)
            self._set_switch(blk["manual"], bool(on))

    def _build_clear_panels(self) -> None:
        # 两大框上下叠放；每个大框内部小便签左右流式
        self._overnight_blk = self._build_clear_block(
            title="多自回清体力",
            tip="邮箱堆到 980+ 后，为近 23 小时自回，4 点扫哪里。先清有限次数本；-1 为无限。",
            prefix="overnight",
            with_manual=False,
            notes_horizontal=True,
        )
        self._wire_clear_block(self._overnight_blk)

        self._spend_blk = self._build_clear_block(
            title="到点清体力",
            tip="开「手动清」后，到花体时刻买完体再按本栏扫荡领邮续清。与上方多自回独立。",
            prefix="spend",
            with_manual=True,
            notes_horizontal=True,
        )
        self._wire_clear_block(self._spend_blk)
        self.sw_spend_clear = self._spend_blk.get("manual")
        self.edit_main_normal = self._spend_blk["main_normal"]
        self.edit_main_hard = self._spend_blk["main_hard"]
        self.edit_sp = self._spend_blk["sp_exp"]
        self.edit_act_stage = self._spend_blk["act_stage"]
        self.edit_act_times = self._spend_blk["act_times"]
        self.edit_scr = self._spend_blk["scr"]["trinity"]
        # 困难/普通优先级：editingFinished 保存，否则改了不存、计划用旧值
        try:
            self.edit_main_hard.editingFinished.connect(
                lambda: self._save("hardPriority", self.edit_main_hard.text().strip())
            )
            self.edit_main_normal.editingFinished.connect(
                lambda: self._save("mainlinePriority", self.edit_main_normal.text().strip())
            )
        except Exception:
            pass

        col = QWidget(self)
        cl = QVBoxLayout(col)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(12)
        cl.setAlignment(Qt.AlignTop)
        for blk in (self._overnight_blk, self._spend_blk):
            try:
                blk["sec"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                blk["sec"].setMaximumWidth(16777215)
            except Exception:
                pass
            cl.addWidget(blk["sec"], 0, Qt.AlignTop)
        self.body.addWidget(col)

    def _make_header_setting_cell(self, title: str, widget: QWidget, min_w: int = 0) -> QFrame:
        """顶栏设置开关：四页统一实现（tool_style.make_header_setting_cell）。"""
        from gui.components.expand.tool_style import make_header_setting_cell

        return make_header_setting_cell(
            title, widget, obj_name="hoardHeaderSetting", min_w=min_w
        )

    def header_settings_widgets(self):
        """供 ToolsFragment 挂到「名称右侧」设置区（纯设置 + 栏位单选）。"""
        cells = list(getattr(self, "_header_settings_cells", []) or [])
        # 主页栏位单选（第一栏=标题下 / 第二栏=启停下），紧邻开关右侧
        try:
            from gui.components.expand.tool_style import make_home_bar_slot_cell
            _slot = make_home_bar_slot_cell("hoard_ap")
            if _slot is not None:
                cells.append(_slot)
        except Exception:
            pass
        return cells

    def _refresh_home_plugins(self) -> None:

        try:
            c = self.config
            win = c.get_window() if c is not None and hasattr(c, "get_window") else None
            if win is None:
                return
            for h in getattr(win, "_sub_list", [[]])[0]:
                if getattr(h, "config", None) is c and hasattr(h, "refresh_home_plugins"):
                    h.refresh_home_plugins()
        except Exception as e:
            print("[hoard] refresh home failed:", e)

    def sizeHint(self):
        try:
            h = max(360, int(self.minimumSizeHint().height()))
        except Exception:
            h = PAGE_H
        try:
            w = max(480, min(CONTENT_MAX_W, int(self.width() or CONTENT_MAX_W)))
        except Exception:
            w = CONTENT_MAX_W
        return QSize(w, h)

    def minimumSizeHint(self):
        return QSize(480, 360)

    def _sync_claimed_height(self):
        """已领小框高度与「当前体力/咖啡可领」行大致平齐（同在现状内）。"""
        try:
            cl = getattr(self, "_sec_claimed", None)
            ap = getattr(self, "edit_current_ap", None)
            if cl is None or ap is None:
                return
            # 邮箱明细会更高；已领只对齐上排小框高度，不硬撑整段现状
            target = max(int(ap.sizeHint().height()) + 36, 96)
            cl.setMinimumHeight(target)
        except Exception:
            pass

    def _fit(self):
        try:
            # 宽度：以滚动视口为唯一真源（自动排除竖滚动条宽度）。
            # 扣除量 34 = Section 左右内边距 16×2 + 左右边框 1×2 —— 计划框
            # 右缘到大框边框的距离与左侧完全相等；竖滚动条出现/消失由
            # rangeChanged 兜底重算，不会横向溢出
            try:
                pw = int(self._scroll.viewport().width()) if getattr(self, "_scroll", None) is not None else 0
            except Exception:
                pw = 0
            vw = max(240, pw - 34) if pw > 0 else 480
            self.txt_plan.setFixedWidth(vw)
            doc = self.txt_plan.document()
            doc.setTextWidth(float(vw - 16))
            try:
                self.txt_plan.setLineWrapMode(self.txt_plan.WidgetWidth)
                self.txt_plan.setWordWrapMode(1)
            except Exception:
                pass
            # 高度：按文档 idealHeight，外加一点 padding；长文上限交给外层 scroll
            h = int(doc.size().height()) + 24
            plain = ""
            try:
                plain = self.txt_plan.toPlainText() or ""
            except Exception:
                plain = ""
            if not plain.strip():
                h = 160
            h = max(120, min(h, 20000))
            self.txt_plan.setMinimumHeight(h)
            self.txt_plan.setMaximumHeight(h)
            self.txt_plan.setFixedHeight(h)
            self.txt_plan.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.txt_plan.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            try:
                sb = self.txt_plan.verticalScrollBar()
                if sb is not None:
                    sb.setEnabled(False)
                    sb.setValue(0)
                    sb.hide()
            except Exception:
                pass
            # 触发布局收缩，去掉 Section 多余空白
            try:
                self.txt_plan.updateGeometry()
                if getattr(self, "_scroll", None) is not None and self._scroll.widget():
                    self._scroll.widget().adjustSize()
                    self._scroll.widget().updateGeometry()
                self.updateGeometry()
            except Exception:
                pass
        except Exception:
            pass

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit()
        self._sync_claimed_height()

    def _upd_strategy(self, *_):
        t = (self.edit_tubes.text() or "").strip()
        d = (self.edit_tube_days.text() or "").strip() or "2"
        try:
            n = int(t) if t else 0
            days = max(0, min(3, int(d)))
        except ValueError:
            n, days = 0, 2
        if t == "":
            self.lbl_strategy.setText("自动估上限·勤奋")
        elif n <= 0:
            self.lbl_strategy.setText("懒人（不买管）")
        else:
            self.lbl_strategy.setText("勤奋 上限%d管(按缺口)" % n)

    def _on_jjc(self, keys):
        keys = set(keys or [])
        if "30" in keys and "60" in keys:
            mode = "30_60"
        elif "30" in keys:
            mode = "30"
        elif "60" in keys:
            mode = "30_60"
        else:
            mode = "none"
        self._save("hoard_ap_jjc_buy_mode", mode)
        self._upd_jjc()
        try:
            from module.hoard_ap.planner import apply_jjc_to_shop_config

            ref = int(self.edit_jjc_refresh.text().strip() or "0")
            apply_jjc_to_shop_config(self.config, mode, ref)
        except Exception:
            pass

    def _on_gift_card(self, key, checked):
        if checked:
            if key == "0":
                # 点 0：立刻清掉 130/150 的复选
                self.gift_row.set_selected(["0"])
            else:
                # 点 130/150：立刻清掉 0（可继续复选另一个）
                keys = [k for k in self.gift_row.selected_keys() if k != "0"]
                self.gift_row.set_selected(keys)
        else:
            keys = self.gift_row.selected_keys()
            if not keys:
                self.gift_row.set_selected(["0"])
        keys = [str(k) for k in self.gift_row.selected_keys() if str(k)]
        val = "+".join(keys) if keys != ["0"] else "0"
        self._save("hoard_ap_card_amount", val)
        self._save("hoard_ap_use_ap_card", val not in ("", "0"))

    def _upd_jjc(self, *_):
        keys = set(self.jjc_row.selected_keys())
        try:
            ref = max(0, min(3, int(self.edit_jjc_refresh.text().strip() or "0")))
        except ValueError:
            ref = 0
        per = (30 if "30" in keys else 0) + (60 if "60" in keys else 0)
        # 只显示数量（如 360），不要「每天」
        self.lbl_jjc.setText(str(per * (ref + 1)) if per > 0 else "0")

    def _popup_cal(self):
        today = QDate.currentDate()
        cur = today.addDays(2)
        text = self.edit_date.text().strip()
        if text:
            p = text.replace("/", "-").split("-")
            if len(p) == 3:
                cur = QDate(int(p[0]), int(p[1]), int(p[2]))
        pop = _CalendarPopup(self, current=max(cur, today), minimum=today)
        pop.move(self.btn_cal.mapToGlobal(QPoint(0, self.btn_cal.height())))
        if pop.exec_():
            qd = pop.chosen()
            s = "%04d-%02d-%02d" % (qd.year(), qd.month(), qd.day())
            self.edit_date.setText(s)
            self._save("hoard_ap_target_date", s)


    def _set_switch(self, sw, on: bool):
        """设置开关并强制 polish，避免首次圆点贴边。"""
        try:
            sw.blockSignals(True)
        except Exception:
            pass
        try:
            sw.setChecked(bool(on))
        except Exception:
            pass
        try:
            sw.blockSignals(False)
        except Exception:
            pass
        self._polish_switch(sw)

    def _polish_switch(self, sw):
        try:
            from PyQt5.QtWidgets import QApplication
            sw.style().unpolish(sw)
            sw.style().polish(sw)
            sw.update()
            # 再延迟一帧
            QTimer.singleShot(0, sw.update)
            QTimer.singleShot(30, sw.update)
        except Exception:
            pass

    def _on_claimed_switch(self, key, v, sw=None):
        self._save(key, bool(v))
        # 同步旧键
        if key == "hoard_ap_lesson_claimed":
            self._save("hoard_ap_lesson_ready", (not bool(v)))
        # 事实来源：inventory
        try:
            from module.hoard_ap.data_service import InventoryService

            srv = InventoryService(self._config_dir())
            kw = {}
            if key == "hoard_ap_task_claimed":
                kw["task"] = bool(v)
            elif key == "hoard_ap_lesson_claimed":
                kw["lesson"] = bool(v)
            elif key == "hoard_ap_jjc_claimed":
                kw["jjc"] = bool(v)
            elif key == "hoard_ap_group_claimed":
                kw["group"] = bool(v)
            elif key == "hoard_ap_free_buy_claimed":
                kw["free_buy"] = bool(v)
            if kw:
                srv.set_claimed(**kw, cfg=self.config)
        except Exception:
            pass
        if sw is not None:
            self._polish_switch(sw)

    def _hoard_should_project(self) -> bool:
        """仅启用 + 有运行计划时才推算咖啡/邮 remaining，否则彻底停表省资源。"""
        try:
            if not bool(self.sw_enabled.isChecked()):
                return False
        except Exception:
            return False
        try:
            from module.hoard_ap.state import load_state
            from module.hoard_ap.constants import PHASE_IDLE, PHASE_DONE, PHASE_ABORTED

            st = load_state(self._config_dir())
            if not st.plan or not (st.plan.get("steps") or []):
                return False
            if str(st.phase or "") in (PHASE_IDLE, PHASE_DONE, PHASE_ABORTED, ""):
                # Idle 且无活跃步骤：不推
                # 有计划但 idle（刚算完未开）仍可推显示；用户明确要求关闭/无计划才断
                pass
            return True
        except Exception:
            return False

    def _sync_proj_timer(self) -> None:
        """按启用/计划状态启停 30s 推算定时器。"""
        timer = getattr(self, "_proj_timer", None)
        if timer is None:
            return
        try:
            if self._hoard_should_project():
                if not timer.isActive():
                    timer.start()
            else:
                if timer.isActive():
                    timer.stop()
        except Exception:
            pass

    def _tick_project(self):
        """按 inventory 快照推算：咖啡可领随时间涨；邮箱 remain 扣减；仅刷新显示不打断编辑。"""
        # 关闭 / 无计划：彻底不推，省资源
        if not self._hoard_should_project():
            self._sync_proj_timer()
            return
        try:
            if self.edit_mail_detail.hasFocus() or self.edit_cafe_claimable.hasFocus():
                return
            if self.edit_current_ap.hasFocus() or self.edit_mail_ap.hasFocus():
                return
        except Exception:
            pass
        try:
            from module.hoard_ap.inventory import load_inventory, project_display, format_mail_bags_input
            inv = load_inventory(self._config_dir())
            if not inv.snapped_at and not inv.mail_scanned_at:
                return
            disp = project_display(inv)
            # 咖啡：有快照才推
            if inv.snapped_at:
                cafe = int(disp.get("cafe_claimable") or 0)
                # 用户刚手改过则仍显示推算（手改会重写 snapped_at）
                cur_c = self.edit_cafe_claimable.text().strip()
                if cur_c != str(cafe):
                    self.edit_cafe_claimable.blockSignals(True)
                    self.edit_cafe_claimable.setText(str(cafe))
                    self.edit_cafe_claimable.blockSignals(False)
                ap = int(disp.get("current_ap") or 0)
                if self.edit_current_ap.text().strip() != str(ap):
                    # 仅当低于软顶时推算才变
                    self.edit_current_ap.blockSignals(True)
                    self.edit_current_ap.setText(str(ap))
                    self.edit_current_ap.blockSignals(False)
            bags = list(disp.get("mail_bags") or [])
            if bags:
                self._mail_bags = bags
                txt = format_mail_bags_input(bags)
                cur = self._mail_detail_text().replace(" ", "")
                if cur.replace("\n", ",") != (txt or "").replace(" ", ""):
                    self._set_mail_detail_text(txt)
                total = int(disp.get("mail_ap") or 0)
                if self.edit_mail_ap.text().strip() != str(total):
                    self.edit_mail_ap.blockSignals(True)
                    self.edit_mail_ap.setText(str(total))
                    self.edit_mail_ap.blockSignals(False)
                self.lbl_mail.setText(" + ".join("%s" % int(b.get("amount") or 0) for b in bags))
            # 执行后自动刷新时间轴✓（无需点计算计划）
            try:
                self._refresh_plan_view(silent=True)
            except Exception:
                pass
        except Exception:
            pass

    def _resnap_inventory_from_form(self):
        """用户改了现状数字 → 重写 inventory 基准时刻。"""
        try:
            from module.hoard_ap.inventory import snapshot_from_form, save_inventory
            bags = self._parse_bags(self._mail_detail_text()) or list(self._mail_bags)
            mail_total = self.edit_mail_ap.text().strip()
            if bags and not mail_total:
                mail_total = str(sum(int(b.get("amount") or 0) for b in bags))
            inv = snapshot_from_form(
                current_ap=int(float(self.edit_current_ap.text() or 0) or 0),
                mail_ap=int(float(mail_total or 0) or 0),
                cafe_claimable=int(float(self.edit_cafe_claimable.text() or 0) or 0),
                soft_cap=int(float(self.edit_soft.text() or 160) or 160),
                cafe_cap=float(self.edit_cafe_cap.text() or 740),
                task_claimed=bool(self.sw_task.isChecked()),
                lesson_claimed=bool(self.sw_lesson.isChecked()),
                jjc_claimed=bool(self.sw_jjc.isChecked()),
                group_claimed=bool(self.sw_group.isChecked()),
                free_buy_claimed=bool(self.sw_free.isChecked()),
                mail_bags=bags,
            )
            save_inventory(self._config_dir(), inv)
        except Exception as e:
            # 「已领」开关没写进账本=界面与执行态脱节，必须留痕
            print("[hoard_ap] 已领开关写账本失败:", e)

    @staticmethod
    def _parse_remain_hours(text):
        """@后的持续时间：数字=小时；d6 / 6d / 6天 = 天数（1天=24h）。

        与输入提示「如10@d6为这个10体力持续6天」保持一致，
        解析失败返回 None（调用方丢弃该条）。
        """
        s = str(text or "").strip().lower().replace("天", "d")
        if not s:
            return None
        try:
            if s.startswith("d"):  # d6 → 6 天
                return float(s[1:]) * 24.0
            if s.endswith("d"):  # 6d → 6 天
                return float(s[:-1]) * 24.0
            return float(s)
        except ValueError:
            return None

    def _parse_bags(self, text):
        bags = []
        raw = (text or "").replace("，", ",").replace("\n", ",").replace("\r", ",").replace(" ", "")
        for part in raw.split(","):
            if not part:
                continue
            if "@" in part:
                a, h = part.split("@", 1)
                hours = self._parse_remain_hours(h)
                try:
                    if hours is None:
                        continue
                    bags.append({"amount": int(a), "remain_hours": hours, "source": "manual"})
                except ValueError:
                    pass
            else:
                try:
                    bags.append({"amount": int(part), "remain_hours": 23.0, "source": "manual"})
                except ValueError:
                    pass
        return bags

    def _on_mail_detail(self):
        had_bags = bool(self._mail_bags)
        bags = self._parse_bags(self._mail_detail_text())
        self._mail_bags = bags
        try:
            self._save("hoard_ap_mail_bags_json", json.dumps(bags, ensure_ascii=False))
        except Exception:
            pass
        if not bags and had_bags:
            # 明细被清空 → 总量必须归零（以明细之和为唯一邮箱总量），
            # 否则旧合计会继续参与计划，制造并不存在的「幽灵邮件」。
            # 仅「原有明细被清空」时触发；本来就没明细的旧版总量快照不受影响。
            self.edit_mail_ap.setText("0")
            self._save("hoard_ap_mail_ap", "0")
            self.lbl_mail.setText("")
            try:
                from module.hoard_ap.data_service import InventoryService

                InventoryService(self._config_dir()).set_mail(
                    mail_ap=0, mail_bags=[], cfg=self.config
                )
            except Exception:
                pass
            return
        if bags:
            total = sum(int(b["amount"]) for b in bags)
            self.edit_mail_ap.setText(str(total))
            self._save("hoard_ap_mail_ap", str(total))
            # 算式单行
            self.lbl_mail.setText(" + ".join("%s" % b["amount"] for b in bags))
            # 明细折两行回写显示
            try:
                self._set_mail_detail_text(
                    ",".join(
                        "%s@%s"
                        % (
                            int(b.get("amount") or 0),
                            ("%.1f" % float(b.get("remain_hours") or 0)).rstrip("0").rstrip(".")
                            if b.get("remain_hours") is not None
                            else "23",
                        )
                        for b in bags
                        if int(b.get("amount") or 0) > 0
                    )
                )
            except Exception:
                pass
        else:
            self.lbl_mail.setText("")
        self._resnap_inventory_from_form()

    def _busy(self):
        return self._worker is not None and self._worker.isRunning()

    def _config_dir(self):
        """解析当前配置目录（必须能写到 config/<名>/event.json）。"""
        c = self.config
        cands = []
        try:
            if getattr(c, "config_dir", None):
                cands.append(str(c.config_dir))
        except Exception:
            pass
        try:
            cs = getattr(c, "config_set", None)
            if cs is not None and getattr(cs, "config_dir", None):
                cands.append(str(cs.config_dir))
        except Exception:
            pass
        try:
            if getattr(c, "config_path", None):
                cands.append(str(c.config_path))
        except Exception:
            pass
        for d in cands:
            if not d:
                continue
            d = os.path.abspath(d)
            # 目录本身含 config.json / event.json
            if os.path.isfile(os.path.join(d, "config.json")) or os.path.isfile(
                os.path.join(d, "event.json")
            ):
                return d
            # 有时传的是文件路径
            if os.path.isfile(d) and d.endswith(".json"):
                return os.path.dirname(d)
        # 最后兜底：相对 ./config 下找
        try:
            name = None
            for attr in ("name", "config_name", "user_config_dir"):
                v = getattr(c, attr, None)
                if v:
                    name = str(v)
                    break
            if name:
                rel = os.path.abspath(os.path.join("config", name))
                if os.path.isdir(rel):
                    return rel
        except Exception:
            pass
        return cands[0] if cands else os.path.abspath(".")

    def _on_mail_ocr(self):
        if self._busy():
            return
        from module.hoard_ap.runtime_ui import require_baas_for_ocr, run_mail_ocr_on_baas

        baas, err = require_baas_for_ocr(self.config)
        if err:
            notification.error("囤体", err, self.config)
            self.lbl_mail.setText(err)
            return
        cfg = self._config_dir()

        def job(st):
            st("识别中…")
            try:
                return run_mail_ocr_on_baas(baas, cfg)
            except Exception as e:
                return {"ok": False, "error": f"识别异常: {e}"}

        self._worker = _Worker(job, self)

        def ok(scan):
            if not isinstance(scan, dict) or not scan.get("ok"):
                notification.error(
                    "囤体",
                    "识别失败：%s" % ((scan or {}).get("error") if isinstance(scan, dict) else ""),
                    self.config,
                )
                return
            bags = list(scan.get("bags") or [])
            total = int(scan.get("total") or 0)
            pages = int(scan.get("pages") or 1)
            self._mail_bags = bags
            self.edit_mail_ap.setText(str(total))
            self._save("hoard_ap_mail_ap", str(total))
            try:
                self.edit_mail_detail.setEnabled(True)
                self.edit_mail_detail.setReadOnly(False)
            except Exception:
                pass
            self._set_mail_detail_text(
                ",".join(
                    "%s@%s"
                    % (
                        b.get("amount"),
                        ("%.1f" % float(b.get("remain_hours") or 0)).rstrip("0").rstrip("."),
                    )
                    for b in bags
                )
            )
            self._on_mail_detail()
            msg = "识别 %d 包，合计 %d（扫 %d 页）" % (len(bags), total, pages)
            if len(bags) <= 1 and total > 0:
                msg += "；若还有邮件请再点一次或手填明细"
            notification.success("囤体", msg, self.config)

        self._worker.ok.connect(ok)
        self._worker.fail.connect(lambda e: notification.error("囤体", e, self.config))
        self._worker.status.connect(self.lbl_mail.setText)
        self._worker.start()

    def _on_pick_daily(self):
        """截图点选：打开任务页→截屏→在弹窗图上点「每日」→写入坐标。"""
        if self._busy():
            return
        from module.hoard_ap.runtime_ui import require_running_baas
        from module.hoard_ap.task_daily import save_daily_tab_xy

        baas, err = require_running_baas(self.config)
        if err:
            notification.error("囤体", err, self.config)
            self.lbl_pick.setText(err)
            return
        cfg = self._config_dir()
        self.lbl_pick.setText("截图中…")

        def job(st):
            st("打开任务页并截图…")
            try:
                baas.to_main_page()
            except Exception:
                pass
            try:
                from module.collect_daily_task_power import to_tasks
                try:
                    to_tasks(baas, True)
                except TypeError:
                    to_tasks(baas)
            except Exception:
                try:
                    from module.collect_reward import to_tasks
                    to_tasks(baas)
                except Exception:
                    pass
            import time as _t
            _t.sleep(0.6)
            try:
                baas.latest_img_array = baas.get_screenshot_array()
            except Exception:
                pass
            img = getattr(baas, "latest_img_array", None)
            if img is None:
                raise RuntimeError("截图失败")
            # 转成 PNG bytes 供 UI 线程显示
            import numpy as np
            arr = np.asarray(img)
            return {"arr_shape": list(arr.shape), "arr": arr}

        self._worker = _Worker(job, self)

        def ok(payload):
            try:
                arr = payload.get("arr")
                pos = self._pick_on_image(arr)
                if not pos:
                    self.lbl_pick.setText("已取消")
                    return
                x, y = int(pos[0]), int(pos[1])
                save_daily_tab_xy(cfg, x, y)
                self.edit_daily_xy.setText("%d,%d" % (x, y))
                self._save("hoard_ap_task_daily_tab_xy", "%d,%d" % (x, y))
                self.lbl_pick.setText("%d,%d" % (x, y))
                try:
                    baas.logger.info("[囤体] 每日位置截图点选 (%s,%s)" % (x, y))
                except Exception:
                    pass
                notification.success("囤体", "每日 (%d,%d)" % (x, y), self.config)
            except Exception as e:
                self.lbl_pick.setText(str(e))
                notification.error("囤体", str(e), self.config)

        self._worker.ok.connect(ok)
        self._worker.fail.connect(
            lambda e: (self.lbl_pick.setText(str(e)), notification.error("囤体", str(e), self.config))
        )
        self._worker.status.connect(self.lbl_pick.setText)
        self._worker.start()

    def _pick_on_image(self, arr):
        """弹出截图，单击返回游戏坐标 (x,y)。"""
        import numpy as np
        from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout

        a = np.asarray(arr)
        if a.ndim == 2:
            h, w = a.shape
            qimg = QImage(a.data, w, h, w, QImage.Format_Grayscale8).copy()
        else:
            h, w = a.shape[:2]
            if a.shape[2] >= 3:
                # BAAS 常见 BGR
                rgb = a[:, :, :3][:, :, ::-1].copy()
                bytes_per = rgb.strides[0]
                qimg = QImage(rgb.data, w, h, bytes_per, QImage.Format_RGB888).copy()
            else:
                return None

        class _Img(QLabel):
            def __init__(self, pm, parent=None):
                super().__init__(parent)
                self._pm0 = pm
                self._chosen = None
                self.setPixmap(pm)
                self.setFixedSize(pm.size())

            def mousePressEvent(self, e):
                if e.button() == Qt.LeftButton:
                    self._chosen = (e.x(), e.y())
                    pm = QPixmap(self._pm0)
                    p = QPainter(pm)
                    p.setPen(QPen(QColor(255, 64, 64), 3))
                    x, y = self._chosen
                    p.drawEllipse(x - 8, y - 8, 16, 16)
                    p.drawLine(x - 12, y, x + 12, y)
                    p.drawLine(x, y - 12, x, y + 12)
                    p.end()
                    self.setPixmap(pm)

        dlg = QDialog(self)
        dlg.setWindowTitle("点选「每日」页签中心")
        dlg.setModal(True)
        lay = QVBoxLayout(dlg)
        tip = QLabel("在图上单击任务页顶部的「每日」文字中心，再点确定。", dlg)
        tip.setStyleSheet("color:#333;font-size:12px;")
        lay.addWidget(tip)
        # 缩放到最大 960 宽
        pm = QPixmap.fromImage(qimg)
        scale = 1.0
        if pm.width() > 960:
            scale = 960.0 / pm.width()
            pm = pm.scaledToWidth(960, Qt.SmoothTransformation)
        img = _Img(pm, dlg)
        lay.addWidget(img, 0, Qt.AlignCenter)
        row = QHBoxLayout()
        btn_ok = PushButton("确定", dlg)
        btn_cancel = PushButton("取消", dlg)
        row.addStretch(1)
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)
        lay.addLayout(row)
        btn_cancel.clicked.connect(dlg.reject)
        btn_ok.clicked.connect(dlg.accept)
        if dlg.exec_() != QDialog.Accepted or not img._chosen:
            return None
        sx, sy = img._chosen
        gx = int(round(sx / scale))
        gy = int(round(sy / scale))
        return gx, gy


    def _build_plan_head(self, duty, plan_obj, rep_notes=None) -> str:
        """精简值守 + 已完成清单（不再输出补做 key 长串）。"""
        from module.hoard_ap.execution_log import format_log_section
        from module.hoard_ap.narrative import _fmt, _human_delta, _parse_when
        from datetime import datetime as _dt

        now = _dt.now().replace(second=0, microsecond=0)
        head = []
        summary_lines = list((duty or {}).get("summary") or [])
        # 终点三件套并入花体行
        final_ap = final_mail = cafe = total = None
        try:
            sm = getattr(plan_obj, "summary", None) or {}
            if isinstance(sm, dict):
                final_ap = sm.get("final_ap")
                final_mail = sm.get("final_mail")
                cafe = sm.get("cafe_at_spend")
                if final_ap is not None and final_mail is not None:
                    total = int(final_ap) + int(final_mail) + int(cafe or 0)
        except Exception:
            pass
        spend = getattr(plan_obj, "spend_at", None)
        spend_dt = _parse_when(spend) if not isinstance(spend, _dt) else spend
        for line in summary_lines[:6]:
            s = str(line)
            if s.startswith("花体时刻") and spend_dt is not None and total is not None:
                s = (
                    f"花体时刻（请本人在）：{_fmt(spend_dt)}"
                    f"（还有{_human_delta((spend_dt - now).total_seconds())}）"
                    f"终点约 体{final_ap} + 邮{final_mail} + 咖啡{cafe or 0} ＝ {total}"
                )
            head.append("· " + s)
        # 不展示 rep_notes / 补做 key
        log = format_log_section(self._config_dir(), limit=12)
        head.append("")
        head.append("【已完成清单，✓为已完成项目】")
        if log and "尚无" not in log:
            head.append(log)
        else:
            head.append("  （还没有成功执行记录）")
        return "\n".join(head)

    def _load_plan(self):
        """打开页面只读已保存说明，绝不在此刻重算/改写步骤时间。

        以前 silent 调 _refresh_plan_view 会跑 apply_replan，把过点步骤
        改成「补做 now」，看起来像每次打开都更新日期。
        """
        # 1) 优先读上次落盘的说明文本（用户可见的原文）
        p = os.path.join(self._config_dir(), "hoard_ap_plan.txt")
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    text = f.read()
                if text and str(text).strip():
                    self.txt_plan.setPlainText(text)
                    try:
                        self._fit()
                    except Exception:
                        pass
                    return
            except Exception:
                pass
        # 2) 没有 txt 时，用 state.plan 做「只读」渲染（不 replan、不改 when）
        try:
            if self._render_saved_plan_readonly():
                return
        except Exception:
            pass

    def _render_saved_plan_readonly(self) -> bool:
        """用磁盘上的 state.plan 生成展示，不调用 apply_replan，不写回 state。"""
        try:
            from module.hoard_ap.state import load_state
            from module.hoard_ap.execution_log import done_actions
            from module.hoard_ap.replan import _compute_done_key, build_duty_sections
            from module.hoard_ap.narrative import render_plan_narrative, _parse_when
            from module.hoard_ap.planner import HoardPlan, HoardConfig
            from datetime import datetime as _dt

            st = load_state(self._config_dir())
            plan_dict = dict((st.plan or {}) if isinstance(st.plan, dict) else {})
            if not plan_dict.get("steps"):
                return False
            done = list(done_actions(self._config_dir()) or [])
            done_set = set(done)
            done_at_map = {}
            try:
                from module.hoard_ap.execution_log import load_log
                for e in load_log(self._config_dir()):
                    if not e.ok:
                        continue
                    k = str((e.meta or {}).get("done_key") or "").strip()
                    if k and e.when:
                        done_at_map[k] = e.when
            except Exception:
                pass
            # 仅打✓，不改 when / 不补做
            steps_out = []
            for s in plan_dict.get("steps") or []:
                s = dict(s) if isinstance(s, dict) else s
                if not isinstance(s, dict):
                    continue
                try:
                    k = _compute_done_key(s)
                    md = dict(s.get("meta") or {})
                    if k in done_set or md.get("done_ok") or s.get("done_ok"):
                        md["done_ok"] = True
                        md["done_key"] = k
                        if k in done_at_map:
                            md["done_at"] = done_at_map[k]
                            md["display_when"] = done_at_map[k]
                        if not md.get("planned_when"):
                            md["planned_when"] = s.get("when")
                        s["meta"] = md
                        s["done_ok"] = True
                except Exception:
                    pass
                steps_out.append(s)
            plan_dict = dict(plan_dict)
            plan_dict["steps"] = steps_out
            # duty 只用于头部摘要，不触发补做
            try:
                spend = _parse_when(plan_dict.get("spend_at"))
            except Exception:
                spend = None
            pending = [
                s for s in steps_out
                if not ((s.get("meta") or {}).get("done_ok") or s.get("done_ok"))
                and str(s.get("action") or "") not in ("notify", "wait", "hold")
            ]
            try:
                duty = build_duty_sections(
                    pending or steps_out, spend_at=spend, now=_dt.now()
                )
            except Exception:
                duty = plan_dict.get("duty") or {}

            cfg = HoardConfig()
            try:
                raw_cfg = plan_dict.get("config") or {}
                if isinstance(raw_cfg, dict):
                    for k, v in raw_cfg.items():
                        if hasattr(cfg, k):
                            try:
                                setattr(cfg, k, v)
                            except Exception:
                                pass
            except Exception:
                pass
            spend_dt = spend or _dt.now()
            plan_obj = HoardPlan(
                config=cfg,
                generated_at=_dt.now(),
                spend_at=spend_dt,
                steps=steps_out,
                summary=dict(plan_dict.get("summary") or {}),
                warnings=list(plan_dict.get("warnings") or []),
            )
            try:
                sm = dict(plan_obj.summary or {})
                sm["compact_head"] = True
                # 只读展示：不注入新的 replan_at，沿用已有
                sm["done_keys"] = list(done)
                plan_obj.summary = sm
            except Exception:
                pass
            body = render_plan_narrative(plan_obj)
            head = self._build_plan_head(duty, plan_obj, rep_notes=None)
            narrative = (head + "\n\n" if head else "") + body
            self.txt_plan.setPlainText(narrative)
            try:
                self._fit()
            except Exception:
                pass
            return True
        except Exception:
            return False

    def _refresh_plan_view(self, silent=False):
        """执行后刷新说明区：可 replan；打开页面请用 _load_plan，勿直接调这里。"""
        try:
            from module.hoard_ap.state import load_state
            from module.hoard_ap.execution_log import format_log_section, done_actions
            from module.hoard_ap.replan import apply_replan_to_state_plan, _compute_done_key
            from module.hoard_ap.narrative import render_plan_narrative
            from module.hoard_ap.planner import HoardPlan, HoardConfig, PlanStep
            from datetime import datetime as _dt

            st = load_state(self._config_dir())
            plan_dict = dict((st.plan or {}) if isinstance(st.plan, dict) else {})
            if not plan_dict.get("steps"):
                return False
            done = list(done_actions(self._config_dir()) or [])
            # 用账本 done_at 覆盖展示时间
            done_at_map = {}
            try:
                from module.hoard_ap.execution_log import load_log
                for e in load_log(self._config_dir()):
                    if not e.ok:
                        continue
                    k = str((e.meta or {}).get("done_key") or "").strip()
                    if k and e.when:
                        done_at_map[k] = e.when
            except Exception:
                pass
            plan_dict, _, rep_notes, duty = apply_replan_to_state_plan(
                plan_dict, now=_dt.now(), done_actions=done, step_index=0
            )
            for s in plan_dict.get("steps") or []:
                try:
                    k = _compute_done_key(s)
                    md = dict(s.get("meta") or {})
                    if k in set(done) or md.get("done_ok"):
                        md["done_ok"] = True
                        md["done_key"] = k
                        if k in done_at_map:
                            md["done_at"] = done_at_map[k]
                            # 展示用实际完成时间，不改原定 when 语义键
                            md["display_when"] = done_at_map[k]
                        s["meta"] = md
                        s["done_ok"] = True
                except Exception:
                    pass
            # 构造轻量 plan 对象供 narrative
            cfg = HoardConfig()
            try:
                raw_cfg = plan_dict.get("config") or {}
                if isinstance(raw_cfg, dict):
                    for k, v in raw_cfg.items():
                        if hasattr(cfg, k):
                            try:
                                setattr(cfg, k, v)
                            except Exception:
                                pass
            except Exception:
                pass
            steps = []
            for s in plan_dict.get("steps") or []:
                try:
                    steps.append(s if isinstance(s, dict) else s)
                except Exception:
                    pass
            spend = plan_dict.get("spend_at")
            try:
                from module.hoard_ap.narrative import _parse_when
                spend_dt = _parse_when(spend) or _dt.now()
            except Exception:
                spend_dt = _dt.now()
            plan_obj = HoardPlan(
                config=cfg,
                generated_at=_dt.now(),
                spend_at=spend_dt,
                steps=steps,
                summary=dict(plan_dict.get("summary") or {}),
                warnings=list(plan_dict.get("warnings") or []),
            )
            try:
                plan_obj.summary["done_keys"] = list(done)
            except Exception:
                pass
            # 终点三件套塞进值守花体行
            try:
                sm = dict(plan_obj.summary or {})
                sm["compact_head"] = True
                sm["replan_at"] = plan_dict.get("replanned_at") or sm.get("replan_at")
                sm["done_keys"] = list(done)
                plan_obj.summary = sm
            except Exception:
                pass
            body = render_plan_narrative(plan_obj)
            head = self._build_plan_head(duty, plan_obj, rep_notes=None)
            narrative = (head + "\n\n" if head else "") + body
            self.txt_plan.setPlainText(narrative)
            try:
                with open(
                    os.path.join(self._config_dir(), "hoard_ap_plan.txt"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(narrative)
            except Exception:
                pass
            self._fit()
            return True
        except Exception as e:
            if not silent:
                try:
                    notification.error("囤体", "刷新说明失败：%s" % e, self.config)
                except Exception:
                    pass
            return False

    def _sync_header_switch_styles(self) -> None:
        """blockSignals 后 checkedChanged 不发，手动调格子现算刷新。

        _refresh 读真实 isChecked()（活状态）现算 QSS，浅/深主题、开/关
        全部一个入口，不再依赖模块级 CSS 快照。
        """
        for cell in list(getattr(self, "_header_settings_cells", []) or []):
            if cell is None:
                continue
            try:
                fn = getattr(cell, "_refresh", None)
                if callable(fn):
                    fn()
            except Exception:
                pass

    def _load(self):
        c = self.config
        self.sw_enabled.setChecked(_as_bool(_cfg_get(c, "hoard_ap_enabled", False)))
        try:
            if hasattr(self, "sw_home_entry"):
                self.sw_home_entry.blockSignals(True)
                self.sw_home_entry.setChecked(_as_bool(_cfg_get(c, "hoard_ap_home_entry", True), True))
                self.sw_home_entry.blockSignals(False)
            if hasattr(self, "sw_home_intercept"):
                self.sw_home_intercept.blockSignals(True)
                self.sw_home_intercept.setChecked(
                    _as_bool(_cfg_get(c, "hoard_ap_home_intercept_visible", True), True)
                )
                self.sw_home_intercept.blockSignals(False)
        except Exception:
            pass
        try:
            self._sync_header_switch_styles()
        except Exception:
            pass
        try:
            if getattr(self, "sw_spend_clear", None) is not None:
                on = _cfg_get(c, "hoard_ap_spend_manual", None)
                if on is None or str(on).strip() == "":
                    on = _as_bool(_cfg_get(c, "hoard_ap_spend_auto_clear", False), False)
                else:
                    on = _as_bool(on, False)
                self._set_switch(self.sw_spend_clear, bool(on))
        except Exception:
            pass
        try:
            self._load_spend_dest_from_config()
        except Exception:
            pass
        try:
            if hasattr(self, "_overnight_blk"):
                self._load_clear_block(self._overnight_blk)
            if hasattr(self, "_spend_blk"):
                self._load_clear_block(self._spend_blk)
        except Exception:
            pass
        self.edit_soft.setText(_as_str(_cfg_get(c, "hoard_ap_soft_cap", "160") or "160"))
        self.edit_cafe_cap.setText(
            _as_str(_cfg_get(c, "hoard_ap_cafe_ap_full_cap", "740") or "740")
        )
        self.edit_current_ap.setText(_as_str(_cfg_get(c, "hoard_ap_current_ap", "")))
        self.edit_mail_ap.setText(_as_str(_cfg_get(c, "hoard_ap_mail_ap", "")))
        self.edit_cafe_claimable.setText(
            _as_str(_cfg_get(c, "hoard_ap_cafe_claimable_manual", ""))
        )
        td = _as_str(_cfg_get(c, "hoard_ap_target_date", ""))
        if not td:
            qd = QDate.currentDate().addDays(2)
            td = "%04d-%02d-%02d" % (qd.year(), qd.month(), qd.day())
        self.edit_date.setText(td)
        self.edit_spend_time.setText(
            _as_str(_cfg_get(c, "hoard_ap_spend_time", "18:30") or "18:30")
        )
        tubes = _as_str(_cfg_get(c, "hoard_ap_tubes", "auto"))
        self.edit_tubes.setText("" if tubes.lower() in ("auto", "自动") else tubes)
        self.edit_tube_days.setText(_as_str(_cfg_get(c, "hoard_ap_tube_days", "2") or "2"))

        self._set_switch(self.sw_task, _as_bool(_cfg_get(c, "hoard_ap_task_claimed", False)))
        # 日程：新键 lesson_claimed；兼容旧 lesson_ready（旧 True=会做≠已领，默认未领）
        lesson_c = _cfg_get(c, "hoard_ap_lesson_claimed", None)
        if lesson_c is None or str(lesson_c).strip() == "":
            lesson_c = False
        self._set_switch(self.sw_lesson, _as_bool(lesson_c, False))
        self._set_switch(self.sw_jjc, _as_bool(_cfg_get(c, "hoard_ap_jjc_claimed", False)))
        self._set_switch(self.sw_group, _as_bool(_cfg_get(c, "hoard_ap_group_claimed", False)))
        self._set_switch(self.sw_free, _as_bool(_cfg_get(c, "hoard_ap_free_buy_claimed", False)))
        # 邮箱明细：优先 config bags json，否则 inventory
        try:
            bags_raw = _cfg_get(c, "hoard_ap_mail_bags_json", "") or ""
            bags = json.loads(bags_raw) if bags_raw else []
        except Exception:
            bags = []
        if not bags:
            try:
                from module.hoard_ap.inventory import load_inventory, project_display, format_mail_bags_text
                inv = load_inventory(self._config_dir())
                disp = project_display(inv)
                bags = list(disp.get("mail_bags") or inv.mail_bags or [])
                if not self.edit_mail_ap.text().strip() and disp.get("mail_ap"):
                    self.edit_mail_ap.setText(str(int(disp.get("mail_ap") or 0)))
                if not self.edit_cafe_claimable.text().strip() and disp.get("cafe_claimable") is not None:
                    self.edit_cafe_claimable.setText(str(int(disp.get("cafe_claimable") or 0)))
                if not self.edit_current_ap.text().strip() and disp.get("current_ap") is not None:
                    self.edit_current_ap.setText(str(int(disp.get("current_ap") or 0)))
            except Exception:
                bags = []
        if bags:
            self._mail_bags = bags
            self._set_mail_detail_text(
                ",".join(
                    "%s@%s"
                    % (
                        int(b.get("amount") or 0),
                        ("%.1f" % float(b.get("remain_hours") or 0)).rstrip("0").rstrip(".")
                        if b.get("remain_hours") is not None
                        else "23",
                    )
                    for b in bags
                    if int(b.get("amount") or 0) > 0
                )
            )
            self.lbl_mail.setText(
                " + ".join("%s" % int(b.get("amount") or 0) for b in bags if int(b.get("amount") or 0) > 0)
            )

        mode = _as_str(_cfg_get(c, "hoard_ap_jjc_buy_mode", "30_60") or "30_60")
        keys = []
        if mode == "30":
            keys = ["30"]
        elif mode == "30_60":
            keys = ["30", "60"]
        self.jjc_row.set_selected(keys)
        self.edit_jjc_refresh.setText(_as_str(_cfg_get(c, "hoard_ap_jjc_refresh", "3") or "3"))
        gift = _as_str(_cfg_get(c, "hoard_ap_card_amount", "0") or "0")
        if not _as_bool(_cfg_get(c, "hoard_ap_use_ap_card", False)):
            gift = "0"
        _gparts = [p for p in str(gift).replace("＋", "+").split("+") if p in ("0", "130", "150")]
        if not _gparts:
            _gparts = ["0"]
        self.gift_row.set_selected(_gparts)

        self.edit_act_stage.setText(_as_str(_cfg_get(c, "activity_sweep_task_number", "1") or "1"))
        self.edit_act_times.setText(_as_str(_cfg_get(c, "activity_sweep_times", "0") or "0"))
        self.edit_main_normal.setText(_as_str(_cfg_get(c, "mainlinePriority", "") or ""))
        self.edit_main_hard.setText(_as_str(_cfg_get(c, "hardPriority", "") or ""))
        self.edit_sp.setText(_as_str(_cfg_get(c, "special_task_times", "0,0") or "0,0"))
        self.edit_scr.setText(_as_str(_cfg_get(c, "scrimmage_times", "0,0,0") or "0,0,0"))
        self.edit_daily_xy.setText(_as_str(_cfg_get(c, "hoard_ap_task_daily_tab_xy", "") or ""))
        self._upd_strategy()
        self._upd_jjc()

    def _clear_modes(self):
        # 固定顺序写入：交流会 → 特殊 → 活动 → 主线（执行器也按此序）
        modes = []
        try:
            scr = (self.edit_scr.text() or "0,0,0").replace("，", ",")
            if any(x.strip() not in ("", "0") for x in scr.split(",")):
                modes.append("scrimmage")
        except Exception:
            pass
        try:
            sp = (self.edit_sp.text() or "0,0").replace("，", ",")
            if any(x.strip() not in ("", "0") for x in sp.split(",")):
                modes.append("special")
        except Exception:
            pass
        try:
            if (self.edit_act_times.text() or "0").strip() not in ("", "0"):
                modes.append("activity")
        except Exception:
            pass
        try:
            # 主线：仅当存在次数>0 的关卡才启用
            def _has_pos(s):
                s = (s or "").replace("，", ",").replace("；", " ")
                for tok in s.replace(",", " ").split():
                    segs = tok.split("-")
                    if len(segs) >= 3:
                        t = segs[-1].strip().lower()
                        if t in ("max", "m"):
                            return True
                        try:
                            if int(float(t)) > 0:
                                return True
                        except Exception:
                            pass
                return False
            if _has_pos(self.edit_main_normal.text()) or _has_pos(self.edit_main_hard.text()):
                modes.append("mainline")
        except Exception:
            pass
        return modes or ["notify_only"]

    def _snapshot(self):
        today = QDate.currentDate()
        td = self.edit_date.text().strip()
        if not td:
            qd = today.addDays(2)
            td = "%04d-%02d-%02d" % (qd.year(), qd.month(), qd.day())
            self.edit_date.setText(td)
        tubes = self.edit_tubes.text().strip() or "auto"
        try:
            days = max(0, min(3, int(self.edit_tube_days.text().strip() or "2")))
        except ValueError:
            days = 2
        modes = self._clear_modes()
        cafe_cap = self.edit_cafe_cap.text().strip() or "740"
        try:
            per_h = "%.4f" % (float(cafe_cap) / 24.0)
        except Exception:
            per_h = "30.8333"
        keys = set(self.jjc_row.selected_keys())
        mode = (
            "30_60"
            if "30" in keys and "60" in keys
            else ("30" if "30" in keys else ("30_60" if "60" in keys else "none"))
        )
        try:
            ref = max(0, min(3, int(self.edit_jjc_refresh.text().strip() or "0")))
        except ValueError:
            ref = 0
        per = (30 if "30" in keys else 0) + (60 if "60" in keys else 0)
        bags = self._parse_bags(self._mail_detail_text()) or list(self._mail_bags)
        mail_total = self.edit_mail_ap.text().strip()
        if bags and not mail_total:
            mail_total = str(sum(int(b.get("amount") or 0) for b in bags))
        gift = "+".join(self.gift_row.selected_keys() or ["0"]) or "0"
        try:
            tn = 0 if tubes == "auto" else int(tubes)
        except ValueError:
            tn = 0
        try:
            nml = (self.edit_main_normal.text() or "").replace(" ", "").replace("，", ",")
            hard = (self.edit_main_hard.text() or "").replace(" ", "").replace("，", ",")
            self._save("mainlinePriority", nml)
            self._save("hardPriority", hard)

            def _parse_list(s):
                out = []
                for part in (s or "").split(","):
                    part = part.strip()
                    if not part:
                        continue
                    bits = part.split("-")
                    if len(bits) < 3:
                        continue
                    try:
                        r, m = int(bits[0]), int(bits[1])
                        c = bits[2]
                        c = "max" if str(c).lower() == "max" else int(c)
                        out.append([r, m, c])
                    except Exception:
                        continue
                return out

            self._save("unfinished_normal_tasks", _parse_list(nml))
            self._save("unfinished_hard_tasks", _parse_list(hard))
        except Exception:
            pass

        return {
            "hoard_ap_enabled": bool(self.sw_enabled.isChecked()),
            "hoard_ap_spend_auto_clear": bool(
                getattr(self, "sw_spend_clear", None)
                and self.sw_spend_clear.isChecked()
            ),
            "hoard_ap_target_date": td,
            "hoard_ap_spend_time": self.edit_spend_time.text().strip() or "18:30",
            "hoard_ap_tubes": tubes,
            "hoard_ap_tube_days": str(days),
            "hoard_ap_strategy": "xiuxian" if (tubes == "auto" or tn > 0) else "simple",
            "hoard_ap_clear_mode": modes[0],
            "hoard_ap_clear_modes": ",".join(modes),
            "hoard_ap_use_ap_card": gift not in ("", "0"),
            "hoard_ap_card_amount": gift if gift not in ("", "0") else "0",
            "hoard_ap_hard_cap": "999",
            "hoard_ap_soft_cap": self.edit_soft.text().strip() or "160",
            "hoard_ap_cafe_ap_full_cap": cafe_cap,
            "hoard_ap_cafe_ap_per_hour": per_h,
            "hoard_ap_cafe_claimable_manual": self.edit_cafe_claimable.text().strip(),
            "hoard_ap_cafe_hours_since_claim": "0",
            "hoard_ap_current_ap": self.edit_current_ap.text().strip(),
            "hoard_ap_mail_ap": mail_total,
            "hoard_ap_task_claimed": bool(self.sw_task.isChecked()),
            "hoard_ap_lesson_claimed": bool(self.sw_lesson.isChecked()),
            # 兼容旧字段：lesson_ready=True 表示「会领/未领完」
            "hoard_ap_lesson_ready": (not bool(self.sw_lesson.isChecked())),
            "hoard_ap_jjc_claimed": bool(self.sw_jjc.isChecked()),
            "hoard_ap_group_claimed": bool(self.sw_group.isChecked()),
            "hoard_ap_free_buy_claimed": bool(self.sw_free.isChecked()),
            "hoard_ap_jjc_buy_mode": mode,
            "hoard_ap_jjc_refresh": str(ref),
            "hoard_ap_jjc_ap": str(per * (ref + 1)),
            "hoard_ap_task_ap": "150",
            "hoard_ap_group_ap": "10",
            "hoard_ap_xiuxian_clear_time": "02:00",
            "hoard_ap_mail_bags_json": json.dumps(bags, ensure_ascii=False),
            "hoard_ap_task_daily_tab_xy": self.edit_daily_xy.text().strip(),
            "hoard_ap_overnight_main_normal": (self._overnight_blk["main_normal"].text() if hasattr(self, "_overnight_blk") else "") or "",
            "hoard_ap_overnight_main_hard": (self._overnight_blk["main_hard"].text() if hasattr(self, "_overnight_blk") else "") or "",
            "hoard_ap_overnight_special_exp": (self._overnight_blk["sp_exp"].text() if hasattr(self, "_overnight_blk") else "0") or "0",
            "hoard_ap_overnight_special_money": (self._overnight_blk["sp_money"].text() if hasattr(self, "_overnight_blk") else "0") or "0",
            "hoard_ap_overnight_activity_stage": (self._overnight_blk["act_stage"].text() if hasattr(self, "_overnight_blk") else "1") or "1",
            "hoard_ap_overnight_activity_times": (self._overnight_blk["act_times"].text() if hasattr(self, "_overnight_blk") else "0") or "0",
            "hoard_ap_overnight_scr_trinity": (self._overnight_blk["scr"]["trinity"].text() if hasattr(self, "_overnight_blk") else "0") or "0",
            "hoard_ap_overnight_scr_millennium": (self._overnight_blk["scr"]["millennium"].text() if hasattr(self, "_overnight_blk") else "0") or "0",
            "hoard_ap_overnight_scr_gehenna": (self._overnight_blk["scr"]["gehenna"].text() if hasattr(self, "_overnight_blk") else "0") or "0",
            "hoard_ap_spend_main_normal": (self._spend_blk["main_normal"].text() if hasattr(self, "_spend_blk") else "") or "",
            "hoard_ap_spend_main_hard": (self._spend_blk["main_hard"].text() if hasattr(self, "_spend_blk") else "") or "",
            "hoard_ap_spend_special_exp": (self._spend_blk["sp_exp"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "hoard_ap_spend_special_money": (self._spend_blk["sp_money"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "hoard_ap_spend_activity_stage": (self._spend_blk["act_stage"].text() if hasattr(self, "_spend_blk") else "1") or "1",
            "hoard_ap_spend_activity_times": (self._spend_blk["act_times"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "hoard_ap_spend_scr_trinity": (self._spend_blk["scr"]["trinity"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "hoard_ap_spend_scr_millennium": (self._spend_blk["scr"]["millennium"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "hoard_ap_spend_scr_gehenna": (self._spend_blk["scr"]["gehenna"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "activity_sweep_task_number": (self._spend_blk["act_stage"].text() if hasattr(self, "_spend_blk") else "1") or "1",
            "activity_sweep_times": (self._spend_blk["act_times"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            "mainlinePriority": (self._spend_blk["main_normal"].text() if hasattr(self, "_spend_blk") else "") or "",
            "hardPriority": (self._spend_blk["main_hard"].text() if hasattr(self, "_spend_blk") else "") or "",
            "special_task_times": "%s,%s" % (
                (self._spend_blk["sp_exp"].text() if hasattr(self, "_spend_blk") else "0") or "0",
                (self._spend_blk["sp_money"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            ),
            "scrimmage_times": "%s,%s,%s" % (
                (self._spend_blk["scr"]["trinity"].text() if hasattr(self, "_spend_blk") else "0") or "0",
                (self._spend_blk["scr"]["millennium"].text() if hasattr(self, "_spend_blk") else "0") or "0",
                (self._spend_blk["scr"]["gehenna"].text() if hasattr(self, "_spend_blk") else "0") or "0",
            ),
        }

    def _prefer_clear_mode_from_config(self) -> str:
        try:
            return str(_cfg_get(self.config, "hoard_ap_prefer_clear", "") or "").strip().lower()
        except Exception:
            return ""

    def _normalize_prefer_mode(self, mode: str) -> str:
        """兼容旧 mainline → normal；合法值 normal/hard/special/high_value。"""
        m = (mode or "").strip().lower()
        if m == "mainline":
            return "normal"
        if m in ("normal", "hard", "special", "high_value"):
            return m
        return ""

    def _apply_spend_dest_style(self, mode: str = "") -> None:
        """四快捷：现算 QSS（选中蓝框/其余灰框），不再用冻结快照。"""
        mode = self._normalize_prefer_mode(mode)
        from gui.components.expand.tool_style import _switch_qss

        for k, cell in getattr(self, "_spend_dest_cells", {}).items():
            try:
                cell.setStyleSheet(_switch_qss("spendDestCell", k == mode))
                cell.update()
            except Exception:
                pass
        try:
            # 说明固定，不随选项改写
            self.lbl_status.setText("激活右侧开关\n会拦截选项以外的花体力事件")
        except Exception:
            pass

    def _load_spend_dest_from_config(self) -> None:
        mode = self._normalize_prefer_mode(self._prefer_clear_mode_from_config())
        # 旧 mainline 读到后写回 normal，避免下次再丢
        try:
            raw = self._prefer_clear_mode_from_config()
            if str(raw).strip().lower() == "mainline" and mode == "normal":
                self._save("hoard_ap_prefer_clear", "normal")
        except Exception:
            pass
        for k, sw in getattr(self, "_spend_dest_switches", {}).items():
            try:
                sw.blockSignals(True)
                sw.setChecked(k == mode)
            finally:
                try:
                    sw.blockSignals(False)
                except Exception:
                    pass
        self._apply_spend_dest_style(mode)

    def _on_home_entry_changed(self, v: bool) -> None:
        self._save("hoard_ap_home_entry", bool(v))
        self._refresh_home_plugins()

    def _on_home_intercept_changed(self, v: bool) -> None:
        self._save("hoard_ap_home_intercept_visible", bool(v))
        self._refresh_home_plugins()

    def _fill_spend_neg_one(self, mode: str) -> None:
        """开快捷 → 到点清体力对应项填 -1。"""
        mode = self._normalize_prefer_mode(mode)
        blk = getattr(self, "_spend_blk", None)
        if not blk:
            if mode == "normal":
                cur = str(_cfg_get(self.config, "hoard_ap_spend_main_normal", "") or "").strip()
                if not cur:
                    self._save("hoard_ap_spend_main_normal", "1-1--1")
            elif mode == "hard":
                cur = str(_cfg_get(self.config, "hoard_ap_spend_main_hard", "") or "").strip()
                if not cur:
                    self._save("hoard_ap_spend_main_hard", "h1-1--1")
            elif mode == "special":
                self._save("hoard_ap_spend_special_exp", "-1")
                self._save("hoard_ap_spend_special_money", "-1")
            elif mode == "high_value":
                self._save("hoard_ap_spend_activity_times", "-1")
            return
        if mode == "normal":
            e = blk["main_normal"]
            if not (e.text() or "").strip():
                e.setText("1-1--1")
                self._save("hoard_ap_spend_main_normal", "1-1--1")
        elif mode == "hard":
            e = blk["main_hard"]
            if not (e.text() or "").strip():
                e.setText("h1-1--1")
                self._save("hoard_ap_spend_main_hard", "h1-1--1")
        elif mode == "special":
            blk["sp_exp"].setText("-1")
            blk["sp_money"].setText("-1")
            self._save("hoard_ap_spend_special_exp", "-1")
            self._save("hoard_ap_spend_special_money", "-1")
        elif mode == "high_value":
            blk["act_times"].setText("-1")
            self._save("hoard_ap_spend_activity_times", "-1")

    def _on_spend_dest_toggled(self, mode: str, checked: bool) -> None:
        """四快捷：写 prefer_clear；开时给到点清体对应项填 -1。"""
        mode = self._normalize_prefer_mode(mode)
        if checked:
            for k, sw in getattr(self, "_spend_dest_switches", {}).items():
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
            cur = self._normalize_prefer_mode(self._prefer_clear_mode_from_config())
            val = "" if cur == mode else cur
        try:
            self._save("hoard_ap_prefer_clear", val)
        except Exception:
            pass
        try:
            if val in ("normal", "hard"):
                # 调度侧 clear_mode 仍用 mainline 表示主线系
                self._save("hoard_ap_clear_mode", "mainline")
                self._save("hoard_ap_clear_modes", "mainline")
            elif val == "special":
                self._save("hoard_ap_clear_mode", "special")
                self._save("hoard_ap_clear_modes", "special")
            elif val == "high_value":
                self._save("hoard_ap_clear_mode", "activity")
                self._save("hoard_ap_clear_modes", "activity")
        except Exception:
            pass
        self._apply_spend_dest_style(val)
        self._refresh_home_plugins()

    def _plan_reject(self, msg: str) -> None:
        """拒绝生成计划：只写计划区固定文案，不写 state、不用飞过 toast。"""
        try:
            self.txt_plan.setPlainText(msg)
            self._fit()
        except Exception:
            pass
        try:
            with open(
                os.path.join(self._config_dir(), "hoard_ap_plan.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(msg)
        except Exception:
            pass

    def _resolve_user_spend_at(self):
        """按表单消费日+花体时刻解析，不做次日顺延。"""
        from datetime import timedelta
        from module.hoard_ap.planner import (
            SERVER_DAY_RESET_HOUR,
            combine_server_date_and_time,
            server_day_start,
        )

        td = (self.edit_date.text() or "").strip()
        st = (self.edit_spend_time.text() or "").strip() or "18:30"
        now = datetime.now()
        if not td:
            day = server_day_start(now) + timedelta(days=1)
        else:
            y, m, d = [int(x) for x in td.split("-")]
            day = datetime(y, m, d, SERVER_DAY_RESET_HOUR, 0, 0)
        return combine_server_date_and_time(day, st)

    def _on_calculate(self):
        # 花体时刻/消费日已过点：无论开关，一律不生成；只在计划区写提示
        PAST_MSG = "请把消费日跟花体时刻设在今天以后。"
        try:
            spend_at = self._resolve_user_spend_at()
            if spend_at is not None and spend_at <= datetime.now():
                self._plan_reject(PAST_MSG)
                return
        except Exception:
            self._plan_reject(PAST_MSG)
            return
        # 关闭状态下禁止出新计划（避免关着仍写 Armed / 调度）
        try:
            if not bool(self.sw_enabled.isChecked()):
                self._plan_reject("当前为关闭状态。请先打开「启用」再点计算计划。")
                return
        except Exception:
            pass

        snap = self._calc_snapshot_and_save()
        if snap is None:
            return

        try:
            res = self._calc_plan_and_replan(snap)
            if res is None:
                return  # 已过点：内部已写提示
            plan, plan_dict, start_idx, duty, done = res
            self._calc_commit_state(plan, plan_dict, duty, snap, start_idx)
            self._calc_sync_schedule(plan, plan_dict)
            s = plan.summary or {}
            notification.success(
                "囤体",
                "已计算 · %s · 体%s 邮%s"
                % (
                    plan.spend_at.strftime("%m-%d %H:%M"),
                    s.get("final_ap"),
                    s.get("final_mail"),
                ),
                self.config,
            )
        except Exception as e:
            notification.error("囤体", str(e), self.config)
            self.txt_plan.setPlainText("%s\n%s" % (e, traceback.format_exc(limit=3)))

    def _calc_snapshot_and_save(self):
        """表单快照 → 保存配置与库存；失败返回 None。"""
        try:
            snap = self._snapshot()
            for k, v in snap.items():
                if k != "hoard_ap_mail_bags_json":
                    self._save(k, v)
            bags = json.loads(snap.get("hoard_ap_mail_bags_json") or "[]")
            try:
                from module.hoard_ap.inventory import snapshot_from_form, save_inventory

                inv = snapshot_from_form(
                    current_ap=int(float(snap.get("hoard_ap_current_ap") or 0) or 0),
                    mail_ap=int(float(snap.get("hoard_ap_mail_ap") or 0) or 0),
                    cafe_claimable=int(
                        float(snap.get("hoard_ap_cafe_claimable_manual") or 0) or 0
                    ),
                    soft_cap=int(float(snap.get("hoard_ap_soft_cap") or 160) or 160),
                    cafe_cap=float(snap.get("hoard_ap_cafe_ap_full_cap") or 740),
                    task_claimed=bool(snap.get("hoard_ap_task_claimed")),
                    lesson_claimed=bool(snap.get("hoard_ap_lesson_claimed")),
                    jjc_claimed=bool(snap.get("hoard_ap_jjc_claimed")),
                    group_claimed=bool(snap.get("hoard_ap_group_claimed")),
                    free_buy_claimed=bool(snap.get("hoard_ap_free_buy_claimed")),
                    mail_bags=bags,
                )
                save_inventory(self._config_dir(), inv)
            except Exception as e:
                # 快照没落盘=计算用的现状与真实账本可能不一致，留痕
                print("[hoard_ap] 计算快照写账本失败:", e)
            return snap
        except Exception as e:
            notification.error("囤体", "保存失败：%s" % e, self.config)
            return None

    def _calc_plan_and_replan(self, snap):
        """构建计划 → 账本迟到重算 → 打勾回写；已过点返回 None。"""
        from module.hoard_ap.planner import build_plan_from_user_config
        from module.hoard_ap.replan import apply_replan_to_state_plan
        from module.hoard_ap.execution_log import done_actions

        plan = build_plan_from_user_config(snap)
        # 双重保险：计划器解析后仍过点 → 不写 state，只提示改期
        try:
            sa = getattr(plan, "spend_at", None)
            if sa is not None and sa <= datetime.now():
                self._plan_reject("请把消费日跟花体时刻设在今天以后。")
                return None
        except Exception:
            self._plan_reject("请把消费日跟花体时刻设在今天以后。")
            return None
        plan_dict = plan.to_dict()
        # 保留执行账本：已跑过的节点打✓并跳过；新计划插在「现在」之后
        # （不要 clear_log，否则会把刚清完的体又当成未做去补做）
        done = []
        try:
            done = list(done_actions(self._config_dir()) or [])
        except Exception:
            done = []
        plan_dict, start_idx, _rep_notes, duty = apply_replan_to_state_plan(
            plan_dict,
            now=datetime.now(),
            done_actions=done,
            step_index=0,
        )
        # 把账本里的完成标记写回 steps，供时间轴打✓
        self._stamp_done_marks(plan_dict, done)
        # narrative 用带 done 标记的 plan_dict
        try:
            # 覆盖 steps 为 replan 后的
            if hasattr(plan, "steps"):
                plan.steps = plan_dict.get("steps") or plan.steps
        except Exception:
            pass
        try:
            if getattr(plan, "summary", None) is None:
                plan.summary = {}
            if isinstance(plan.summary, dict):
                plan.summary["done_keys"] = list(done)
        except Exception:
            pass
        try:
            if getattr(plan, "summary", None) is None:
                plan.summary = {}
            if isinstance(plan.summary, dict):
                plan.summary["compact_head"] = True
                plan.summary["replan_at"] = plan_dict.get("replanned_at")
                plan.summary["done_keys"] = list(done)
        except Exception:
            pass
        # 账本 done_at 写回 steps，锁死完成时间
        self._stamp_done_at(plan, plan_dict, done)
        return plan, plan_dict, start_idx, duty, done

    def _stamp_done_marks(self, plan_dict: dict, done: list):
        """账本完成标记写回 steps（done_ok/done_key），供时间轴打✓。"""
        try:
            from module.hoard_ap.replan import _compute_done_key as _cdk
            done_set = set(done)
            for s in plan_dict.get("steps") or []:
                try:
                    k = _cdk(s)
                    md = dict(s.get("meta") or {})
                    if k in done_set or md.get("done_ok"):
                        md["done_ok"] = True
                        md["done_key"] = k
                        s["meta"] = md
                except Exception:
                    pass
        except Exception:
            pass

    def _stamp_done_at(self, plan, plan_dict: dict, done: list):
        """账本 done_at 写回 steps，锁死完成时间与原定时间展示。"""
        try:
            from module.hoard_ap.execution_log import load_log
            from module.hoard_ap.replan import _compute_done_key as _cdk2
            done_at_map = {}
            for e in load_log(self._config_dir()):
                if not e.ok:
                    continue
                k = str((e.meta or {}).get("done_key") or "").strip()
                if k and e.when:
                    done_at_map[k] = e.when
            for s in plan_dict.get("steps") or []:
                try:
                    k = _cdk2(s)
                    md = dict(s.get("meta") or {})
                    if k in set(done) or md.get("done_ok"):
                        md["done_ok"] = True
                        md["done_key"] = k
                        if not md.get("planned_when"):
                            md["planned_when"] = s.get("when")
                        if k in done_at_map:
                            md["done_at"] = done_at_map[k]
                            md["display_when"] = done_at_map[k]
                        # when 保持原定，不改成计算时刻
                        if md.get("planned_when"):
                            s["when"] = md["planned_when"]
                        s["meta"] = md
                        s["done_ok"] = True
                except Exception:
                    pass
            if hasattr(plan, "steps"):
                plan.steps = plan_dict.get("steps") or plan.steps
        except Exception:
            pass

    def _calc_commit_state(self, plan, plan_dict: dict, duty, snap, start_idx) -> str:
        """渲染 narrative → 写 Armed state → 刷新 UI/库存表单/落盘。"""
        from module.hoard_ap.narrative import render_plan_narrative
        from module.hoard_ap.constants import PHASE_ARMED
        from module.hoard_ap.state import HoardRuntimeState, save_state

        body = render_plan_narrative(plan)
        head = self._build_plan_head(duty, plan, rep_notes=None)
        narrative = (head + "\n\n" if head else "") + body
        plan_dict["narrative"] = narrative
        plan_dict["duty"] = duty
        state = HoardRuntimeState(
            phase=PHASE_ARMED,
            plan=plan_dict,
            step_index=int(start_idx or 0),
            armed_at=datetime.now().isoformat(sep=" ", timespec="seconds"),
            strategy_mode=str(snap.get("hoard_ap_strategy") or ""),
        )
        save_state(self._config_dir(), state)
        self.txt_plan.setPlainText(narrative)
        self._fit()
        try:
            self._sync_proj_timer()
        except Exception:
            pass
        # 同步库存邮箱明细到表单（识别结果）
        try:
            from module.hoard_ap.inventory import load_inventory, format_mail_bags_input
            inv = load_inventory(self._config_dir())
            if inv.mail_bags:
                self._mail_bags = list(inv.mail_bags)
                self._set_mail_detail_text(format_mail_bags_input(inv.mail_bags))
                if inv.mail_ap:
                    self.edit_mail_ap.setText(str(int(inv.mail_ap)))
        except Exception:
            pass
        try:
            with open(
                os.path.join(self._config_dir(), "hoard_ap_plan.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(narrative)
        except Exception:
            pass
        return narrative

    def _calc_sync_schedule(self, plan, plan_dict: dict):
        """计算成功且启用中 → 调度页事件「囤体」必须勾上，并写 next_tick 到首步。"""
        from module.hoard_ap.narrative import first_actionable_when

        start_when = first_actionable_when(plan)
        try:
            steps = plan_dict.get("steps") or []
            if steps:
                from module.hoard_ap.narrative import _parse_when

                w0 = _parse_when(steps[0].get("when"))
                if w0:
                    start_when = w0
        except Exception:
            pass
        try:
            ts = max(int(start_when.timestamp()), int(time.time()) + 15)
            self._sync_hoard_event_enabled(True, next_tick=ts)
            # 额外确保 next_tick 精确落到首步
            for ep in self._event_json_paths():
                try:
                    with open(ep, "r", encoding="utf-8") as f:
                        events = json.load(f)
                    for ev in events:
                        if not isinstance(ev, dict):
                            continue
                        if ev.get("func_name") == "hoard_ap" or ev.get("event_name") in (
                            "囤体",
                            "hoard_ap",
                        ):
                            ev["enabled"] = True
                            ev["next_tick"] = ts
                    tmp = ep + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(events, f, ensure_ascii=False, indent=2)
                    os.replace(tmp, ep)
                except Exception as e:
                    # 对齐失败=计划开始时间与调度表脱节，留痕
                    print("[hoard_ap] event.json 对齐 next_tick 失败:", e)
        except Exception:
            pass


    def _event_json_paths(self):
        """调度页读的 event.json 可能路径：config_dir/event.json。"""
        paths = []
        cd = self._config_dir()
        if cd:
            paths.append(os.path.join(cd, "event.json"))
        # 兼容少数把 config 指到上级的情况
        try:
            parent = os.path.dirname(cd.rstrip("\\/")) if cd else ""
            if parent:
                paths.append(os.path.join(parent, "event.json"))
        except Exception:
            pass
        out, seen = [], set()
        for pth in paths:
            ap = os.path.abspath(pth)
            if ap not in seen and os.path.isfile(ap):
                seen.add(ap)
                out.append(ap)
        return out

    def _sync_hoard_event_enabled(self, enabled: bool, next_tick: int = 0) -> bool:
        """把囤体开关同步进调度页 event.json 的「启用」列（事件·囤体）。

        调度页事件表读的就是这份文件的 enabled 字段。
        返回是否成功写到至少一份文件；写完后热刷调度表勾选。
        """
        ok_any = False
        ts = int(next_tick) if next_tick else 0
        if enabled and ts <= 0:
            ts = int(time.time()) + 15
        paths = list(self._event_json_paths() or [])
        try:
            cd = self._config_dir()
            if cd:
                p0 = os.path.abspath(os.path.join(cd, "event.json"))
                if p0 not in [os.path.abspath(x) for x in paths]:
                    paths.insert(0, p0)
        except Exception:
            pass
        if not paths:
            return False
        for ep in paths:
            try:
                if not os.path.isfile(ep):
                    continue
                with open(ep, "r", encoding="utf-8") as f:
                    events = json.load(f)
                if not isinstance(events, list):
                    continue
                hit = False
                for ev in events:
                    if not isinstance(ev, dict):
                        continue
                    fn = str(ev.get("func_name") or "").strip()
                    ename = str(ev.get("event_name") or "").strip()
                    if fn == "hoard_ap" or ename in ("囤体", "hoard_ap"):
                        hit = True
                        ev["enabled"] = bool(enabled)
                        if enabled:
                            try:
                                cur_nt = int(ev.get("next_tick") or 0)
                            except Exception:
                                cur_nt = 0
                            if ts > 0 and (cur_nt <= 0 or cur_nt < int(time.time())):
                                ev["next_tick"] = ts
                if not hit:
                    events.append(
                        {
                            "enabled": bool(enabled),
                            "priority": -3,
                            "interval": 300,
                            "daily_reset": [[20, 0, 0]],
                            "next_tick": int(ts or 0),
                            "event_name": "囤体",
                            "func_name": "hoard_ap",
                            "disabled_time_range": [],
                            "pre_task": [],
                            "post_task": [],
                        }
                    )
                    hit = True
                tmp = ep + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(events, f, ensure_ascii=False, indent=2)
                os.replace(tmp, ep)
                ok_any = True
            except Exception:
                continue
        try:
            self._refresh_schedule_feature_switch_ui()
        except Exception:
            pass
        return ok_any

    def _refresh_schedule_feature_switch_ui(self) -> None:
        """让调度页事件表立即按 event.json 重画启用勾选。"""
        root = None
        try:
            getter = getattr(self.config, "get_window", None)
            if callable(getter):
                root = getter()
        except Exception:
            root = None
        if root is None:
            try:
                root = getattr(self.config, "window", None)
            except Exception:
                root = None
        if root is None:
            try:
                w = self
                for _ in range(16):
                    p = w.parent() if hasattr(w, "parent") else None
                    if p is None:
                        break
                    w = p() if callable(p) else p
                root = w
            except Exception:
                root = None
        if root is None:
            return
        try:
            from gui.components.expand.featureSwitch import Layout as FSLayout
        except Exception:
            FSLayout = None
        widgets = []
        try:
            if FSLayout is not None:
                widgets = list(root.findChildren(FSLayout))
        except Exception:
            widgets = []
        for fs in widgets:
            try:
                if hasattr(fs, "reload_from_disk"):
                    fs.reload_from_disk()
                else:
                    if hasattr(fs, "_read_config"):
                        fs._read_config()
                    if hasattr(fs, "_sort"):
                        fs._sort()
            except Exception:
                continue

    def _on_enabled_changed(self, v: bool) -> None:
        """启用/关闭联动：写 config + 调度页 event.json「启用」；关时 phase=idle、停表。"""
        try:
            self._save("hoard_ap_enabled", bool(v))
        except Exception:
            pass
        wrote = False
        try:
            wrote = bool(self._sync_hoard_event_enabled(bool(v)))
        except Exception:
            wrote = False
        try:
            from module.hoard_ap.constants import PHASE_IDLE, PHASE_ARMED
            from module.hoard_ap.state import load_state, save_state

            cd = self._config_dir()
            st = load_state(cd)
            if not v:
                st.phase = PHASE_IDLE
                st.notes = (st.notes or [])[-15:] + ["hoard disabled → release schedule"]
                save_state(cd, st)
            else:
                if st.plan and (st.plan.get("steps") or []):
                    st.phase = PHASE_ARMED
                else:
                    st.phase = PHASE_IDLE
                save_state(cd, st)
        except Exception as e:
            # 相位没随开关复位=调度过滤行为与开关脱节，必须留痕
            print("[hoard_ap] 开关切换写运行状态失败:", e)
        # 关：立刻停咖啡/邮推算定时器
        try:
            self._sync_proj_timer()
        except Exception:
            pass
        if not wrote:
            try:
                notification.error(
                    "囤体",
                    "未能写入调度事件表（event.json）。请到「调度」页手动取消勾选事件「囤体」。\n目录：%s"
                    % self._config_dir(),
                    self.config,
                )
            except Exception:
                pass

    def _reset_form_for_new_plan(self) -> None:
        """一键清除配置：清现状数字 / 今日已领 / 邮箱明细（保留上限·氪金·清体去向·花体时刻）。"""
        # 今日已领 → 全部未领
        for attr, key in (
            ("sw_task", "hoard_ap_task_claimed"),
            ("sw_lesson", "hoard_ap_lesson_claimed"),
            ("sw_group", "hoard_ap_group_claimed"),
            ("sw_free", "hoard_ap_free_buy_claimed"),
            ("sw_jjc", "hoard_ap_jjc_claimed"),
        ):
            sw = getattr(self, attr, None)
            if sw is None:
                continue
            try:
                sw.blockSignals(True)
                sw.setChecked(False)
            finally:
                try:
                    sw.blockSignals(False)
                except Exception:
                    pass
            try:
                self._save(key, False)
            except Exception:
                pass
        try:
            self._save("hoard_ap_lesson_ready", True)
        except Exception:
            pass

        # 当前现状 → 清空，逼重新填/识别（否则会沿用上一轮花完后的 999/邮堆）
        for edit, key, val in (
            (getattr(self, "edit_current_ap", None), "hoard_ap_current_ap", ""),
            (getattr(self, "edit_cafe_claimable", None), "hoard_ap_cafe_claimable_manual", ""),
            (getattr(self, "edit_mail_ap", None), "hoard_ap_mail_ap", ""),
        ):
            if edit is None:
                continue
            try:
                edit.blockSignals(True)
                edit.setText(val)
            finally:
                try:
                    edit.blockSignals(False)
                except Exception:
                    pass
            try:
                self._save(key, val)
            except Exception:
                pass
        self._mail_bags = []
        try:
            self._set_mail_detail_text("")
        except Exception:
            pass
        try:
            self._save("hoard_ap_mail_bags_json", "[]")
        except Exception:
            pass
        try:
            if getattr(self, "lbl_mail", None) is not None:
                self.lbl_mail.setText("")
        except Exception:
            pass

        # inventory：直接删文件 + 写空快照，避免计时器/合计被旧邮回填
        try:
            from module.hoard_ap.inventory import (
                InventorySnapshot,
                save_inventory,
                inventory_path,
            )

            ip = inventory_path(self._config_dir())
            try:
                if os.path.isfile(ip):
                    os.remove(ip)
            except Exception:
                pass
            # snapped_at 置空 → _tick_project 直接 return，不再给咖啡计时
            empty = InventorySnapshot(
                snapped_at="",
                current_ap=0,
                mail_ap=0,
                cafe_claimable=0,
                soft_cap=int(float(self.edit_soft.text() or 160) or 160),
                cafe_cap=float(self.edit_cafe_cap.text() or 740),
                task_claimed=False,
                lesson_claimed=False,
                jjc_claimed=False,
                group_claimed=False,
                free_buy_claimed=False,
                claimed_day_start="",
                mail_bags=[],
                mail_scanned_at="",
            )
            save_inventory(self._config_dir(), empty)
        except Exception as e:
            print("[hoard_ap] 清空账本落盘失败:", e)

        # 邮箱合计强制清 UI（含隐藏绑定值）
        try:
            self.edit_mail_ap.blockSignals(True)
            self.edit_mail_ap.setText("0")
            self.edit_mail_ap.blockSignals(False)
            self._save("hoard_ap_mail_ap", "0")
        except Exception:
            pass
        try:
            self.lbl_mail.setText("")
        except Exception:
            pass
        try:
            self._set_mail_detail_text("")
        except Exception:
            pass

        # 计划区清空
        try:
            self.txt_plan.setPlainText(
                "已清空上一轮计划 / 执行记录 / 今日已领 / 现状。\n"
                "请重新填写当前体力、邮箱、咖啡可领（或点识别邮箱），打开启用后再点「计算计划」。"
            )
        except Exception:
            pass
        try:
            pth = os.path.join(self._config_dir(), "hoard_ap_plan.txt")
            if os.path.isfile(pth):
                os.remove(pth)
        except Exception:
            pass
        try:
            self._sync_proj_timer()
        except Exception:
            pass

    def _on_new_plan(self):
        """一键清除配置：清空执行账本 + 现状/已领 + 旧计划（保留上限/氪金/清体去向/花体时刻）。"""
        try:
            from module.hoard_ap.execution_log import clear_log
            from module.hoard_ap.state import HoardRuntimeState, save_state
            from module.hoard_ap.constants import PHASE_IDLE

            cd = self._config_dir()
            clear_log(cd)
            try:
                save_state(
                    cd,
                    HoardRuntimeState(phase=PHASE_IDLE, plan={}, step_index=0),
                )
            except Exception as e:
                print("[hoard_ap] 复位运行状态落盘失败:", e)
            # 去掉日界重启旗标，允许下一轮 04:00 再重启
            try:
                fp = os.path.join(cd, "hoard_ap_day_restart.flag")
                if os.path.isfile(fp):
                    os.remove(fp)
            except Exception:
                pass
            # 清内部调用旗标，避免卡死
            for name in ("hoard_ap_internal.flag",):
                try:
                    fp = os.path.join(cd, name)
                    if os.path.isfile(fp):
                        os.remove(fp)
                except Exception:
                    pass
            self._reset_form_for_new_plan()
        except Exception as e:
            notification.error("囤体", "清空失败：%s" % e, self.config)
            return
        try:
            self._fit()
        except Exception:
            pass
        try:
            notification.success(
                "囤体",
                "已清除配置：执行记录/今日已领/现状/旧计划已清空；上限与清体去向保留。请重填现状后点计算计划。",
                self.config,
            )
        except Exception:
            pass
