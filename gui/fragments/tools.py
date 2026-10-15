# -*- coding: utf-8 -*-
"""左侧「工具」导航：大厅卡片 → 进入全页工作台。

导航记忆：
- 在工具页内再点左侧「工具」→ 回大厅
- 从主页等其它页再点「工具」→ 回到上次打开的工具
- Esc → 回大厅
"""
from __future__ import annotations

import time
from hashlib import md5
from random import random
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QApplication,
)

try:
    from qfluentwidgets import (
        PushButton,
        CheckBox,
        LineEdit,
        MessageBox,
        InfoBar,
    )
except Exception:  # pragma: no cover
    from PyQt5.QtWidgets import QPushButton as PushButton
    from PyQt5.QtWidgets import QCheckBox as CheckBox, QLineEdit as LineEdit
    MessageBox = None
    InfoBar = None

# 页级视口高度约束（防 frameless 首次移动原生加高，见类 docstring）
try:
    from gui.util.customized_ui import ViewportCappedFragment, ViewportCappedVBoxLayout
except Exception:  # pragma: no cover
    class ViewportCappedFragment:
        pass
    ViewportCappedVBoxLayout = QVBoxLayout
    try:
        from qfluentwidgets import CheckBox, LineEdit
    except Exception:
        from PyQt5.QtWidgets import QCheckBox as CheckBox, QLineEdit as LineEdit
    MessageBox = None
    InfoBar = None

try:
    from gui.components.expand.tool_style import (
        apply_full_theme_refresh,
        connect_theme_refresh_full,
        is_dark,
        themed_accent_text,
        themed_title_text,
        themed_secondary_text,
        themed_badge_bg,
        themed_card_bg,
        themed_card_hover_border,
        themed_disabled_strip,
        themed_disabled_text,
        themed_input_border,
        themed_section_body_bg,
        make_icon_button,
        themed_scrollbar_qss,
        themed_page_transparent_qss,
        safe_connect_theme,
        themed_text,
        themed_tool_card_bg,
        apply_theme_to_labels,
    )
except Exception:  # pragma: no cover
    apply_full_theme_refresh = None
    connect_theme_refresh_full = None
    is_dark = lambda: False
    themed_accent_text = lambda: "#1677D2"
    themed_title_text = lambda: "#1D2735"
    themed_secondary_text = lambda: "#687588"
    themed_badge_bg = lambda: "#F1F3F5"
    themed_card_bg = lambda: "#FFFFFF"
    themed_card_hover_border = lambda: "#8a8a8a"
    themed_disabled_strip = lambda: "rgba(140,140,140,36)"
    themed_disabled_text = lambda: "#8a8a8a"
    themed_input_border = lambda: "#999999"
    themed_scrollbar_qss = lambda: ""
    themed_page_transparent_qss = lambda *o: ""
    safe_connect_theme = lambda *o, **k: None
    themed_text = lambda: "#333333"
    themed_tool_card_bg = lambda: "#FFFFFF"
    apply_theme_to_labels = lambda *o: None


