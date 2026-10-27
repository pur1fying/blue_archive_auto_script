# -*- coding: utf-8 -*-
"""沙勒总决算库存管理页面。

UI 修改入口在 UI_CONFIG。棋盘使用自绘控件，保证 9x5 格零间隙排列，并把
棋盘交互集中在 BoardCanvas：左键旋转、右键删除、拖动移动。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QAbstractSpinBox, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

try:
    from qfluentwidgets import CheckBox, PrimaryPushButton, PushButton, SpinBox
    from qfluentwidgets.components.widgets.spin_box import SpinButton as _QfwSpinButton
    _qfw_spin_orig_paint = _QfwSpinButton.paintEvent

    def _qfw_spin_centered_paint(self, event):
        # qfw 固定把箭头画在 (10,9) 起；按钮非默认尺寸时改为居中绘制。
        if (self.width(), self.height()) == (31, 23):
            _qfw_spin_orig_paint(self, event)
            return
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPainter
        from PyQt5.QtWidgets import QToolButton
        QToolButton.paintEvent(self, event)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        if self.isPressed:
            painter.setOpacity(0.7)
        size = min(11, self.width() - 6, self.height() - 4)
        # qfw 原版图标的视觉中心约在按钮 63% 高度处，按同比例下沉，避免偏上。
        self._icon.render(painter, QRectF((self.width() - size) / 2, (self.height() - size) / 2 + 2, size, size))

    _QfwSpinButton.paintEvent = _qfw_spin_centered_paint
except Exception:  # pragma: no cover
    CheckBox = QCheckBox
    PrimaryPushButton = PushButton = QPushButton
    SpinBox = QSpinBox

try:
    from gui.components.expand.tool_style import (apply_full_theme_refresh, connect_theme_refresh_full, themed_text,
                                                  is_dark, themed_input_bg, themed_input_text, themed_input_border,
                                                  themed_spinbox_css, themed_accent)
except Exception:  # pragma: no cover
    apply_full_theme_refresh = connect_theme_refresh_full = None
    themed_text = lambda: "#333333"
    is_dark = lambda: False
    themed_input_bg = lambda: "#FFFFFF"
    themed_input_text = lambda: "#111111"
    themed_input_border = lambda: "#999999"
    themed_spinbox_css = lambda: ""
    themed_accent = lambda: "#0078d4"


def _darken(hex_color, factor=0.45):
    """颜色按比例压暗：色块 2px 描边与填充同色系但足够区分，同色备品不再糊一起。"""
    try:
        c = QColor(hex_color)
        return QColor(
            max(0, int(c.red() * (1 - factor))),
            max(0, int(c.green() * (1 - factor))),
            max(0, int(c.blue() * (1 - factor))),
        ).name()
    except Exception:
        return hex_color


def _lighten(hex_color, factor=0.45):
    """颜色按比例提亮（向白混）：深色模式的描边专用——

    暗底上再压暗只会隐身（与热力图深端同坑），反其道提亮才有对比。
    """
    try:
        c = QColor(hex_color)
        return QColor(
            min(255, int(c.red() + (255 - c.red()) * factor)),
            min(255, int(c.green() + (255 - c.green()) * factor)),
            min(255, int(c.blue() + (255 - c.blue()) * factor)),
        ).name()
    except Exception:
        return hex_color

from .solver import BoardState, ItemDef, PlacedItem, solve

# ============================== 可调 UI 配置 ==============================
# 修改布局、颜色、文案优先从这里改，不需要动棋盘算法。
UI_CONFIG = {
    "cell_size": 52,
    "grid_line": 1,
    "panel_gap": 16,
    "page_padding": 8,
    "row_gap": 3,
    "spin_width": 76,
    "place_width": 62,
    "title": "沙勒总决算：库存管理",
    "hint": "默认点击棋盘输入空格；点击备品后的“放置”后再点击棋盘放置。左键旋转，右键删除，拖动移动。",
    "empty_color": "#d7dce0",
    "open_color": "#ffffff",
    "prob_low": "#E6F7FA",
    "prob_high": "#00A0E9",
    "item_colors": ["#e57373", "#22c55e", "#64b5f6"],
}

# solver 原始错误码 → 用户可读文案（正常操作流到不了这些码，兜底用）
_MSG_TRANS = {
    "input_error": "无有效配置：请检查高/宽/数量与已翻开的空格",
    "overlap": "备品存在重叠",
}
BOARD_W = 9
BOARD_H = 5


class _CalcWorker(QThread):
    result_ready = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state

    def run(self):
        try:
            self.result_ready.emit(solve(self.state))
        except Exception as exc:  # pragma: no cover
            self.failed.emit(str(exc))


class BoardCanvas(QWidget):
    """紧密棋盘与全部棋盘鼠标交互。"""

    changed = pyqtSignal()

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.cell_size = UI_CONFIG["cell_size"]
        self._prob_min = 0.0
        self._prob_max = 0.0
        self._best_cell = None  # 概率最高格 (r,c)：随重算/显示集变化即时更新
        self.setFixedSize(BOARD_W * self.cell_size + 2, BOARD_H * self.cell_size + 2)
        self.setSizePolicy(QWidget().sizePolicy().Fixed, QWidget().sizePolicy().Fixed)
        self._drag_index = None
        self._drag_origin = None
        self._drag_offset = (0, 0)
        self._drag_pos = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

    def _cell(self, pos):
        return pos.y() // self.cell_size, pos.x() // self.cell_size

    def _placed_at(self, row, col):
        defs = self.owner._read_item_defs()
        for i in range(len(self.owner._placed) - 1, -1, -1):
            p = self.owner._placed[i]
            it = defs[p.item_index]
            h, w = (it.width, it.height) if p.rotated else (it.height, it.width)
            if p.row <= row < p.row + h and p.col <= col < p.col + w:
                return i
        return None

    def mousePressEvent(self, event):
        row, col = self._cell(event.pos())
        if not (0 <= row < BOARD_H and 0 <= col < BOARD_W):
            return
        index = self._placed_at(row, col)
        if event.button() == Qt.RightButton:
            if index is not None:
                self.owner._placed.pop(index)
                self.owner._on_board_changed()
            else:
                self.owner._cells[row * BOARD_W + col] = 0
                self.owner._on_board_changed()
            return
        if event.button() != Qt.LeftButton:
            return
        if index is not None:
            p = self.owner._placed[index]
            self._drag_index = index
            self._drag_origin = (p.row, p.col, p.rotated)
            self._drag_offset = (row - p.row, col - p.col)
            self._drag_pos = (row, col)
            self._drag_moved = False
            return
        self.owner._on_empty_board_click(row, col)

    def mouseMoveEvent(self, event):
        if self._drag_index is None or not (event.buttons() & Qt.LeftButton):
            return
        row, col = self._cell(event.pos())
        p = self.owner._placed[self._drag_index]
        new_row = row - self._drag_offset[0]
        new_col = col - self._drag_offset[1]
        if (new_row, new_col) == (p.row, p.col):
            return
        self._drag_moved = True
        if self.owner._valid_placement(self._drag_index, new_row, new_col, p.rotated):
            p.row, p.col = new_row, new_col
            self._drag_pos = (row, col)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._drag_index is None:
            return
        index = self._drag_index
        self._drag_index = None
        if index >= len(self.owner._placed):
            return
        p = self.owner._placed[index]
        if not getattr(self, "_drag_moved", False):
            # 左键点击备品：只旋转，不删除。
            # 贴边/受阻时原锚点放不下旋转形态：在棋盘内找离原位置最近的
            # 合法锚点，整体挪过去旋转——只要棋盘有空位就转得动。
            new_rotated = not p.rotated
            if self.owner._valid_placement(index, p.row, p.col, new_rotated):
                p.rotated = new_rotated
            else:
                best = self.owner._nearest_valid_anchor(p, new_rotated)
                if best is not None:
                    p.row, p.col = best
                    p.rotated = new_rotated
                else:
                    self.owner._status.setText("旋转后棋盘已无空位可放")
        self.owner._on_board_changed()

    def set_cell_size(self, cell):
        self.cell_size = cell
        self.setFixedSize(BOARD_W * cell + 2, BOARD_H * cell + 2)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#888888"), UI_CONFIG["grid_line"]))
        defs = self.owner._read_item_defs()
        placed_map = {}
        seq = {}
        for p in self.owner._placed:
            seq[p.item_index] = seq.get(p.item_index, 0) + 1
            it = defs[p.item_index]
            h, w = (it.width, it.height) if p.rotated else (it.height, it.width)
            for rr in range(p.row, min(BOARD_H, p.row + h)):
                for cc in range(p.col, min(BOARD_W, p.col + w)):
                    placed_map[(rr, cc)] = (p.item_index, seq[p.item_index])
        for r in range(BOARD_H):
            for c in range(BOARD_W):
                rect_x, rect_y = c * self.cell_size, r * self.cell_size
                if (r, c) in placed_map:
                    i, order = placed_map[(r, c)]
                    color = UI_CONFIG["item_colors"][i]
                    text = f"{order}备品{i + 1}" if any(p.row == r and p.col == c for p in self.owner._placed if p.item_index == i) else ""
                elif self.owner._prob is not None and self.owner._cells[r * BOARD_W + c] == 0:
                    selected = self.owner._selected_items()
                    probs = [self.owner._prob[i][r][c] for i in selected]
                    # 各组是互斥的摆放结果，组合显示为选中组的覆盖概率之和。
                    value = min(1.0, sum(probs)) if probs else 0.0
                    # 区间 [vmin,vmax] → [0.2,1.0]：低端钳 20% 保底对比，最高值仍到最深。
                    lo, hi = self._prob_min, self._prob_max
                    norm = 0.2 + 0.8 * (value - lo) / (hi - lo) if hi > lo else 1.0
                    color = self.owner._prob_color(min(1.0, max(0.0, norm)))
                    text = f"{value * 100:.1f}%"
                elif self.owner._cells[r * BOARD_W + c]:
                    # 深色模式：开放格用输入框同款深底（themed_input_bg），
                    # 纯白底违反深色显示原则；"空"字由下方 themed_input_text()
                    # 自动获得可读对比（深色浅字/浅色深字）。
                    color, text = themed_input_bg(), "空"
                else:
                    # 未标记格：深色用更深灰阶，避免棋盘上出现大片亮块
                    color = "#26282c" if is_dark() else UI_CONFIG["empty_color"]
                    text = ""
                painter.fillRect(rect_x, rect_y, self.cell_size, self.cell_size, QColor(color))
                if (r, c) in placed_map:
                    # 填充即可，描边统一在循环后按"外沿 2px / 内部 1px"画。
                    i, order = placed_map[(r, c)]
                    if text:
                        # 序号章：浅色白底深描边、深色黑底浅描边，与插件大框标题栏一致。
                        dark = is_dark()
                        bg = QColor("#000000") if dark else QColor("#ffffff")
                        ring = QColor("#ffffff") if dark else QColor("#303030")
                        label = text.split("备品")[0] or "1"
                        # 禁止对 painter 字体做 setPointSize/setFont 换挡：控件字体
                        # 可能是像素字体（pointSize=-1），对它 +/-1 会被 Qt 拒绝
                        # （QFont::setPointSize 警告），而把这种未解析字体 setFont
                        # 回去会让 C++ 栅格引擎静默失效——序号章之后的所有格子
                        # 都画不出来（深浅色都复现，表现为棋盘大面积纯黑）。
                        # 序号章直接用当前字体绘制即可。
                        fm = painter.fontMetrics()
                        badge_w, badge_h = fm.horizontalAdvance(label) + 10, fm.height() + 3
                        bx = rect_x + (self.cell_size - badge_w) // 2
                        by = rect_y + (self.cell_size - badge_h) // 2
                        painter.setPen(QPen(ring, 1))
                        painter.setBrush(bg)
                        painter.drawRoundedRect(bx, by, badge_w, badge_h, 3, 3)
                        painter.setPen(QColor("#ffffff") if dark else QColor("#303030"))
                        painter.drawText(bx, by, badge_w, badge_h, Qt.AlignCenter, label)
                        painter.setBrush(Qt.NoBrush)
                else:
                    painter.setPen(QPen(QColor("#888888"), UI_CONFIG["grid_line"]))
                    painter.drawRect(rect_x, rect_y, self.cell_size, self.cell_size)
                    if text:
                        painter.setPen(QColor(themed_input_text()))
                        painter.drawText(rect_x, rect_y, self.cell_size, self.cell_size, Qt.AlignCenter, text)
        # 描边两遍走：外沿 2px 压暗描边勾出备品形状（用户指定）。
        try:
            for p in self.owner._placed:
                it = defs[p.item_index]
                h, w = (it.width, it.height) if p.rotated else (it.height, it.width)
                cells = {(rr, cc) for rr in range(p.row, min(BOARD_H, p.row + h))
                         for cc in range(p.col, min(BOARD_W, p.col + w))}
                # 一遍收集四边：内部共享边=1px 格子线，外露边=2px 压暗形状描边
                inner, outer = [], []
                for (rr, cc) in cells:
                    x, y = cc * self.cell_size, rr * self.cell_size
                    for a, b, c2, d2, shared in (
                        (x, y, x, y + self.cell_size, (rr, cc - 1) in cells),
                        (x + self.cell_size, y, x + self.cell_size, y + self.cell_size, (rr, cc + 1) in cells),
                        (x, y, x + self.cell_size, y, (rr - 1, cc) in cells),
                        (x, y + self.cell_size, x + self.cell_size, y + self.cell_size, (rr + 1, cc) in cells),
                    ):
                        (inner if shared else outer).append((a, b, c2, d2))
                painter.setPen(QPen(QColor("#888888"), 1))
                for seg in inner:
                    painter.drawLine(*seg)
                painter.setPen(QPen(QColor(_darken(UI_CONFIG["item_colors"][p.item_index])), 2))
                for seg in outer:
                    painter.drawLine(*seg)
        except Exception:
            pass
        # 建议格：热力最高的可点格描 2px 边（像备品一样有形状强调），
        # 数据在 _cache_prob_range 随重算/勾选集变化一并更新。
        # 概率数据在 owner(Layout) 上；paintEvent 中途抛异常会把激活的
        # QPainter 留给 QBackingStore → 段错误，判定也必须兜进 try。
        try:
            if self.owner._prob is not None and self._best_cell is not None:
                br, bc = self._best_cell
                accent = themed_accent()
                # 浅色底压暗、深色底提亮（反色）：暗底上压暗色会隐身
                ring = QColor(_darken(accent)) if not is_dark() else QColor(_lighten(accent))
                painter.setPen(QPen(ring, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(bc * self.cell_size + 1, br * self.cell_size + 1,
                                 self.cell_size - 2, self.cell_size - 2)
        except Exception:
            pass
        painter.end()


class _ItemShapePreview(QWidget):
    """备品形状示意图：正方形（边≈一个行距，随窗口缩放）。

    内容=当前形状横向优先：显示行数=min(高,宽)、列数=max(高,宽)——
    3x1 画一行三块、3x2 画两行三块、4x4 画 4 行 4 列；方块边长按较
    长边适配，多大都能完整装进方框。描边恒 1px（压暗同色），放大只
    增大小不加边宽。
    """

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self._index = index
        self._owner = None
        self._color = "#5b8def"
        self._side = 26
        self.setFixedSize(self._side, self._side)

    def set_owner(self, owner):
        self._owner = owner

    def set_item_color(self, color):
        self._color = color
        self.update()

    def set_scale(self, factor):
        try:
            self._side = max(18, min(40, int(round(26 * max(0.7, min(1.6, factor))))))
            self.setFixedSize(self._side, self._side)
            self.update()
        except Exception:
            pass

    def _dims(self):
        """先高后宽（BA 习惯）：返回 (行数, 列数)。"""
        try:
            h, w, _ = self._owner._items[self._index]
            return max(1, min(5, int(h.value()))), max(1, min(5, int(w.value())))
        except Exception:
            return 1, 1

    def _refresh_size(self):
        # 兼容旋钮 valueChanged 直连：格数变化只需重绘
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            h, w = self._dims()
            # 横向优先：显示行数=min(高,宽)、列数=max(高,宽)——
            # 3x1 显示 1 行 3 块，3x2 显示 2 行 3 块
            rows, cols = min(h, w), max(h, w)
            pad = 2.0
            gap = 2.0
            # 方块边长按较长边适配：4x4 也要完整装进正方形
            span = max(rows, cols)
            cell = (self._side - 2 * pad - (span - 1) * gap) / span
            cell = max(1.0, cell)
            gw = cols * cell + (cols - 1) * gap
            gh = rows * cell + (rows - 1) * gap
            x0 = (self._side - gw) / 2.0
            y0 = (self._side - gh) / 2.0
            # 描边恒 1px：放大只增大小，不加边宽
            painter.setPen(QPen(QColor(_darken(self._color)), 1))
            painter.setBrush(QColor(self._color))
            for r in range(rows):
                for c in range(cols):
                    painter.drawRect(x0 + c * (cell + gap), y0 + r * (cell + gap), cell, cell)
            painter.setBrush(Qt.NoBrush)
        finally:
            painter.end()


class Layout(QWidget):
    """库存计算器页面；三行备品控件和棋盘均保持紧凑布局。"""

    def __init__(self, parent=None, config=None, **kwargs):
        super().__init__(parent)
        self.config = config
        self._cells = [0] * (BOARD_W * BOARD_H)
        self._items = []
        self._placed: list[PlacedItem] = []
        self._active_item: Optional[int] = None
        self._prob = None
        self._worker: Optional[_CalcWorker] = None
        self._pending_recalc = False
        self._status_override = False
        self._status_item = None
        self._compute_checks = []
        self._histories = [[], [], []]
        self._history_buttons = [[], [], []]
        self._history_layouts = []
        self._item_frames = []
        self._shape_previews = []
        self._history_delete_mode = False
        self._history_values = [[], [], []]
        self._loading_state = True
        self._build_ui()
        self._load_state()
        if apply_full_theme_refresh is not None:
            apply_full_theme_refresh(self)
            # "只刷可见页"由容器统一处理（隐藏堆叠页整页跳过、切回时补刷）；
            # connect_theme_refresh_full 只收 widget 一个参数。
            connect_theme_refresh_full(self)
        self._configure_spinboxes()
        self._apply_uniform_font()
        self._refresh_place_buttons()
        self._loading_state = False
        self._refresh_board()
        self._schedule_recalc()

    def _build_ui(self):
        root = QVBoxLayout(self)
        pad = UI_CONFIG["page_padding"]
        root.setContentsMargins(pad, pad, pad, pad)
        root.setSpacing(4)
        title = QLabel(UI_CONFIG["title"], self)
        title.setObjectName("schaleInventoryTitle")
        root.addWidget(title)
        hint = QLabel(UI_CONFIG["hint"], self)
        hint.setWordWrap(True)
        root.addWidget(hint)
        main = QHBoxLayout(); main.setContentsMargins(0, 0, 0, 0); main.setSpacing(UI_CONFIG["panel_gap"])
        left_host = QWidget(self); self._left_host = left_host; left_host.setFixedWidth(BOARD_W * UI_CONFIG["cell_size"] + 2); left_host.setSizePolicy(left_host.sizePolicy().Fixed, left_host.sizePolicy().Fixed)
        left = QVBoxLayout(left_host); left.setContentsMargins(0, 0, 0, 0); left.setSpacing(0)
        self._board = BoardCanvas(self, left_host)
        # 棋盘整体下移 12px（约至右列「显示概率」中段往下）：
        # 顶部 spacer 12、与底行间距 16→4，列总高不变，清空棋盘与状态文字位置不动
        left.addSpacing(12)
        left.addWidget(self._board, 0, Qt.AlignLeft)
        left.addSpacing(4)
        actions = QHBoxLayout(); actions.setContentsMargins(0, 0, 0, 0); actions.setSpacing(4)
        self._clear = PushButton("清空棋盘", self)
        self._clear.clicked.connect(self._clear_board)
        actions.addStretch(1)
        actions.addWidget(self._clear)
        actions.addStretch(1)
        status_box = QFrame(self); status_box.setObjectName("schaleStatusBox"); status_box.setFixedWidth(128); status_box.setFixedHeight(50); status_row = QVBoxLayout(status_box); status_row.setContentsMargins(0, 0, 0, 0); self._status = QLabel("计算完成", status_box); self._status.setWordWrap(True); self._status.setAlignment(Qt.AlignLeft | Qt.AlignTop); self._status.setProperty("themeSemanticColor", True); status_row.addWidget(self._status)
        actions.addSpacing(12)
        actions.addWidget(status_box, 0, Qt.AlignVCenter)
        left.addLayout(actions); self._actions_row = actions; self._left_host = left_host; self._status_box = status_box; left_host.setFixedHeight(self._board.height() + 16 + 50)
        main.addWidget(left_host, 0, Qt.AlignLeft | Qt.AlignTop); main.addSpacing(UI_CONFIG["panel_gap"]); main.addWidget(self._build_side_panel(), 0); main.addStretch(1); root.addLayout(main)

    def _apply_uniform_font(self):
        font = self._clear.font() if hasattr(self, "_clear") else self.font()
        for widget in self.findChildren(QWidget):
            widget.setFont(font)

    def _refresh_theme(self):
        self._apply_uniform_font(); self._apply_status_color(); self._apply_status_baseline(); self._refresh_place_buttons(); self._configure_spinboxes(); self._restyle_item_boxes(); 
        for cb in getattr(self, "_compute_checks", []):
            cb.setStyleSheet(self._small_checkbox_css())
        self._refresh_history_buttons(); self._board.update()

    def _apply_status_baseline(self):
        # 清空棋盘已移到底部居中行：状态文字在固定 50px 框内垂直居中，
        # 框高与列高不变，窗口几何零波动。
        try:
            if not hasattr(self, "_status") or not hasattr(self, "_status_box"):
                return
            row = self._status.parentWidget().layout()
            if row is None:
                return
            fm = self._status.fontMetrics()
            top = max(0, (self._status_box.height() - fm.height()) // 2)
            row.setContentsMargins(0, top, 0, 0)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "_scaling", False):
            return
        self._scaling = True
        try:
            self._relayout_scale()
        finally:
            self._scaling = False

    def _relayout_scale(self):
        # 棋盘随窗口比例缩放（文字大小不变），限制在 0.7x–1.6x。
        if not hasattr(self, "_board") or not hasattr(self, "_left_host"):
            return
        base_w = BOARD_W * UI_CONFIG["cell_size"] + 2 + UI_CONFIG["panel_gap"] + 300
        base_h = BOARD_H * UI_CONFIG["cell_size"] + 2 + 16 + 44 + 80 + 2 * UI_CONFIG["page_padding"]
        factor = min(self.width() / base_w, self.height() / base_h)
        cell = int(UI_CONFIG["cell_size"] * max(0.7, min(1.6, factor)))
        if cell == self._board.cell_size:
            return
        self._board.set_cell_size(cell)
        self._left_host.setFixedWidth(BOARD_W * cell + 2)
        self._left_host.setFixedHeight(self._board.height() + 16 + 50)
        for sp in getattr(self, "_shape_previews", []):
            sp.set_scale(factor)
        QTimer.singleShot(0, self._apply_status_baseline)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._apply_status_baseline)

    def _configure_spinboxes(self):
        # 使用 Qt 原生 SpinBox：上下箭头天然纵向排列，数字编辑区不会被按钮覆盖。
        for values in self._items:
            for spin in values:
                spin.setFixedHeight(33)
                spin.setAlignment(Qt.AlignCenter)
                spin.lineEdit().setAlignment(Qt.AlignCenter)
                # 壳层 QSS 覆盖 qfw 默认样式：默认会在右侧预留 ~80px，窄控件下编辑区宽度为 0。
                spin.setStyleSheet(themed_spinbox_css())
                try:
                    spin.hBoxLayout.setDirection(QHBoxLayout.TopToBottom)
                    spin.hBoxLayout.setContentsMargins(0, 0, 0, 0)
                    spin.hBoxLayout.setSpacing(0)
                    spin.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    spin.upButton.setFixedSize(24, 16)
                    spin.downButton.setFixedSize(24, 16)
                except Exception:
                    pass


    def _on_compute_changed(self):
        # 勾选状态变化 → 框体 1px 灰/主题色同步刷新 + 重算概率
        self._restyle_item_boxes()
        self._cache_prob_range(); self._on_board_changed()

    def _style_item_box(self, index):
        """备品小框：主题引擎「程序内在选的 1px 蓝框」统一发放（与编队表格同款）。"""
        try:
            from gui.components.expand.tool_style import themed_inner_select_qss

            box = self._item_frames[index]
            on = self._compute_checks[index].isChecked()
            box.setStyleSheet(themed_inner_select_qss("schaleItemBox%d" % (index + 1), on))
        except Exception:
            pass

    def _restyle_item_boxes(self):
        for i in range(len(self._item_frames)):
            self._style_item_box(i)

    def eventFilter(self, obj, event):
        # 整个备品小框都可点选切换"是否计算"；点在旋钮/按钮/勾选框上除外。
        try:
            from PyQt5.QtCore import QEvent

            if event.type() == QEvent.MouseButtonRelease and obj in self._item_frames:
                child = obj.childAt(event.pos())
                meaningful = child is not None and child is not obj and (
                    isinstance(child, (QAbstractSpinBox, QPushButton))
                    or isinstance(child, QCheckBox)
                    or child.objectName().startswith("schalePlace")
                )
                if not meaningful:
                    i = self._item_frames.index(obj)
                    cb = self._compute_checks[i]
                    cb.setChecked(not cb.isChecked())
                    return True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _selected_items(self):
        return [i for i, cb in enumerate(self._compute_checks) if cb.isChecked()]

    def _build_side_panel(self):
        panel = QWidget(self)
        # 整列右移一点：不贴着棋盘，给左缘留 14px 空气
        layout = QVBoxLayout(panel); layout.setContentsMargins(14, 0, 0, 0); layout.setSpacing(UI_CONFIG["row_gap"])
        # 表头与备品行同构（同 spacing=4、同槽宽）："显示概率" 对齐小框，
        # 空 62px 让出放置钮位，高/宽/总数 52px 对齐旋钮
        header = QHBoxLayout(); header.setContentsMargins(4, 0, 0, 0); header.setSpacing(4)
        prob = QLabel("显示概率", panel); prob.setFixedWidth(UI_CONFIG["place_width"]); prob.setAlignment(Qt.AlignCenter)
        header.addWidget(prob)
        place_holder = QWidget(panel); place_holder.setFixedWidth(UI_CONFIG["place_width"])
        header.addWidget(place_holder)
        for label in ("高", "宽", "总数"):
            lab = QLabel(label, panel); lab.setFixedWidth(52); lab.setAlignment(Qt.AlignCenter); header.addWidget(lab)
        header.addStretch(1)
        layout.addLayout(header)
        for i in range(3): layout.addWidget(self._build_item_row(i))
        # 删除历史记录紧跟右栏内容（间距=行距，不沉到整列最底）
        bottom = QHBoxLayout(); bottom.setContentsMargins(0, 0, 0, 0)
        delete = PushButton("删除历史记录", panel); delete.setCheckable(True); delete.clicked.connect(self._toggle_history_delete)
        bottom.addWidget(delete); bottom.addStretch(1); layout.addLayout(bottom)
        layout.addStretch(1)
        return panel

    def _build_item_row(self, index):
        # 计算开关小框：只围 checkbox + 备品N 文字（与放置钮差不多大），
        # 勾选框紧贴备品文字；1px 灰框，参与计算=主题色框，整框可点选。
        row_widget = QFrame(self)
        outer = QVBoxLayout(row_widget); outer.setContentsMargins(4, 3, 4, 3); outer.setSpacing(2)
        line = QHBoxLayout(); line.setContentsMargins(0, 0, 0, 0); line.setSpacing(4)
        box = QFrame(row_widget); box.setObjectName(f"schaleItemBox{index + 1}")
        box.setFixedSize(UI_CONFIG["place_width"], 32)
        bl = QHBoxLayout(box); bl.setContentsMargins(3, 1, 3, 1); bl.setSpacing(1)
        cb = CheckBox(box); cb.setChecked(True)
        cb.setStyleSheet(self._small_checkbox_css())
        cb.stateChanged.connect(self._on_compute_changed)
        cb.setToolTip("勾选=参与概率计算；点击小框同样切换")
        self._compute_checks.append(cb)
        # 勾选框 = 原垂直居中位置再往下 2px：19px 宿主（上留 2px）随行居中
        cb_host = QWidget(box); ch = QVBoxLayout(cb_host)
        ch.setContentsMargins(0, 2, 0, 0); ch.setSpacing(0); ch.addWidget(cb)
        bl.addWidget(cb_host, 0, Qt.AlignVCenter)
        name = QLabel(f"备品{index + 1}", box); name.setObjectName(f"schaleInventoryItem{index + 1}"); name.setFixedWidth(42)
        name.setStyleSheet(f"color: {UI_CONFIG['item_colors'][index]};")
        bl.addWidget(name, 0, Qt.AlignVCenter)
        line.addWidget(box, 0, Qt.AlignVCenter)
        place = PrimaryPushButton("放置", row_widget); place.setCheckable(False); place.setObjectName(f"schalePlace{index + 1}"); place.setFixedWidth(UI_CONFIG["place_width"]); place.clicked.connect(lambda checked=False, i=index: self._select_item(i))
        cancel = PushButton("取消", row_widget); cancel.setCheckable(False); cancel.setObjectName(f"schalePlace{index + 1}"); cancel.setFixedWidth(UI_CONFIG["place_width"]); cancel.clicked.connect(lambda checked=False, i=index: self._select_item(i)); cancel.setVisible(False)
        line.addWidget(place)
        line.addWidget(cancel)
        self._cancel_buttons = getattr(self, "_cancel_buttons", []); self._cancel_buttons.append(cancel)
        controls = []
        for maximum in (4, 4, 7):
            spin = SpinBox(row_widget); spin.setRange(1, maximum); spin.setValue(1); spin.setFixedWidth(52); spin.setFixedHeight(33); spin.setAlignment(Qt.AlignCenter); spin.valueChanged.connect(self._on_item_changed); line.addWidget(spin); controls.append(spin)
        outer.addLayout(line)
        # 第二行：正方形格数示意图（横排），历史记录（最多两行）紧随其后
        row2 = QHBoxLayout(); row2.setContentsMargins(0, 0, 0, 0); row2.setSpacing(6)
        shape = _ItemShapePreview(index, row_widget)
        shape.set_owner(self)
        shape.set_item_color(UI_CONFIG["item_colors"][index])
        for spin in controls:
            spin.valueChanged.connect(shape.update)
        self._shape_previews.append(shape)
        row2.addWidget(shape, 0, Qt.AlignVCenter)
        history = QGridLayout(); history.setContentsMargins(0, 0, 0, 0); history.setHorizontalSpacing(3); history.setVerticalSpacing(2)
        hist_host = QWidget(row_widget); hist_host.setLayout(history)
        row2.addWidget(hist_host, 1)
        outer.addLayout(row2)
        self._history_layouts.append(history); self._items.append(tuple(controls)); self._place_buttons = getattr(self, "_place_buttons", []); self._place_buttons.append(place)
        box.installEventFilter(self)
        self._item_frames.append(box)
        self._style_item_box(index)
        return row_widget

    def _read_item_defs(self):
        return [ItemDef(h.value(), w.value(), total.value()) for h, w, total in self._items]

    def _state_path(self):
        return Path(__file__).resolve().parents[3] / "config" / "schale_inventory.json"

    def _load_state(self):
        try:
            data = json.loads(self._state_path().read_text(encoding="utf-8"))
            cells = data.get("cells")
            if isinstance(cells, list) and len(cells) == 45: self._cells = [int(x) for x in cells]
            for i, values in enumerate(data.get("items", [])):
                if i < 3 and isinstance(values, list) and len(values) == 3:
                    h, w, total = self._items[i]; h.setValue(int(values[0])); w.setValue(int(values[1])); total.setValue(max(1, int(values[2])))
            self._placed = [PlacedItem(int(x[0]), bool(x[1]), int(x[2]), int(x[3])) for x in data.get("placed", []) if isinstance(x, list) and len(x) == 4]
            history = data.get("history") or [[], [], []]
            for i in range(min(3, len(history))):
                for scheme in history[i] or []:
                    if isinstance(scheme, (list, tuple)) and len(scheme) == 2:
                        self._add_history(i, (int(scheme[0]), int(scheme[1])))
        except Exception:
            pass

    def _save_state(self):
        try:
            path = self._state_path(); path.parent.mkdir(parents=True, exist_ok=True)
            values = [[h.value(), w.value(), total.value()] for h, w, total in self._items]
            placed = [[p.item_index, p.rotated, p.row, p.col] for p in self._placed]
            history = [[list(s) for s in values] for values in self._histories]
            path.write_text(json.dumps({"cells": self._cells, "items": values, "placed": placed, "history": history}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


    def _small_checkbox_css(self):
        """小号勾选框：引擎统一发放（绿框边体系，按主题缓存）。"""
        try:
            from gui.components.expand.tool_style import themed_small_checkbox_css

            return themed_small_checkbox_css()
        except Exception as e:
            print("[schale] small checkbox css failed:", e)
            return ""

    def _refresh_place_buttons(self):
        # 按钮外观全由主题引擎/qfw 原生发放：未选中=PrimaryPushButton
        # 「放置」（主题色底白字），选中=PushButton「取消」（浅底深字），
        # 两态即主题引擎内两种功能按钮色，插件不碰 setStyleSheet。
        cancels = getattr(self, "_cancel_buttons", [])
        for i, place in enumerate(self._place_buttons):
            active = self._active_item == i
            place.setVisible(not active)
            if i < len(cancels):
                cancels[i].setVisible(active)
        # 刚被点击的按钮随 setVisible(False) 隐藏时，Qt 会把焦点沿 Tab 链
        # 丢给第一个旋钮（表现为"点放置激活了输入栏"）。显式收回棋盘。
        try:
            self._board.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass

    def _select_item(self, index):
        defs = self._read_item_defs()
        if sum(p.item_index == index for p in self._placed) >= defs[index].count:
            # 上限在点击“放置”时就提示，不必等到点击棋盘。
            self._set_status_color(index, f"备品{index + 1}已到达上限", True)
            return
        if self._active_item == index:
            self._active_item = None
            self._status_override = False
            self._refresh_place_buttons()
            self._set_status_color(None, "计算完成")
            return
        self._status_override = True
        self._active_item = index
        self._refresh_place_buttons()
        self._set_status_color(index, f"已选择备品{index + 1}，点击棋盘放置", True)

    def _set_status_color(self, item_index, text, override=False):
        self._status_override = override
        self._status_item = item_index
        self._status.setText(text)
        # 不再设置 toolTip：说明框文字已完整显示，悬停弹出的 title 属于冗余
        self._status.setProperty("themeSemanticColor", True)
        self._apply_status_color()

    def _apply_status_color(self):
        if not hasattr(self, "_status"): return
        pal = self._status.palette()
        color = themed_text() if self._status_item is None else UI_CONFIG["item_colors"][self._status_item]
        pal.setColor(pal.WindowText, QColor(color))
        self._status.setPalette(pal)
        self._status.setStyleSheet(f"color: {color}; font-size: {self._status.font().pointSize()}pt;")

    def _refresh_board(self):
        """刷新自绘棋盘；保留该兼容方法供旧挂载流程调用。"""
        if hasattr(self, "_board"):
            self._board.update()

    def _toggle_history_delete(self, enabled):
        self._history_delete_mode = bool(enabled)
        sender = self.sender()
        if sender is not None:
            sender.setText("保存历史记录" if enabled else "删除历史记录")
        self._refresh_history_buttons()

    def _refresh_history_buttons(self):
        for i, buttons in enumerate(self._history_buttons):
            for button in buttons:
                button.setText(button.property("scheme_text"))
                marker = button.property("delete_marker")
                if marker is not None: marker.setVisible(self._history_delete_mode)
                button.setFixedSize(50, 26)

    def _add_history(self, index, scheme):
        h, w = scheme
        # 交换等价的方案（如 2x3 与 3x2）只记录一次。
        if scheme in self._histories[index] or (w, h) in self._histories[index]: return
        self._histories[index].append(scheme)
        self._histories[index].sort(key=lambda s: (max(s), min(s)))
        # 标签统一大数字在前（2x4 → 4x2），按尺寸从小到大扫过去即可查找。
        label = f"{max(scheme)}x{min(scheme)}"
        button = PushButton(label, self)
        button.setProperty("scheme_text", label)
        button.setProperty("scheme", (h, w))
        marker = QLabel("×", button); marker.setObjectName("schaleHistoryDeleteMarker"); marker.setAlignment(Qt.AlignCenter); marker.setGeometry(34, 0, 14, 26); marker.setVisible(self._history_delete_mode); marker.setStyleSheet(f"color: {themed_input_text()}; background: transparent;"); button.setProperty("delete_marker", marker)
        button.setFixedSize(50, 26)
        button.clicked.connect(lambda checked=False, ii=index, ss=scheme, bb=button: self._history_clicked(ii, ss, bb))
        self._history_buttons[index].append(button)
        layout = self._history_layouts[index]
        layout.setContentsMargins(4, 0, 0, 0)
        # 最多两行：先横向填满一行（8 个）再换行，位置即排序后的名次。
        layout.setColumnStretch(8, 1)
        layout.addWidget(button, 0, 0, Qt.AlignLeft)
        self._relayout_history(index)
        self._refresh_history_buttons()

    def _relayout_history(self, index):
        """按尺寸从小到大、从左到右重排；一行 8 个，填满再换行。"""
        layout = self._history_layouts[index]
        self._history_buttons[index].sort(
            key=lambda b: (max(b.property("scheme")), min(b.property("scheme")))
        )
        for pos, button in enumerate(self._history_buttons[index]):
            layout.removeWidget(button)
            layout.addWidget(button, pos // 8, pos % 8, Qt.AlignLeft)

    def _on_item_changed(self):
        if self._loading_state:
            return
        self._sanitize_placed()
        self._on_board_changed()

    def _history_clicked(self, index, scheme, button):
        if self._history_delete_mode:
            if scheme in self._histories[index]: self._histories[index].remove(scheme)
            self._history_buttons[index].remove(button)
            button.deleteLater()
            self._relayout_history(index)
            self._save_state()
            return
        self._use_history(index, scheme)

    def _use_history(self, index, scheme):
        h, w, _ = self._items[index]
        h.blockSignals(True); w.blockSignals(True)
        h.setValue(scheme[0]); w.setValue(scheme[1])
        h.blockSignals(False); w.blockSignals(False)
        self._on_item_changed()

    def _on_empty_board_click(self, row, col):
        if self._active_item is None:
            self._status_override = False
            self._set_status_color(None, "计算中…")
            self._cells[row * BOARD_W + col] = 1
            self._on_board_changed()
            return
        item_index = self._active_item
        success = self._place_item(item_index, row, col)
        self._active_item = None
        self._refresh_place_buttons()
        if success: self._on_board_changed()

    def _valid_placement(self, index, row, col, rotated):
        if row < 0 or col < 0: return False
        defs = self._read_item_defs(); p = self._placed[index]; item = defs[p.item_index]
        h, w = (item.width, item.height) if rotated else (item.height, item.width)
        if row + h > BOARD_H or col + w > BOARD_W: return False
        target = {(r, c) for r in range(row, row + h) for c in range(col, col + w)}
        if any(self._cells[r * BOARD_W + c] for r, c in target): return False
        for j, other in enumerate(self._placed):
            if j == index: continue
            old = defs[other.item_index]; oh, ow = (old.width, old.height) if other.rotated else (old.height, old.width)
            occupied = {(r, c) for r in range(other.row, other.row + oh) for c in range(other.col, other.col + ow)}
            if target & occupied: return False
        return True

    def _nearest_valid_anchor(self, placed, rotated):
        """旋转形态在棋盘内离原锚点最近的可放位置；无空位返回 None。

        全盘扫描（9x5 共 45 格，代价可忽略），跳过越界候选由
        _valid_placement 统一裁决（边界/禁用格/其他备品）。
        """
        defs = self._read_item_defs()
        item = defs[placed.item_index]
        h, w = (item.width, item.height) if rotated else (item.height, item.width)
        best = None
        best_d = None
        self._rotating_placed = placed
        try:
            for r in range(BOARD_H - h + 1):
                for c in range(BOARD_W - w + 1):
                    d = abs(r - placed.row) + abs(c - placed.col)
                    if best_d is not None and d >= best_d:
                        continue
                    if self._valid_placement_by_item(item, r, c, rotated):
                        best_d = d
                        best = (r, c)
        finally:
            self._rotating_placed = None
        return best

    def _valid_placement_by_item(self, item, row, col, rotated):
        """与 _valid_placement 相同，但按 item 而非 placed 下标判定。"""
        if row < 0 or col < 0:
            return False
        h, w = (item.width, item.height) if rotated else (item.height, item.width)
        if row + h > BOARD_H or col + w > BOARD_W:
            return False
        target = {(r, c) for r in range(row, row + h) for c in range(col, col + w)}
        if any(self._cells[r * BOARD_W + c] for r, c in target):
            return False
        defs = self._read_item_defs()
        for other in self._placed:
            if getattr(self, "_rotating_placed", None) is not None and other is self._rotating_placed:
                continue  # 旋转中的备品自身旧占位不算障碍
            old = defs[other.item_index]
            oh, ow = (old.width, old.height) if other.rotated else (old.height, old.width)
            occupied = {(r, c) for r in range(other.row, other.row + oh) for c in range(other.col, other.col + ow)}
            if target & occupied:
                return False
        return True

    def _place_item(self, item_index, row, col):
        defs = self._read_item_defs(); item = defs[item_index]
        if sum(p.item_index == item_index for p in self._placed) >= item.count:
            self._set_status_color(item_index, f"备品{item_index + 1}已到达上限", True)
            return False
        # 点击格必须被覆盖：以点击点为左上角优先（距离 0），放不下时在
        # 覆盖点击格的锚点集合里找合法位置——物品可往左/往上伸展（点击格
        # 落在物品任意格上），凹形空位、边缘、角落都能放；离点击点最近优先。
        for rotated in (False, True):
            if rotated and item.height == item.width:
                continue
            h, w = (item.width, item.height) if rotated else (item.height, item.width)
            cands = []
            r_lo, r_hi = max(0, row - h + 1), min(row, BOARD_H - h)
            c_lo, c_hi = max(0, col - w + 1), min(col, BOARD_W - w)
            for r in range(r_lo, r_hi + 1):
                for c in range(c_lo, c_hi + 1):
                    cands.append((abs(r - row) + abs(c - col), r, c))
            cands.sort()
            for _, r0, c0 in cands:
                p = PlacedItem(item_index, rotated, r0, c0)
                self._placed.append(p)
                if self._valid_placement(len(self._placed) - 1, r0, c0, rotated):
                    hs, ws, _ = self._items[item_index]
                    self._add_history(item_index, (hs.value(), ws.value()))
                    self._save_state()
                    self._set_status_color(item_index, f"已放置备品{item_index + 1}", True)
                    return True
                self._placed.pop()
        self._set_status_color(item_index, "此处无法放置 请根据格子换位重试", True)
        return False

    def _sanitize_placed(self):
        defs = self._read_item_defs(); kept = []
        for p in self._placed:
            if p.item_index >= 3 or sum(x.item_index == p.item_index for x in kept) >= defs[p.item_index].count: continue
            kept.append(p)
        self._placed = kept

    def _on_board_changed(self):
        self._save_state(); self._board.update(); self._schedule_recalc()

    def _clear_board(self):
        self._cells = [0] * 45; self._placed = []; self._prob = None; self._set_status_color(None, "计算中…"); self._save_state(); self._board.update(); self._schedule_recalc()

    def _schedule_recalc(self):
        if self._worker and self._worker.isRunning(): self._pending_recalc = True; return
        self._start_calculation()

    def _start_calculation(self):
        if self._worker and self._worker.isRunning(): return
        # 复选框只控制结果显示，不改变求解器中的备品数量。
        state = BoardState(cells=list(self._cells), items=self._read_item_defs(), placed=list(self._placed))
        self._set_status_color(None, "计算中…")
        self._worker = _CalcWorker(state, self); self._worker.result_ready.connect(self._on_calculation_done); self._worker.failed.connect(self._on_calculation_failed); self._worker.start()

    def _on_calculation_done(self, result):
        if result.ok:
            self._prob = result.prob
            if not self._status_override: self._set_status_color(None, "计算完成")
        else:
            self._prob = None
            if not self._status_override: self._set_status_color(None, _MSG_TRANS.get(result.message, result.message) or "无有效配置")
        self._cache_prob_range()
        self._board.update()
        if self._pending_recalc: self._pending_recalc = False; self._schedule_recalc()

    def _cache_prob_range(self):
        # 一遍扫 45 格缓存区间 + 建议格（同一次求和，零额外扫描）。
        # 建议格只在有显示集合时给出；已开格与备品占格不可点，排除。
        lo, hi = 1.0, 0.0
        best = None
        if self._prob is not None:
            sel = self._selected_items()
            covered = set()
            defs = self._read_item_defs()
            for p in self._placed:
                it = defs[p.item_index]
                h, w = (it.width, it.height) if p.rotated else (it.height, it.width)
                covered.update((r, c) for r in range(p.row, p.row + h) for c in range(p.col, p.col + w))
            if sel:
                for r in range(BOARD_H):
                    for c in range(BOARD_W):
                        if self._cells[r * BOARD_W + c] or (r, c) in covered:
                            continue
                        v = min(1.0, sum(self._prob[i][r][c] for i in sel))
                        lo = min(lo, v); hi = max(hi, v)
                        if best is None or v > best[2]:
                            best = (r, c, v)
        if hi <= lo:
            lo, hi = 0.0, 1.0
        self._board._prob_min, self._board._prob_max = lo, hi
        self._board._best_cell = (best[0], best[1]) if best is not None else None
        if self._pending_recalc: self._pending_recalc = False; self._schedule_recalc()

    def _on_calculation_failed(self, message):
        self._set_status_color(None, f"计算失败：{_MSG_TRANS.get(message, message)}", True); self._board.update()

    def _prob_color(self, value):
        if is_dark():
            low, high = QColor("#B0BEC5"), QColor("#004D40")
        else:
            low, high = QColor(UI_CONFIG["prob_low"]), QColor(UI_CONFIG["prob_high"])
        value = max(0.0, min(1.0, float(value)))
        return QColor(int(low.red() + (high.red() - low.red()) * value), int(low.green() + (high.green() - low.green()) * value), int(low.blue() + (high.blue() - low.blue()) * value)).name()

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning(): self._worker.quit(); self._worker.wait(1000)
        self._save_state(); super().closeEvent(event)
