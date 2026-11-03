# -*- coding: utf-8 -*-
"""auto_push 插件私有编队面板：「一张表完成一切」（侧栏 / 预设1-4）。

本文件是从共享 formationConfig 搬进插件的表格版（工具大厅功能整体插件化，
上游 gui/components/expand/formationConfig.py 保持干净三模式版）：
  - 计划存插件键 tool_auto_push_team_plan；
  - choose_team_method 只写上游合法值（preset）：表格全未点亮的
    「用当前队伍」语义改经 team_config["keep_current"] 标记传递
    （见 module/explore_tasks/task_utils.py 的 convert_team_config /
    employ_units），不再把 "default" 写进上游键（上游面板会断言失败）。
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from qfluentwidgets import ComboBox

from gui.components.expand.tool_style import (
    is_dark,
    set_style_dedup,
    themed_accent,
    themed_input_bg,
    themed_input_border,
    themed_note_bg,
    themed_inner_select_qss,
    themed_table_css,
    themed_text,
)

# 属性键顺序即下拉框顺序（未使用放最后）
ATTR_KEYS = ("burst", "pierce", "mystic", "shock", "Unused")


class _ComboNoAni(ComboBox):
    """无动画下拉：qfw ComboBox 自带主题适配（浅色描边/深色适配/箭头内边距），
    仅去掉弹出动画（用户要求）。"""

    def _showComboMenu(self):
        if not self.items:
            return
        from qfluentwidgets.components.widgets.combo_box import ComboBoxMenu
        from qfluentwidgets.components.widgets.menu import MenuAnimationType
        from PyQt5.QtWidgets import QAction
        from PyQt5.QtCore import QPoint

        menu = ComboBoxMenu(self)
        for i, item in enumerate(self.items):
            menu.addAction(
                QAction(item.icon, item.text, triggered=lambda c, x=i: self._onItemClicked(x)))

        if menu.view.width() < self.width():
            menu.view.setMinimumWidth(self.width())
            menu.adjustSize()

        menu.setMaxVisibleItems(self.maxVisibleItems())
        menu.closedSignal.connect(self._onDropMenuClosed)
        self.dropMenu = menu

        if self.currentIndex() >= 0 and self.items:
            menu.setDefaultAction(menu.actions()[self.currentIndex()])

        x = -menu.width() // 2 + menu.layout().contentsMargins().left() + self.width() // 2
        pd = self.mapToGlobal(QPoint(x, self.height()))
        menu.view.adjustSize(pd, MenuAnimationType.NONE)
        menu.exec(pd, aniType=MenuAnimationType.NONE)


class _TeamCell(QFrame):
    """表格格子（Excel 式）：左边「使用」提示文字 + 右边窄属性下拉。

    点格子任意处 = 点亮/熄灭本格（选中态为主题色描边）。
    """
    toggled = pyqtSignal()
    attr_changed = pyqtSignal(str)

    def __init__(self, parent=None, names=None):
        super().__init__(parent)
        self.setObjectName('teamCell')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._use = False
        self._attr = "Unused"
        if names is None:
            names = list(ATTR_KEYS)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.setSpacing(4)

        self.chip = QLabel(self.tr('使用:'), self)
        self.chip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lay.addWidget(self.chip, 0, Qt.AlignVCenter)

        # qfw ComboBox 自带主题适配（浅色描边/深色配色/箭头内边距），不自造 QSS；仅去掉弹出动画
        self.combo = _ComboNoAni(self)
        cf = self.combo.font()
        cf.setPixelSize(13)  # 与「使用:」提示文字同一字号，避免一行两副字体
        self.combo.setFont(cf)
        self.combo.addItems(list(names))
        self.combo.setCurrentIndex(len(names) - 1)
        self._combo_names = list(names)
        self.combo.currentIndexChanged.connect(self._on_combo)
        lay.addWidget(self.combo, 0, Qt.AlignVCenter)

        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(self.tr('点击点亮/熄灭本格；下拉选属性'))
        self.setFixedHeight(40)

    def _on_combo(self, idx):
        if 0 <= idx < len(ATTR_KEYS):
            self._attr = ATTR_KEYS[idx]
            self.attr_changed.emit(self._attr)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 点在下拉上时不切换点亮（让下拉自己处理）；点其余区域切换
            child = self.childAt(event.pos())
            over_combo = False
            w = child
            while w is not None and w is not self:
                if w is self.combo:
                    over_combo = True
                    break
                w = w.parentWidget()
            if not over_combo:
                self.set_use(not self._use, emit=True)
        super().mousePressEvent(event)

    def set_use(self, use, emit=False):
        if self._use == use:
            return
        self._use = use
        self.apply_theme()
        if emit:
            self.toggled.emit()

    def is_lit(self):
        return self._use

    def attr_key(self):
        return self._attr

    def set_state(self, use, attr):
        """程序化设置（载入时），不发信号。"""
        idx = ATTR_KEYS.index(attr) if attr in ATTR_KEYS else len(ATTR_KEYS) - 1
        if self.combo.currentIndex() != idx:
            self.combo.blockSignals(True)
            self.combo.setCurrentIndex(idx)
            self.combo.blockSignals(False)
        self._attr = ATTR_KEYS[idx]
        if self._use != use:
            self._use = use
            self.apply_theme()

    def apply_theme(self):
        set_style_dedup(self, themed_inner_select_qss('teamCell', self._use))
        set_style_dedup(self.chip, f"color: {themed_text()}; background: transparent;")
        # 下拉框样式全权交给 qfw（FluentStyleSheet.COMBO_BOX 自带浅色描边/深色配色/
        # 箭头内边距），不再自造 QSS 覆盖。
        f = self.chip.font()
        f.setPixelSize(13)
        self.chip.setFont(f)



class _ColumnHeader(QFrame):
    """列头：与下方格子同尺寸的可点框。小 checkbox 仅作装饰（勾选态示意），
    文字本身即点击热区；选中态用主题色描边（与格子点亮一致）。"""

    toggled = pyqtSignal(bool)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName('colHeader')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._on = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 8, 0)
        lay.setSpacing(4)
        self.mark = QLabel('☐', self)  # 装饰勾选示意，紧贴列名文字，整组居中
        self.mark.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lay.addStretch(1)
        lay.addWidget(self.mark, 0, Qt.AlignVCenter)
        lay.addWidget(self.label, 0, Qt.AlignVCenter)
        lay.addStretch(1)
        f = self.label.font()
        f.setPixelSize(13)
        self.label.setFont(f)
        fm = self.mark.font()
        fm.setPixelSize(13)
        self.mark.setFont(fm)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('点击点亮/熄灭整列')
        self.setFixedHeight(40)  # 与下方格子同高

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_on(not self._on, emit=True)
        super().mousePressEvent(event)

    def set_on(self, on, emit=False):
        if self._on == on:
            return
        self._on = bool(on)
        self.apply_theme()
        if emit:
            self.toggled.emit(self._on)

    def is_on(self):
        return self._on

    def apply_theme(self):
        set_style_dedup(self.mark, 'color: %s; background: transparent;' % themed_text())
        self.mark.setText('☑' if self._on else '☐')
        set_style_dedup(self.label, 'color: %s; background: transparent;' % themed_text())
        set_style_dedup(self, themed_inner_select_qss('colHeader', self._on))


class Layout(QWidget):
    """编队选择：一张表完成一切（侧栏 / 预设1-4）。

    Excel 式表格：列头 checkbox 勾选=点亮整列；格子内点「使用:」或格子
    空白处点亮/熄灭单格（选中态=主题色描边）；下拉选属性（可选）。
    全部不点亮 = 默认使用当前已设置的队伍战斗。
    """

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.ATTR_NAMES = {
            "burst": self.tr('爆发'), "pierce": self.tr('贯穿'),
            "mystic": self.tr('神秘'), "shock": self.tr('振动'),
            "Unused": self.tr('未定'),
        }
        self.SOURCES = (
            ("side", self.tr('侧栏'), 4),
            ("preset1", self.tr('预设1'), 5),
            ("preset2", self.tr('预设2'), 5),
            ("preset3", self.tr('预设3'), 5),
            ("preset4", self.tr('预设4'), 5),
        )
        self._cells = {}
        self._col_checks = {}
        self._suspend = False
        self.plan = self._load_plan()

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(8)
        self._build_ui()
        self._sync_from_plan()
        self._refresh_theme()
        # 主题统一由容器遍历刷新（_refresh_theme）；自身不连 themeChanged，避免多重遍历卡顿

    # ---------- 数据 ----------

    def _load_plan(self):
        try:
            plan = self.config.get("tool_auto_push_team_plan")
        except Exception:
            plan = None
        if not (isinstance(plan, dict) and plan):
            plan = self._migrate_legacy_plan()
        norm = {}
        for key, _name, cap in self.SOURCES:
            slots = plan.get(key) if isinstance(plan, dict) else None
            col = []
            for j in range(cap):
                item = slots[j] if isinstance(slots, list) and j < len(slots) and isinstance(slots[j], dict) else {}
                attr = item.get("attr")
                if attr not in ATTR_KEYS:
                    attr = "Unused"
                col.append({"use": bool(item.get("use", False)), "attr": attr})
            norm[key] = col
        return norm

    def _migrate_legacy_plan(self):
        """旧三选项配置 -> 新表初始显示值（只进内存，不写回、不动旧键）。"""
        plan = {key: [{"use": False, "attr": "Unused"} for _ in range(cap)]
                for key, _n, cap in self.SOURCES}
        try:
            method = self.config.get("choose_team_method")
        except Exception:
            method = "preset"
        try:
            if method == "side":
                side = self.config.get("side_team_attribute")
                row = side[0] if isinstance(side, list) and side and isinstance(side[0], list) else []
                for j, attr in enumerate(list(row)[:4]):
                    if attr in ATTR_KEYS:
                        plan["side"][j] = {"use": attr != "Unused", "attr": attr}
            else:
                data = self.config.get("preset_team_attribute")
                if isinstance(data, list):
                    for k in range(1, 5):
                        row = data[k - 1] if k - 1 < len(data) and isinstance(data[k - 1], list) else []
                        for m, attr in enumerate(list(row)[:5]):
                            if attr in ATTR_KEYS:
                                plan[f"preset{k}"][m] = {"use": attr != "Unused", "attr": attr}
        except Exception:
            pass
        return plan

    def _collect_plan(self):
        return {key: [{"use": self._cells[(key, r)].is_lit(),
                       "attr": self._cells[(key, r)].attr_key()} for r in range(cap)]
                for key, _name, cap in self.SOURCES}

    def _persist(self):
        import json as _json
        plan = self._collect_plan()
        method = self._derive_method(plan)
        try:
            self.config.set("tool_auto_push_team_plan", _json.loads(_json.dumps(plan)))
            # 只写上游合法值；全空(default)的「用当前队伍」语义经
            # team_config["keep_current"] 传递，不把 "default" 写进上游键
            self.config.set("choose_team_method", "preset" if method == "default" else method)
        except Exception:
            pass

    def _derive_method(self, plan=None):
        plan = plan if plan is not None else self._collect_plan()
        for col in plan.values():
            for item in col:
                if item["use"]:
                    return "preset"
        return "default"

    # ---------- 界面 ----------

    def _build_ui(self):
        # 表格整体小框：主题引擎统一描边
        table = QFrame(self)
        table.setObjectName('teamTable')
        table.setAttribute(Qt.WA_StyledBackground, True)
        grid = QGridLayout(table)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        grid.setContentsMargins(8, 8, 8, 8)

        for c, (key, name, _cap) in enumerate(self.SOURCES):
            head = _ColumnHeader(name, table)
            head.toggled.connect(lambda on, k=key: self._toggle_column(k, on))
            self._col_checks[key] = head
            grid.addWidget(head, 0, c + 1, Qt.AlignVCenter)

        max_cap = max(cap for _k, _n, cap in self.SOURCES)
        for r in range(max_cap):
            row_label = QLabel(str(r + 1), table)
            row_label.setAlignment(Qt.AlignCenter)  # 竖列文字居中
            row_label.setObjectName('rowNumLabel')
            grid.addWidget(row_label, r + 1, 0)
            for c, (key, _name, cap) in enumerate(self.SOURCES):
                if r >= cap:
                    dead = QLabel('—', table)
                    dead.setAlignment(Qt.AlignCenter)
                    dead.setObjectName('deadCellLabel')
                    grid.addWidget(dead, r + 1, c + 1, Qt.AlignVCenter)
                    continue
                cell = _TeamCell(table, names=[self.ATTR_NAMES[k] for k in ATTR_KEYS])
                cell.toggled.connect(lambda k=key: self._on_cell_toggle(k))
                cell.attr_changed.connect(lambda _a=None, k=key: self._on_any_change())
                self._cells[(key, r)] = cell
                grid.addWidget(cell, r + 1, c + 1, Qt.AlignVCenter)

        grid.setColumnStretch(0, 0)
        for c in range(1, 6):
            grid.setColumnStretch(c, 1)
        self.vBoxLayout.addWidget(table)

        self.summary_label = QLabel(self)
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName('planSummary')
        self.summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.vBoxLayout.addWidget(self.summary_label)
        self.setLayout(self.vBoxLayout)

    def _sync_from_plan(self):
        self._suspend = True
        try:
            for (key, r), cell in self._cells.items():
                item = self.plan[key][r]
                cell.set_state(item["use"], item["attr"])
            for key, _name, cap in self.SOURCES:
                self._sync_column_check(key)
        finally:
            self._suspend = False
        self._update_summary()

    def _sync_column_check(self, key):
        cap = next(c for k, _n, c in self.SOURCES if k == key)
        all_lit = all(self._cells[(key, r)].is_lit() for r in range(cap))
        head = self._col_checks[key]
        if head.is_on() != all_lit:
            head.set_on(all_lit)
            head.apply_theme()

    def _toggle_column(self, key, on):
        """列头点击：点亮=整列点亮，取消=整列熄灭。"""
        if self._suspend:
            return
        cap = next(c for k, _n, c in self.SOURCES if k == key)
        for r in range(cap):
            self._cells[(key, r)].set_use(bool(on))
        self._sync_column_check(key)
        self._update_summary()
        self._persist()

    def _on_cell_toggle(self, key):
        self._sync_column_check(key)
        self._update_summary()
        self._persist()

    def _on_any_change(self):
        if self._suspend:
            return
        self._update_summary()
        self._persist()

    def _first_lit_label(self):
        for key, name, cap in self.SOURCES:
            for r in range(cap):
                cell = self._cells.get((key, r))
                if cell is not None and cell.is_lit():
                    unit = "格" if key == "side" else "队"
                    return f"{name} 第{r + 1}{unit}"
        return None

    def _update_summary(self):
        lit_cols, attr_cols = [], []
        first_lit = None
        for key, name, cap in self.SOURCES:
            has_lit = any(self._cells[(key, r)].is_lit() for r in range(cap))
            has_attr = any(self._cells[(key, r)].is_lit() and self._cells[(key, r)].attr_key() != "Unused"
                           for r in range(cap))
            if has_lit:
                (attr_cols if has_attr else lit_cols).append(name)
            if has_lit and first_lit is None:
                first_lit = self._first_lit_label()
        if not attr_cols and not lit_cols:
            self.summary_label.setText(
                self.tr('什么都不点：默认使用当前已设置的队伍战斗。'))
            return
        if attr_cols:
            cols = '、'.join(attr_cols)
            self.summary_label.setText(self.tr(
                '战斗前将点击 %s 与设置属性符合编队。如无克制属性，将默认使用已设置属性队伍。' % cols))
            return
        # 有点亮但全都未设置属性：默认用第一个点亮的队伍
        self.summary_label.setText(self.tr(
            '已选队伍未设置属性，默认使用 %s。' % (first_lit or '')))

    def _refresh_theme(self):
        """主题引擎统一刷新入口（容器遍历调用）。"""
        # 表格整体 = 主题引擎小框；每格 = 引擎两态格；行号/占位文字 = 主题文字色
        for _k, cell in self._cells.items():
            cell.apply_theme()
        for head in self._col_checks.values():
            head.apply_theme()
        table = self._cells[('side', 0)].parentWidget() if self._cells else None
        if table is not None:
            set_style_dedup(table, themed_table_css('teamTable'))
            for w in table.findChildren(QLabel):
                if w.objectName() in ('rowNumLabel', 'deadCellLabel'):
                    set_style_dedup(w, f"color: {themed_text()}; background: transparent;")
        set_style_dedup(
            self.summary_label,
            f"#planSummary {{ background: {themed_note_bg()}; color: {themed_text()}; "
            f"border-radius: 6px; padding: 8px 10px; }}")