class ToolCard(QFrame):
    """工具入口：统一图标、名称、说明和能力标签。"""

    clicked = pyqtSignal(str)

    def __init__(self, tool_id: str, title: str, summary: str, badges=None,
                 parent=None, icon_name: str = "APPLICATION"):
        super().__init__(parent)
        self.tool_id = tool_id
        self._icon_name = icon_name
        self._edit_mode = False
        self._marked_deleted = False
        self._disabled_visual = False
        self.setObjectName("toolCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(title)
        self.setMinimumWidth(240)
        self.setMinimumHeight(176)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)
        self._edit_host = QWidget(self)
        self._edit_row = QHBoxLayout(self._edit_host)
        self._edit_row.setContentsMargins(0, 0, 0, 0)
        self._edit_row.setSpacing(8)
        self.cb = CheckBox("启用", self)
        self._edit_row.addWidget(self.cb)
        self._edit_row.addStretch(1)
        from qfluentwidgets import FluentIcon

        self.btn_del = make_icon_button(FluentIcon.DELETE, "删除工具", self, size=30)
        self.btn_del.clicked.connect(self._toggle_mark_deleted)
        self._edit_row.addWidget(self.btn_del)
        self._edit_host.hide()
        lay.addWidget(self._edit_host)

        identity = QHBoxLayout()
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(12)
        self.icon_label = QLabel(self)
        self.icon_label.setObjectName("toolCardIcon")
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        identity.addWidget(self.icon_label)
        self.t = QLabel(title, self)
        self.t.setWordWrap(True)
        self.t.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.t.setAttribute(Qt.WA_TransparentForMouseEvents)
        identity.addWidget(self.t, 1)
        self.arrow = QLabel("›", self)
        self.arrow.setFixedWidth(16)
        self.arrow.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.arrow.setAttribute(Qt.WA_TransparentForMouseEvents)
        identity.addWidget(self.arrow)
        lay.addLayout(identity)

        self.name_edit = LineEdit(self)
        self.name_edit.setText(str(title or ""))
        self.name_edit.setClearButtonEnabled(False)
        self.name_edit.setPlaceholderText("工具名称")
        self.name_edit.setFixedHeight(32)
        self.name_edit.hide()
        identity.insertWidget(1, self.name_edit, 1)
        self.tags_edit = LineEdit(self)
        self.tags_edit.setClearButtonEnabled(False)
        self.tags_edit.setPlaceholderText("标签，用逗号分隔")
        self.tags_edit.setToolTip("留空使用工具默认标签")
        self.tags_edit.setFixedHeight(32)
        self.tags_edit.hide()
        lay.addWidget(self.tags_edit)

        self.s = QLabel(summary or "打开工具，查看详细设置。", self)
        self.s.setWordWrap(True)
        self.s.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.s.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(self.s, 1)
        self._badges = []
        self._build_badges(badges, lay)
        for label in (self.t, self.s, self.arrow, self.icon_label, *self._badges):
            label.setProperty("themeSemanticColor", True)
        self._refresh_theme()

    def _build_badges(self, badges, lay) -> None:
        if not badges:
            return
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        for badge in badges:
            lab = QLabel(str(badge), self)
            lab.setAttribute(Qt.WA_TransparentForMouseEvents)
            lab.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            row.addWidget(lab)
            self._badges.append(lab)
        row.addStretch(1)
        lay.addLayout(row)

    def set_edit_mode(
        self, on: bool, checked: bool = True, deleted: bool = False,
        tags: str = "",
    ) -> None:
        """保留编辑表单和提交契约；编辑时卡片不触发导航。"""
        self._edit_mode = bool(on)
        self._marked_deleted = bool(deleted)
        self._edit_host.setVisible(self._edit_mode)
        self.cb.setChecked(bool(checked))
        self.name_edit.setVisible(self._edit_mode)
        self.tags_edit.setVisible(self._edit_mode)
        self.tags_edit.setText(str(tags or ""))
        self.t.setVisible(not self._edit_mode)
        self.arrow.setVisible(not self._edit_mode)
        self.setCursor(Qt.ArrowCursor if self._edit_mode else Qt.PointingHandCursor)
        self.setMinimumHeight(252 if self._edit_mode else 176)
        self._update_del_btn()

    def _toggle_mark_deleted(self) -> None:
        self._marked_deleted = not self._marked_deleted
        self._update_del_btn()

    def _update_del_btn(self) -> None:
        from qfluentwidgets import FluentIcon

        text = "撤销删除" if self._marked_deleted else "删除工具"
        self.btn_del.setIcon(FluentIcon.RETURN if self._marked_deleted else FluentIcon.DELETE)
        self.btn_del.setToolTip(text)
        self.btn_del.setAccessibleName(text)
        self._refresh_theme()

    def set_disabled_visual(self, on: bool) -> None:
        """停用的入口仍可打开，其视觉状态跟随主题刷新。"""
        self._disabled_visual = bool(on)
        self._refresh_theme()

    def _card_bg(self) -> str:
        return themed_tool_card_bg()

    def _card_border(self) -> str:
        return themed_input_border()

    def _card_hover_border(self) -> str:
        return themed_accent_text()

    def _card_qss(self) -> str:
        return (
            "QFrame#toolCard{"
            f"border:1px solid {self._card_border()};"
            f"border-radius:10px;background:{self._card_bg()};outline:0;}}"
            "QFrame#toolCard:hover,QFrame#toolCard:focus{"
            f"border:1px solid {self._card_hover_border()};}}"
        )

    def _badge_qss(self):
        return (
            "padding:3px 7px;border:0;border-radius:4px;"
            f"background:{themed_badge_bg()};font-size:11px;"
            f"font-weight:400;color:{themed_secondary_text()};"
        )

    def _refresh_theme(self):
        self.setStyleSheet(self._card_qss())
        disabled = self._disabled_visual or self._marked_deleted
        title_color = themed_disabled_text() if disabled else themed_title_text()
        self.t.setStyleSheet(
            f"background:transparent;color:{title_color};font-size:15px;font-weight:600;"
        )
        self.s.setStyleSheet(
            f"background:transparent;color:{themed_secondary_text()};font-size:12px;"
        )
        self.arrow.setStyleSheet(
            f"background:transparent;color:{themed_disabled_text()};font-size:24px;"
        )
        self.icon_label.setStyleSheet(
            f"background:{themed_badge_bg()};border:0;border-radius:8px;"
        )
        try:
            from qfluentwidgets import FluentIcon

            icon = getattr(FluentIcon, self._icon_name, FluentIcon.APPLICATION)
            color = themed_disabled_text() if disabled else themed_accent_text()
            self.icon_label.setPixmap(icon.icon(color=QColor(color)).pixmap(QSize(20, 20)))
        except Exception:
            self.icon_label.setText("◇")
        for lab in self._badges:
            lab.setStyleSheet(self._badge_qss())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._edit_mode:
                self.clicked.emit(self.tool_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if not self._edit_mode and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit(self.tool_id)
            event.accept()
            return
        super().keyPressEvent(event)


class ToolsFragment(ViewportCappedFragment, QFrame):
    """每个配置账号一份：大厅 + 各工具页栈。

    注意：不用外层 ScrollArea 包整页，避免与工具页内滚动/布局互相抢宽度导致崩溃。
    """

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self._pages: Dict[str, QWidget] = {}
        self._current_tool: Optional[str] = None
        self._last_tool: Optional[str] = None
        self._lobby_ids: List[str] = []
        self._nav_active = False  # 当前是否停留在「工具」导航
        self._settings_expanded = False

        self.setObjectName("toolsFragment")
        # 页面底色随应用，卡片保持统一的中性表面。
        self.setStyleSheet(
            themed_page_transparent_qss("toolsFragment", "toolsHallScroll")
            + "QWidget#toolsHall,QWidget#toolsCardsHost{background:transparent;}"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.StrongFocus)

        # 标题与设置分成两行，让各工具的设置有稳定、独立的可用宽度。
        outer = ViewportCappedVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 20)
        outer.setSpacing(16)
        self.head_host = QWidget(self)
        self.head_host.setObjectName("toolsHeadHost")
        self.head_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        head = QVBoxLayout(self.head_host)
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(12)
        title_row = QWidget(self.head_host)
        title_row.setFixedHeight(48)
        title_lay = QHBoxLayout(title_row)
        title_lay.setContentsMargins(0, 0, 0, 0)
        title_lay.setSpacing(12)
        from qfluentwidgets import FluentIcon

        left_actions = QWidget(title_row)
        left_actions.setFixedWidth(80)
        left_lay = QHBoxLayout(left_actions)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(8)
        self.btn_back = make_icon_button(FluentIcon.LEFT_ARROW, "返回工具大厅 · Esc", left_actions, size=36)
        self.btn_back.setVisible(False)
        self.btn_back.clicked.connect(self.show_hall)
        left_lay.addWidget(self.btn_back)
        left_lay.addStretch(1)
        title_lay.addWidget(left_actions)
        self.title = QLabel("工具", title_row)
        self.title.setMinimumWidth(0)
        self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:26px;font-weight:600;background:transparent;")
        try:
            if config is not None and hasattr(config, "inject"):
                config.inject(self.title, self.tr("工具") + " {name}")
        except Exception:
            pass
        title_lay.addWidget(self.title, 1)
        right_actions = QWidget(title_row)
        right_actions.setFixedWidth(80)
        right_lay = QHBoxLayout(right_actions)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)
        self.btn_settings = make_icon_button(FluentIcon.SETTING, "显示设置", right_actions, size=36)
        self.btn_settings.setCheckable(True)
        self.btn_settings.setToolTip("设置主页入口、显示位置和工具选项")
        self.btn_settings.hide()
        self.btn_settings.clicked.connect(self._toggle_header_settings)
        right_lay.addWidget(self.btn_settings)
        self.btn_next = make_icon_button(FluentIcon.RIGHT_ARROW, "下一个工具", right_actions, size=36)
        self.btn_next.setVisible(False)
        self.btn_next.clicked.connect(self.open_next_tool)
        right_lay.addWidget(self.btn_next)
        title_lay.addWidget(right_actions)
        head.addWidget(title_row)

        self.settings_scroll = QScrollArea(self.head_host)
        self.settings_scroll.setObjectName("toolHeaderSettingsScroll")
        self.settings_scroll.setFrameShape(QFrame.NoFrame)
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.settings_scroll.setFixedHeight(60)
        self.settings_scroll.setStyleSheet(
            "QScrollArea#toolHeaderSettingsScroll{background:transparent;border:none;}"
            + themed_scrollbar_qss()
        )
        self.settings_scroll.viewport().setStyleSheet("background:transparent;")
        self.settings_host = QWidget()
        self.settings_host.setObjectName("toolHeaderSettings")
        self.settings_host.setAttribute(Qt.WA_StyledBackground, True)
        self.settings_lay = QHBoxLayout(self.settings_host)
        self.settings_lay.setContentsMargins(16, 10, 16, 10)
        self.settings_lay.setSpacing(28)
        self.settings_lay.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.settings_scroll.setWidget(self.settings_host)
        self.settings_host.setAutoFillBackground(False)
        self.settings_scroll.hide()
        head.addWidget(self.settings_scroll)
        outer.addWidget(self.head_host)

        self.stack = QStackedWidget(self)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer.addWidget(self.stack, 1)

        self.hall = QWidget()
        self.hall.setObjectName("toolsHall")
        self.hall.setStyleSheet("QWidget#toolsHall{background:transparent;}")
        hall_l = QVBoxLayout(self.hall)
        hall_l.setContentsMargins(0, 0, 0, 0)
        hall_l.setSpacing(18)
        hall_head_host = QWidget(self.hall)
        hall_head_host.setObjectName("toolsHallHead")
        hall_head = QHBoxLayout(hall_head_host)
        hall_head.setContentsMargins(0, 0, 0, 0)
        hall_head.setSpacing(12)
        intro = QVBoxLayout()
        intro.setContentsMargins(0, 0, 0, 0)
        intro.setSpacing(6)
        section_row = QHBoxLayout()
        section_row.setSpacing(8)
        self.hall_section = QLabel("所有工具", hall_head_host)
        self.hall_section.setStyleSheet("font-size:16px;font-weight:600;")
        section_row.addWidget(self.hall_section)
        self.tool_count = QLabel("", hall_head_host)
        self.tool_count.setStyleSheet("font-size:12px;")
        section_row.addWidget(self.tool_count)
        section_row.addStretch(1)
        intro.addLayout(section_row)
        self.hall_sub = QLabel("选择工具开始工作，按 Esc 返回此处。", hall_head_host)
        self.hall_sub.setWordWrap(True)
        self.hall_sub.setStyleSheet("font-size:12px;background:transparent;")
        self._hall_sub_text = self.hall_sub.text()
        for label in (self.title, self.hall_section, self.hall_sub, self.tool_count):
            label.setProperty("themeSemanticColor", True)
        intro.addWidget(self.hall_sub)
        hall_head.addLayout(intro, 1)
        self.btn_tool_cancel = make_icon_button(FluentIcon.CLOSE, "取消更改", hall_head_host)
        self.btn_tool_cancel.setVisible(False)
        self.btn_tool_cancel.clicked.connect(self._exit_edit_mode)
        hall_head.addWidget(self.btn_tool_cancel, 0, Qt.AlignTop)
        self.btn_tool_edit = make_icon_button(FluentIcon.EDIT, "管理工具", hall_head_host, primary=True)
        self.btn_tool_edit.clicked.connect(self._toggle_edit_mode)
        hall_head.addWidget(self.btn_tool_edit, 0, Qt.AlignTop)
        hall_l.addWidget(hall_head_host)
        self._hall_head_spacing = 12

        self.hall_scroll = QScrollArea(self.hall)
        self.hall_scroll.setObjectName("toolsHallScroll")
        self.hall_scroll.setWidgetResizable(True)
        self.hall_scroll.setFrameShape(QFrame.NoFrame)
        self.hall_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hall_scroll.setStyleSheet(
            "QScrollArea#toolsHallScroll{background:transparent;border:none;}"
            + themed_scrollbar_qss()
        )
        try:
            self.hall_scroll.viewport().setStyleSheet("background:transparent;")
        except Exception:
            pass
        self.cards_host = QWidget()
        self.cards_host.setObjectName("toolsCardsHost")
        self.cards_host.setStyleSheet("QWidget#toolsCardsHost{background:transparent;}")
        self.cards_grid = QGridLayout(self.cards_host)
        self.cards_grid.setContentsMargins(0, 0, 4, 4)
        self.cards_grid.setHorizontalSpacing(16)
        self.cards_grid.setVerticalSpacing(16)
        self.cards_grid.setAlignment(Qt.AlignTop)
        self._grid_columns = 0
        self.hall_scroll.setWidget(self.cards_host)
        hall_l.addWidget(self.hall_scroll, 1)

        # 底部右下角：「恢复已删除插件」（编辑模式且存在已删除插件时出现）
        restore_row = QWidget(self.hall)
        rl = QHBoxLayout(restore_row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        rl.addStretch(1)
        self.btn_restore = make_icon_button(FluentIcon.HISTORY, "恢复已删除工具", restore_row)
        self.btn_restore.setVisible(False)
        self.btn_restore.clicked.connect(self._open_restore_dialog)
        rl.addWidget(self.btn_restore, 0)
        hall_l.addWidget(restore_row)

        self.stack.addWidget(self.hall)  # index 0

        self._load_cards()

        self.object_name = md5(f"{time.time()}%{random()}".encode("utf-8")).hexdigest()
        self.setObjectName(f"{self.object_name}.ToolsFragment")

        # Esc 全局过滤（仅本 fragment 可见时）
        try:
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
        except Exception:
            pass

        # 深色模式适配（统一刷：labels/输入框/QFrame白底/ToolCard._refresh_theme 等）
        if apply_full_theme_refresh is not None:
            self._theme_seen = is_dark()
            apply_full_theme_refresh(self)
            self._refresh_theme()
            # 切主题时只刷可见 fragment（其他账号的页由 showEvent 按需补刷）
            safe_connect_theme(
                self,
                self._apply_theme_full_if_visible,
                light_callback=self._apply_theme_light_if_visible,
            )

    # ---------- 事件 / 导航 ----------
    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                if self.isVisible() and self._current_tool:
                    self.show_hall()
                    return True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def on_nav_selected(self, already_on_tools: bool = False) -> None:
        """左侧点了「工具」。already_on_tools=True 表示本来就在工具导航。

        记忆规则：
        - 离开工具时若正开着某个插件 → 回来继续该插件
        - 若已主动回大厅（_last_tool 已清）→ 回来仍是大厅，不强制重开
        """
        self._nav_active = True
        try:
            self.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass
        # 主页入口已 open_tool：跳过本次恢复，避免顶栏二次挂载上浮
        if getattr(self, "_skip_next_nav_open", False):
            self._skip_next_nav_open = False
            return
        if already_on_tools:
            # 再点一次工具 → 回大厅（并清记忆，避免之后从主页又强制打开）
            if self._current_tool:
                self.show_hall()
            return
        # 从其它导航回来：
        # 仍停在某插件页（_current_tool 还在）→ 什么都不做，保持现状
        if self._current_tool:
            return
        # 主动回过大厅 → _last_tool 已空 → 大厅
        # 离开时插件仍开着 → _last_tool 有值且栈页还在 → 恢复（不重复 mount）
        if self._last_tool:
            self.open_tool(self._last_tool)
        else:
            self.show_hall()

    def on_nav_left(self) -> None:
        """离开工具导航：若当前开着插件，记下以便回来恢复。"""
        self._nav_active = False
        try:
            if self._current_tool:
                self._last_tool = self._current_tool
            # 已在大厅：_last_tool 保持 show_hall 清掉的空，回来仍大厅
        except Exception:
            pass

    # ---------- 大厅 ----------
    def _perm_badges(self, tool) -> list:
        # 用户在编辑模式改过的标签优先（逗号分隔）
        try:
            from module.tools.registry import get_tool_tags_override

            ov = get_tool_tags_override(tool.id)
            if ov:
                return [x.strip() for x in ov.replace("，", ",").split(",") if x.strip()]
        except Exception:
            pass
        mapping = {
            "scheduler": "调度",
            "device": "模拟器",
            "ocr": "识别",
        }
        out = []
        for p in tool.permissions or []:
            out.append(mapping.get(str(p), str(p)))
        if getattr(tool, "kind", "") == "local":
            out.append("仅本地")
        return out

    # ---------- 工具启用与修改（编辑模式） ----------
    def _toggle_edit_mode(self) -> None:
        if getattr(self, "_edit_mode", False):
            self._exit_edit_mode(apply=True)
        else:
            self._enter_edit_mode()

    _EDIT_DESC_TEXT = "调整启用状态、名称和标签后保存。删除的工具可恢复，重启后生效。"

    def _enter_edit_mode(self) -> None:
        self._edit_mode = True
        # 说明换文字显示在同一固定框里；「工具」标题行、卡片位置都不动
        try:
            self.hall_sub.setText(self._EDIT_DESC_TEXT)
            # 换字后重测（测量基准含编辑态，高度应不变；此处校正宽度漂移）
            from PyQt5.QtCore import QTimer as _QT

            _QT.singleShot(0, self._fit_hall_head_height)
        except Exception:
            pass
        try:
            from qfluentwidgets import FluentIcon

            self.btn_tool_edit.setIcon(FluentIcon.SAVE)
            self.btn_tool_edit.setToolTip("保存更改")
            self.btn_tool_edit.setAccessibleName("保存更改")
            self.btn_tool_cancel.setVisible(True)
        except Exception:
            pass
        try:
            self._sync_restore_btn()
        except Exception:
            pass
        try:
            self._load_cards()
        except Exception as e:
            print("[tools] enter edit mode failed:", e)

    def _exit_edit_mode(self, *args, apply: bool = False) -> None:
        was_edit = bool(getattr(self, "_edit_mode", False))
        self._edit_mode = False
        any_deleted = False
        state_changed = False
        if was_edit and apply:
            try:
                from module.tools.registry import (
                    is_tool_enabled as _is_enabled,
                    is_tool_deleted as _is_deleted,
                    set_tool_state as _set_state,
                    get_registry as _get_registry,
                )

                reg = _get_registry()
                for i in range(self.cards_grid.count()):
                    item = self.cards_grid.itemAt(i)
                    card = item.widget() if item is not None else None
                    if card is None or not hasattr(card, "tool_id"):
                        continue
                    tid = str(card.tool_id)
                    enabled = bool(card.cb.isChecked())
                    label = str(card.name_edit.text() or "").strip()
                    tags = str(card.tags_edit.text() or "").strip()
                    if enabled != _is_enabled(tid):
                        state_changed = True
                    if getattr(card, "_marked_deleted", False) and not _is_deleted(tid):
                        any_deleted = True
                    _set_state(tid, enabled=enabled, label=label, tags=tags)
                    if getattr(card, "_marked_deleted", False):
                        _set_state(tid, deleted=True)
                    # 名称/标签即时写回注册表实例（覆盖属性，""=回清单默认）
                    tool = reg.get(tid)
                    if tool is not None:
                        tool._label_override = label
                        tool._tags_override = tags
                    # 页面缓存里的停用灰条即时同步（补挂/摘除都覆盖）
                    self._sync_page_banner(self._pages.get(tid), tid)
                    # 当前打开的页面：顶栏设置立即重挂（通用方法）
                    self._remount_header_for(tid)
            except Exception as e:
                print("[tools] apply plugin state failed:", e)
        try:
            self.hall_sub.setText(self._hall_sub_text)
            from PyQt5.QtCore import QTimer as _QT

            _QT.singleShot(0, self._fit_hall_head_height)
            from qfluentwidgets import FluentIcon

            self.btn_tool_edit.setIcon(FluentIcon.EDIT)
            self.btn_tool_edit.setToolTip("管理工具")
            self.btn_tool_edit.setAccessibleName("管理工具")
            self.btn_tool_cancel.setVisible(False)
        except Exception:
            pass
        try:
            self._sync_restore_btn()
        except Exception:
            pass
        try:
            self._load_cards()
        except Exception as e:
            print("[tools] exit edit mode reload failed:", e)
        if was_edit and apply:
            if state_changed:
                # 启用/停用即时生效：主页板块与启停栏控件现场重挂
                self._refresh_home_live()
            if any_deleted:
                self._ask_restart_after_disable()
            else:
                self._toast("已应用", "已应用，启用状态与标签即时生效。")

    def _remount_header_for(self, tool_id: str) -> None:
        """应用启用变化后的通用重挂：当前正打开的页面立即重刷顶栏设置。

        任何插件页只要声明 header_settings_widgets，启用/停用/恢复后都走这
        一条路——不针对单个插件写特判。
        """
        try:
            page = self._pages.get(tool_id)
            if page is None:
                return
            if str(tool_id) != str(getattr(self, "_current_tool", None) or ""):
                return
            self._mount_header_settings(page)
        except Exception as e:
            print("[tools] remount header failed:", e)

    def _sync_page_banner(self, page: QWidget, tool_id: str) -> None:
        """页面停用灰条：非启用显示/启用隐藏；缓存页也即时补挂/摘除。"""
        if page is None:
            return
        try:
            from module.tools.registry import is_tool_enabled

            disabled = not is_tool_enabled(tool_id)
        except Exception:
            return
        try:
            from PyQt5 import sip
        except Exception:
            sip = None
        banner = getattr(page, "_disabled_banner", None)
        if banner is not None and sip is not None:
            try:
                if sip.isdeleted(banner):
                    banner = None
                    page._disabled_banner = None
            except Exception:
                pass
        try:
            if disabled and banner is None:
                banner = QLabel(
                    "此插件已非启用：不参与执行，主页贡献已隐藏；"
                    "可在「管理工具」重新启用，即时生效。",
                    page,
                )
                banner.setWordWrap(True)
                banner.setStyleSheet(
                    "QLabel{background:%s;color:%s;"
                    'font-family:"Microsoft YaHei";font-size:12px;font-weight:700;'
                    "padding:6px 12px;border-radius:6px;}" % (themed_disabled_strip(), themed_text())
                )
                lay = page.layout()
                if lay is not None:
                    lay.insertWidget(0, banner)
                    page._disabled_banner = banner
            if banner is not None:
                banner.setVisible(bool(disabled))
        except Exception as e:
            print("[tools] banner sync failed:", e)

    def _fit_hall_head_height(self) -> None:
        """让说明按实际宽度换行，管理按钮保持在说明右上方。"""
        try:
            self.hall_sub.updateGeometry()
            host = self.hall_sub.parentWidget()
            if host is not None and host.layout() is not None:
                host.layout().invalidate()
                host.updateGeometry()
        except Exception:
            pass

    def _refresh_home_live(self) -> None:
        """启用/停用即时生效：主页插件区与启停栏控件现场重挂。"""
        try:
            home = getattr(self.window(), "homeInterface", None)
            if home is None:
                return
            for m in (
                "refresh_home_plugins",
                "_sync_home_assets_switch_entry",
                "_sync_home_edit_entry_btn",
            ):
                fn = getattr(home, m, None)
                if callable(fn):
                    fn()
        except Exception as e:
            print("[tools] live home refresh failed:", e)

    def _sync_restore_btn(self) -> None:
        """编辑模式且存在已删除插件时，右下角显示「恢复已删除插件」。"""
        try:
            if not getattr(self, "_edit_mode", False):
                self.btn_restore.setVisible(False)
                return
            from module.tools.registry import deleted_tool_ids

            self.btn_restore.setVisible(bool(deleted_tool_ids()))
        except Exception:
            self.btn_restore.setVisible(False)

    def _open_restore_dialog(self) -> None:
        """恢复已删除插件：配置卡同款 MessageBox + qt 原生 checkbox 多选，
        恢复勾选的那些；恢复后顺带问是否同时启用。"""
        try:
            if MessageBox is None:
                return
            from PyQt5.QtWidgets import QCheckBox

            from module.tools.registry import (
                deleted_tool_ids,
                get_registry,
                set_tool_state,
            )

            ids = sorted(deleted_tool_ids())
            if not ids:
                self._toast("没有已删除的插件", "")
                return
            w = MessageBox("恢复已删除插件", "勾选要恢复的插件：", self.window())
            boxes = []
            for tid in ids:
                tool = get_registry().get(tid)
                name = str(getattr(tool, "name", tid) if tool is not None else tid)
                cb = QCheckBox(name, w)
                cb.setChecked(True)
                # qfw 1.2.0 MessageBox 没有 viewLayout，勾选行挂 textLayout
                w.textLayout.addWidget(cb)
                boxes.append((tid, cb))
            w.yesButton.setText("恢复")
            w.cancelButton.setText("取消")
            if not w.exec_():
                return
            picked = [tid for tid, cb in boxes if cb.isChecked()]
            if not picked:
                self._toast("未选择", "没有勾选任何要恢复的插件。")
                return
            for tid in picked:
                set_tool_state(tid, deleted=False)
            # 恢复后顺带问是否启用，免得再手动勾一次
            w2 = MessageBox("恢复完成", "是否同时启用恢复的插件？", self.window())
            w2.yesButton.setText("启用")
            w2.cancelButton.setText("暂不启用")
            enable = bool(w2.exec_())
            if enable:
                for tid in picked:
                    set_tool_state(tid, enabled=True)
            self._sync_restore_btn()
            self._load_cards()
            self._refresh_home_live()
            self._toast(
                "已恢复",
                "已恢复 %d 个插件%s。" % (len(picked), "并启用" if enable else "（保持非启用）"),
            )
        except Exception as e:
            print("[tools] restore dialog failed:", e)

    def _ask_restart_after_disable(self) -> None:
        """非启用插件后询问是否重启；取消也提示需重启生效。"""
        if MessageBox is not None:
            try:
                w = MessageBox("应用成功", "非启用了插件，请问是否重启。", self.window())
                w.yesButton.setText("重启")
                w.cancelButton.setText("取消")
                yes = bool(w.exec_())
                if yes:
                    if self._restart_app():
                        return
                    # 重启失败 → 提示手动重启
                self._toast("已应用", "已应用，请重启程序生效。")
                return
            except Exception as e:
                print("[tools] restart dialog failed:", e)
        self._toast("已应用", "已应用，请重启程序生效。")

    def _restart_app(self) -> bool:
        """重启程序（frozen=直接拉起 exe；源码=同解释器重跑入口脚本）。"""
        try:
            import os
            import sys
            from PyQt5.QtCore import QProcess

            exe = sys.executable
            if getattr(sys, "frozen", False):
                args, cwd = [], os.path.dirname(os.path.abspath(exe))
            else:
                entry = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
                if not entry or not os.path.isfile(entry):
                    return False
                args, cwd = [entry], os.path.dirname(entry)
            ok = bool(QProcess.startDetached(exe, args, cwd))
            if ok:
                app = QApplication.instance()
                if app is not None:
                    app.quit()
            return ok
        except Exception as e:
            print("[tools] restart failed:", e)
            return False

    def _toast(self, title: str, content: str) -> None:
        # 统一走商店右上角 toast 的通用方法（notification.saved）
        try:
            from gui.util import notification

            notification.saved(self.config, title, content, duration=3000)
            return
        except Exception as e:
            print("[tools] toast via notification failed:", e)
        try:
            if InfoBar is not None:
                InfoBar.success(
                    title=title,
                    content=content,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position="TOP",
                    duration=3500,
                    parent=self.window(),
                )
        except Exception as e:
            print("[tools] toast failed:", e)

    def _clear_grid(self) -> None:
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            w = item.widget() if item is not None else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _load_cards(self):
        self._clear_grid()
        self._lobby_ids = []
        try:
            from module.tools.registry import get_registry

            reg = get_registry()
            tools = reg.list_lobby_tools() if hasattr(reg, "list_lobby_tools") else reg.list_tools()
            errors = dict(reg.errors or {})
        except Exception as e:
            tools = []
            errors = {"_": str(e)}

        self.tool_count.setText("%d 个" % len(tools))
        if not tools and not errors:
            lab = QLabel("还没有可用工具。", self.cards_host)
            self.cards_grid.addWidget(lab, 0, 0)
            return

        cols = self._card_columns()
        self._grid_columns = cols

        r = c = 0
        edit_mode = bool(getattr(self, "_edit_mode", False))
        try:
            from module.tools.registry import is_tool_enabled, is_tool_deleted, get_tool_tags_override
        except Exception:
            is_tool_enabled = is_tool_deleted = get_tool_tags_override = None
        for t in tools:
            self._lobby_ids.append(t.id)
            card = ToolCard(
                t.id,
                t.name,
                t.summary,
                badges=self._perm_badges(t),
                parent=self.cards_host,
                icon_name=str(getattr(t, "icon_name", "APPLICATION")),
            )
            card.clicked.connect(self.open_tool)
            if is_tool_enabled is not None:
                try:
                    card.set_disabled_visual(not is_tool_enabled(t.id))
                except Exception:
                    pass
            if edit_mode and is_tool_enabled is not None:
                try:
                    card.set_edit_mode(
                        True,
                        checked=is_tool_enabled(t.id),
                        deleted=is_tool_deleted(t.id),
                        tags=get_tool_tags_override(t.id),
                    )
                except Exception:
                    pass
            self.cards_grid.addWidget(card, r, c)
            c += 1
            if c >= cols:
                c = 0
                r += 1

        for tid, err in errors.items():
            if str(tid).startswith("_"):
                continue
            card = ToolCard(
                tid,
                f"{tid}（加载失败已禁用）",
                str(err)[:120],
                badges=["加载失败"],
                parent=self.cards_host,
            )
            card.setEnabled(False)
            self.cards_grid.addWidget(card, r, c)
            c += 1
            if c >= cols:
                c = 0
                r += 1

        for i in range(4):
            self.cards_grid.setColumnStretch(i, 1 if i < cols else 0)

    def _card_columns(self) -> int:
        """卡片随视口在一至三列间切换，不把说明挤成狭窄长条。"""
        width = self.hall_scroll.viewport().width()
        if width < 200:
            width = max(240, self.width() - 48)
        return max(1, min(3, (width + 16) // 280))

    def _relayout_cards(self) -> None:
        """只移动现有卡片，窗口缩放时保留未保存的编辑内容。"""
        if not hasattr(self, "cards_grid"):
            return
        cols = self._card_columns()
        if cols == self._grid_columns:
            return
        widgets = []
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item is not None and item.widget() is not None:
                widgets.append(item.widget())
        for index, widget in enumerate(widgets):
            self.cards_grid.addWidget(widget, index // cols, index % cols)
        for index in range(4):
            self.cards_grid.setColumnStretch(index, 1 if index < cols else 0)
        self._grid_columns = cols

    def _make_base_home_cells(self, tool):
        """基层主页设置组：主页显示开关 + 主页栏位单选（构建一次复用）。

        给未自带 header_settings_widgets 的插件兜底；囤体/资产/装备/推送
        已自带（含各自专用开关），框架不重复注入。
        """
        cells = []
        sw_cell = self._make_home_visible_switch(tool)
        if sw_cell is not None:
            cells.append(sw_cell)
        # 栏1/栏2 同样默认发放：自动入口与声明板块都吃这个选择
        try:
            from gui.components.expand.tool_style import make_home_bar_slot_cell

            slot = make_home_bar_slot_cell(str(tool.id))
            if slot is not None:
                cells.append(slot)
        except Exception as e:
            print("[tools] base slot cell failed:", e)
        return cells

    def _make_home_visible_switch(self, tool=None):
        """框架级「主页显示」开关格：有主页贡献的插件默认拥有（构建一次复用）。

        样式走主题引擎 make_header_setting_cell（与四页顶栏开关格同一实现）；
        键 = tool_<id>_home_visible，默认开；切换即时重挂主页板块。
        """
        if tool is None:
            tool_id = str(getattr(self, "_current_tool", "") or "")
            if not tool_id:
                return None
            try:
                from module.tools.registry import get_registry

                tool = next(
                    (t for t in get_registry().list_tools() if str(t.id) == tool_id),
                    None,
                )
            except Exception:
                tool = None
        if tool is None:
            return None
        # 所有插件都能自动发主页入口（未声明 home 的由框架发入口卡），
        # 因此开关永远可用，不置灰
        cache = getattr(self, "_home_vis_cells", None)
        if cache is None:
            cache = {}
            self._home_vis_cells = cache
        _cid = str(tool.id)
        if _cid in cache:
            try:
                # 缓存页可能已随设置栏卸载而销毁。
                cache[_cid].objectName()
            except RuntimeError:
                cache.pop(_cid, None)
            else:
                return cache[_cid]
        try:
            from qfluentwidgets import SwitchButton as _SW
        except Exception:
            return None
        sw = _SW()
        try:
            sw.setOnText("开")
            sw.setOffText("关")
        except Exception:
            pass
        from module.tools.base import _cfg_bool

        key = f"{tool.config_prefix}home_visible"
        try:
            sw.setChecked(bool(_cfg_bool(self.config, key, True)))
        except Exception:
            sw.setChecked(True)

        def _on(checked, _key=key):
            try:
                self._set_tool_cfg(_key, bool(checked))
            except Exception as e:
                print("[tools] home-visible write failed:", e)
            self._refresh_home_live()

        try:
            sw.checkedChanged.connect(_on)
        except Exception:
            pass
        try:
            from gui.components.expand.tool_style import make_header_setting_cell

            cell = make_header_setting_cell(
                "主页显示", sw, obj_name="homeEditHeaderCell"
            )
        except Exception as e:
            print("[tools] home-visible cell failed:", e)
            return None
        if cell is None:
            return None
        cache[_cid] = cell
        return cell

    def _set_tool_cfg(self, key, value):
        """写工具配置键并落盘（统一走 module/tools/base 的 _cfg_set）。"""
        try:
            from module.tools.base import _cfg_set as _base_cfg_set

            _base_cfg_set(self.config, key, value)
        except Exception as e:
            print("[tools] cfg set failed:", key, e)

    def _make_auto_settings_button(self, tool):
        """config_defaults 声明 → 顶栏「插件设置」按钮（作者零 Qt 的设置页）。"""
        try:
            entries = tool.auto_settings_entries()
            if not entries:
                return None

            def _open():
                try:
                    from module.tools.auto_settings import open_settings_dialog

                    open_settings_dialog(tool, self.config, self)
                except Exception as e:
                    print("[tools] auto settings dialog failed:", e)

            from qfluentwidgets import PushButton as _PB

            btn = _PB("插件设置", self.settings_host)
            btn.clicked.connect(_open)
            return btn
        except Exception as e:
            print("[tools] auto settings button failed:", e)
            return None

    def _refresh_theme(self) -> None:
        self.settings_host.setStyleSheet(
            f"QWidget#toolHeaderSettings{{background:{themed_section_body_bg()};"
            f"border:1px solid {themed_input_border()};border-radius:8px;}}"
        )
        self.title.setStyleSheet(
            f"font-size:26px;font-weight:600;background:transparent;color:{themed_title_text()};"
        )
        self.hall_section.setStyleSheet(
            f"font-size:16px;font-weight:600;background:transparent;color:{themed_title_text()};"
        )
        for label in (self.hall_sub, self.tool_count):
            label.setStyleSheet(
                f"font-size:12px;background:transparent;color:{themed_secondary_text()};"
            )

    def _apply_theme_full_if_visible(self) -> None:
        if self.isVisible():
            self._theme_seen = is_dark()
            apply_full_theme_refresh(self)
            self._refresh_theme()

    def _apply_theme_light_if_visible(self) -> None:
        if self.isVisible():
            apply_theme_to_labels(self)
            self._refresh_theme()

    def _clear_header_settings(self) -> None:
        """收起设置并归还给缓存页，保留开关的信号连接与状态。"""
        try:
            while self.settings_lay.count():
                item = self.settings_lay.takeAt(0)
                w = item.widget() if item is not None else None
                if w is not None:
                    owner = getattr(w, "_tool_header_owner", None)
                    if owner is not None:
                        w.setParent(owner)
                        w.hide()
                        continue
                    cache = getattr(self, "_home_vis_cells", {})
                    for tool_id, cached in list(cache.items()):
                        if cached is w:
                            cache.pop(tool_id, None)
                    w.setParent(None)
                    w.deleteLater()
        except Exception:
            pass
        try:
            self.settings_scroll.setVisible(False)
            self.btn_settings.hide()
            self.settings_host.updateGeometry()
        except Exception:
            pass

    def _toggle_header_settings(self, expanded: bool) -> None:
        self._settings_expanded = bool(expanded)
        self.settings_scroll.setVisible(self._settings_expanded and bool(self._current_tool))

    def _mount_header_settings(self, page: QWidget) -> None:
        """从工具页挂载 header 设置控件到标题行右侧。"""
        self._clear_header_settings()
        inner = None
        try:
            # _create_tool_page 包了一层 wrap；设置挂在真正的 Layout 上。
            # 通用契约：按"能力"探测（谁有 header_settings_widgets 谁就是页面
            # 本体），不依赖 itemAt(0) 位置——页面顶层随后可能插入停用灰条等。
            lay = page.layout() if page is not None else None
            if lay is not None:
                for i in range(lay.count()):
                    cand = lay.itemAt(i).widget()
                    if cand is not None and cand is not page and hasattr(
                        cand, "header_settings_widgets"
                    ):
                        inner = cand
                        break
        except Exception:
            inner = None
        if inner is None:
            inner = page
        cached = getattr(page, "_tools_header_cells", None)
        if cached is not None:
            from PyQt5 import sip

            if any(sip.isdeleted(w) for w in cached):
                cached = None
        widgets = list(cached or [])
        if cached is None:
            try:
                if inner is not None and hasattr(inner, "header_settings_widgets"):
                    widgets = list(inner.header_settings_widgets() or [])
            except Exception as e:
                print("[tools] header settings failed:", e)
        # 框架基层设置注入：所有工具页的设置栏自动获得「主页显示」开关；
        # 有主页贡献的再带「主页栏位」单选（栏1=标题下/栏2=启停下）。
        # 仅当页面未自带 header_settings_widgets 时注入——自带者由插件作者
        # 全权负责（囤体主页拦截、资产入口等专用开关不受影响，避免重复）。
        try:
            if cached is None and not widgets:
                tool_id = str(getattr(self, "_current_tool", "") or "")
                from module.tools.registry import get_registry

                tool = next(
                    (t for t in get_registry().list_tools() if str(t.id) == tool_id),
                    None,
                )
                if tool is not None:
                    widgets = self._make_base_home_cells(tool) + widgets
                    gear = self._make_auto_settings_button(tool)
                    if gear is not None:
                        widgets.append(gear)
        except Exception as e:
            print("[tools] base home cells inject failed:", e)
        page._tools_header_cells = widgets
        for w in widgets:
            try:
                w._tool_header_owner = page
                w.setParent(self.settings_host)
                self.settings_lay.addWidget(w, 0, Qt.AlignVCenter)
                w.show()
            except Exception:
                pass
        try:
            self.settings_lay.addStretch(1)
            self.settings_host.setVisible(True)
            self.btn_settings.setVisible(bool(widgets))
            self.btn_settings.setChecked(self._settings_expanded)
            self.settings_scroll.setVisible(bool(widgets) and self._settings_expanded)
            self.settings_host.updateGeometry()
            if getattr(self, "head_host", None) is not None:
                self.head_host.updateGeometry()
        except Exception:
            pass

    def show_hall(self):
        """主动回大厅：清掉上次插件记忆，之后从主页回工具不再强制重开。"""
        if getattr(self, "_edit_mode", False):
            try:
                self._exit_edit_mode(apply=False)
            except Exception:
                self._edit_mode = False
        self._current_tool = None
        self._last_tool = None
        self.btn_back.setVisible(False)
        self.btn_next.setVisible(False)
        self._clear_header_settings()
        try:
            self.title.setText("工具")
        except Exception:
            pass
        self.stack.setCurrentWidget(self.hall)
        try:
            self._load_cards()
        except Exception as e:
            print("[tools] reload hall failed:", e)

    def open_tool(self, tool_id: str):
        if not tool_id:
            return
        try:
            page_existing = self._pages.get(tool_id)
            # 已在同一工具页且栈也是它：不重复挂顶栏（防二次上浮）
            if (
                str(tool_id) == str(getattr(self, "_current_tool", None) or "")
                and page_existing is not None
                and self.stack.currentWidget() is page_existing
            ):
                self._last_tool = tool_id
                return
            # 页面已创建、只是从大厅/其它导航切回来：只切栈，顶栏若已是该页设置则不重挂
            page = page_existing
            need_mount = True
            if page is None:
                try:
                    from module.tools.registry import is_tool_deleted

                    if is_tool_deleted(tool_id):
                        return
                except Exception:
                    pass
                page = self._create_tool_page(tool_id)
                if page is None:
                    return
                self._pages[tool_id] = page
                self.stack.addWidget(page)
                need_mount = True
            else:
                # 若顶栏已经挂着且 current 即将是它，仍可能是从大厅回来——顶栏被 show_hall 清过，要重挂
                need_mount = True
            # 停用灰条每次打开都校（缓存页也即时补挂/摘除）
            try:
                self._sync_page_banner(page, tool_id)
            except Exception:
                pass
            self._current_tool = tool_id
            self._last_tool = tool_id
            self.btn_back.setVisible(True)
            self._update_next_btn()
            try:
                from module.tools.registry import get_registry

                t = get_registry().get(tool_id)
                self.title.setText(t.name if t else tool_id)
            except Exception:
                self.title.setText(tool_id)
            if need_mount:
                self._mount_header_settings(page)
            self.stack.setCurrentWidget(page)
            # 缓存页在主题切换时被遍历跳过（隐藏页不刷），切回为当前页时补一次；
            # 样式已同步时 set_style_dedup 令其为近零成本。
            try:
                from gui.components.expand.tool_style import apply_full_theme_refresh as _afr

                _afr(page)
            except Exception:
                pass
            # 切页后内容区 scroll 归零,避免点控件时布局重算导致页面上移
            try:
                for _sa in page.findChildren(QScrollArea):
                    try:
                        _sa.verticalScrollBar().setValue(0)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            print("[tools] open_tool failed:", tool_id, e)
            # 失败时回大厅，避免空白崩溃态
            try:
                err = QLabel("打开失败：%s" % e, self)
                err.setWordWrap(True)
                wrap = QWidget()
                QVBoxLayout(wrap).addWidget(err)
                self._pages[tool_id] = wrap
                self.stack.addWidget(wrap)
                self.stack.setCurrentWidget(wrap)
                self._current_tool = tool_id
                self._last_tool = tool_id
                self.btn_back.setVisible(True)
                self._clear_header_settings()
            except Exception:
                self.show_hall()

    def open_next_tool(self):
        ids = list(self._lobby_ids or [])
        if not ids:
            try:
                from module.tools.registry import get_registry

                ids = [t.id for t in get_registry().list_lobby_tools()]
            except Exception:
                ids = []
        if not ids:
            self.show_hall()
            return
        cur = self._current_tool or ""
        try:
            i = ids.index(cur)
            nxt = ids[(i + 1) % len(ids)]
        except ValueError:
            nxt = ids[0]
        self.open_tool(nxt)

    def _update_next_btn(self) -> None:
        ids = list(self._lobby_ids or [])
        if not ids:
            try:
                from module.tools.registry import get_registry

                ids = [t.id for t in get_registry().list_lobby_tools()]
                self._lobby_ids = ids
            except Exception:
                ids = []
        if not ids or not self._current_tool:
            self.btn_next.setVisible(False)
            return
        try:
            i = ids.index(self._current_tool)
            nxt_id = ids[(i + 1) % len(ids)]
        except ValueError:
            nxt_id = ids[0]
        name = nxt_id
        try:
            from module.tools.registry import get_registry

            t = get_registry().get(nxt_id)
            if t is not None:
                name = t.name
        except Exception:
            pass
        self.btn_next.setToolTip("下一个工具：%s" % name)
        self.btn_next.setAccessibleName("下一个工具：%s" % name)
        self.btn_next.setVisible(True)

    def _create_tool_page(self, tool_id: str) -> Optional[QWidget]:
        try:
            from module.tools.registry import get_registry

            tool = get_registry().get(tool_id)
            if tool is None:
                return None
            wrap = QWidget()
            wrap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            lay = QVBoxLayout(wrap)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            try:
                inner = tool.build_widget(parent=wrap, config=self.config)
            except Exception as e:
                err = QLabel("工具界面加载失败：%s" % e, wrap)
                err.setWordWrap(True)
                lay.addWidget(err)
                return wrap
            if inner is None:
                lay.addWidget(QLabel("工具未返回界面。", wrap))
            else:
                try:
                    inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                except Exception:
                    pass
                lay.addWidget(inner, 1)
            return wrap
        except Exception as e:
            w = QWidget()
            QVBoxLayout(w).addWidget(QLabel("打开失败：%s" % e, w))
            return w

    def showEvent(self, e):
        super().showEvent(e)
        # 首次真正显示后布局宽度才可信：重测说明框高度
        try:
            from PyQt5.QtCore import QTimer as _QT

            _QT.singleShot(0, self._fit_hall_head_height)
            _QT.singleShot(0, self._relayout_cards)
        except Exception:
            pass
        # 本 fragment 不可见期间错过的主题切换：显示时按需补一次全量刷新
        try:
            if getattr(self, "_theme_seen", is_dark()) != is_dark():
                self._theme_seen = is_dark()
                apply_full_theme_refresh(self)
                self._refresh_theme()
        except Exception:
            pass

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # 只重排卡片，保留管理模式下尚未保存的输入。
        try:
            if self._current_tool is None and self.stack.currentWidget() is self.hall:
                self._relayout_cards()
        except Exception:
            pass
        # 窗口变化 → 说明文字换行数可能变：实测重算说明框高度
        try:
            from PyQt5.QtCore import QTimer as _QT

            _QT.singleShot(0, self._fit_hall_head_height)
        except Exception:
            pass
