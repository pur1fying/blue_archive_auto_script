"""咖啡厅邀请配置的响应式双卡布局。"""
from __future__ import annotations

from functools import partial

from PyQt5.QtCore import Qt, QPointF, QRectF, QSize
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPalette,
    QRadialGradient,
)
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QBoxLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QFrame,
    QComboBox,
    QSizePolicy,
    QStyledItemDelegate,
)

from qfluentwidgets import LineEdit, SwitchButton

from gui.util import notification
from gui.util.translator import baasTranslator as bt


class _ComboItemDelegate(QStyledItemDelegate):
    """Give every popup option the same readable height as the combo."""

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(max(size.width(), 1), 34)


class _CafeComboBox(QComboBox):
    """Native combo with a guaranteed visible right-side indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._arrow = QLabel("▼", self)
        self._arrow.setAlignment(Qt.AlignCenter)
        self._arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._arrow.setStyleSheet(
            "QLabel{color:#527da6;background:transparent;font-size:10px;}"
            "QLabel:disabled{color:#999999;}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrow.setGeometry(max(0, self.width() - 24), 0, 24, self.height())
        self._arrow.raise_()

    def changeEvent(self, event):
        super().changeEvent(event)
        self._arrow.setEnabled(self.isEnabled())


def _tune_combo(combo: QComboBox, item_count: int = 0) -> None:
    """Keep cafe option menus compact, immediate and visually light."""
    visible = 10 if item_count > 10 else max(item_count, 1)
    combo.setMaxVisibleItems(visible)
    combo.setMinimumHeight(34)
    combo.setMaximumHeight(280)

    palette = combo.palette()
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(238, 247, 255))
    palette.setColor(QPalette.Highlight, QColor(219, 239, 255))
    palette.setColor(QPalette.HighlightedText, QColor(26, 26, 26))
    combo.setPalette(palette)
    combo.setStyleSheet(
        "QComboBox {"
        "  color: #1a1a1a;"
        "  background: #ffffff;"
        "  border: 1px solid rgba(80, 120, 170, 80);"
        "  border-radius: 5px;"
        "  padding: 5px 26px 5px 9px;"
        "  min-height: 20px;"
        "}"
        "QComboBox:hover {"
        "  border-color: rgba(55, 125, 190, 145);"
        "  background: #ffffff;"
        "}"
        "QComboBox:focus {"
        "  border-color: rgba(45, 125, 200, 180);"
        "}"
        "QComboBox:disabled {"
        "  color: #888888;"
        "  background: #eeeeee;"
        "  border-color: rgba(0, 0, 0, 55);"
        "}"
        "QComboBox::drop-down {"
        "  width: 24px;"
        "  border: none;"
        "  background: transparent;"
        "}"
        "QComboBox QAbstractItemView {"
        "  color: #1a1a1a;"
        "  background: #ffffff;"
        "  alternate-background-color: #f6fbff;"
        "  border: 1px solid rgba(80, 120, 170, 70);"
        "  border-radius: 6px;"
        "  padding: 4px;"
        "  outline: none;"
        "  selection-background-color: #dbefff;"
        "  selection-color: #1a1a1a;"
        "}"
    )
    view = combo.view()
    view.setMouseTracking(True)
    view.viewport().setMouseTracking(True)
    view.setItemDelegate(_ComboItemDelegate(view))
    view.setAlternatingRowColors(False)
    view.setStyleSheet(
        "QAbstractItemView {"
        "  color: #1a1a1a;"
        "  background: #ffffff;"
        "  border: 1px solid rgba(80, 120, 170, 70);"
        "  padding: 4px;"
        "  outline: none;"
        "  selection-background-color: #dbefff;"
        "  selection-color: #1a1a1a;"
        "}"
        "QAbstractItemView::item {"
        "  min-height: 28px;"
        "  padding: 3px 8px;"
        "  border-radius: 4px;"
        "}"
        "QAbstractItemView::item:hover {"
        "  color: #1a1a1a;"
        "  background: #dbefff;"
        "}"
        "QAbstractItemView::item:selected {"
        "  color: #1a1a1a;"
        "  background: #dbefff;"
        "}"
    )


class GradientPanel(QFrame):
    """Simple panel chrome that follows the application palette."""

    def __init__(
        self,
        parent=None,
        *,
        object_name: str = "cafePanel",
        title_h: int = 40,
    ):
        super().__init__(parent)
        self.setObjectName(object_name)
        self._title_h = title_h
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QFrame#{object_name} {{"
            "  border: 1px solid rgba(80, 120, 170, 40);"
            "  border-radius: 10px;"
            "  background: palette(base);"
            "}"
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        clip = QPainterPath()
        clip.addRoundedRect(
            QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5),
            10,
            10,
        )
        painter.setClipPath(clip)

        title_height = min(float(self._title_h), float(rect.height()))
        width = float(rect.width())
        height = float(rect.height())
        body_height = max(1.0, height - title_height)

        title_bloom = QRadialGradient(
            QPointF(width * 0.10, title_height * 0.78),
            max(width * 0.55, title_height * 3.2, 90.0),
        )
        title_bloom.setColorAt(0.00, QColor(176, 208, 236, 150))
        title_bloom.setColorAt(0.22, QColor(196, 220, 242, 95))
        title_bloom.setColorAt(0.48, QColor(222, 236, 248, 38))
        title_bloom.setColorAt(0.72, QColor(240, 246, 252, 10))
        title_bloom.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillRect(QRectF(0, 0, width, title_height), title_bloom)

        title_sweep = QRadialGradient(
            QPointF(width * 0.22, title_height * 1.05),
            max(width * 0.42, 70.0),
        )
        title_sweep.setColorAt(0.00, QColor(188, 216, 240, 55))
        title_sweep.setColorAt(0.45, QColor(220, 234, 246, 18))
        title_sweep.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillRect(QRectF(0, 0, width, title_height), title_sweep)

        ink = QPointF(width * 0.96, height * 0.97)
        short = height < 220.0
        radius = max(width, height) * (0.62 if short else 0.58)
        radius = min(
            radius,
            max(
                width * (0.70 if short else 0.68),
                body_height * (1.15 if short else 1.05),
            ),
        )
        radius = max(radius, 96.0)

        body_bloom = QRadialGradient(ink, radius)
        body_bloom.setFocalPoint(QPointF(width * 0.985, height * 0.992))
        body_bloom.setColorAt(0.00, QColor(180, 212, 238, 118))
        body_bloom.setColorAt(0.16, QColor(192, 218, 242, 88))
        body_bloom.setColorAt(0.34, QColor(210, 230, 244, 48))
        body_bloom.setColorAt(0.54, QColor(228, 240, 248, 18))
        body_bloom.setColorAt(0.74, QColor(244, 248, 252, 4))
        body_bloom.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillRect(
            QRectF(0, title_height, width, body_height),
            body_bloom,
        )

        bottom_sweep = QRadialGradient(
            QPointF(width * 0.70, height * 1.04),
            max(
                width * (0.60 if short else 0.58),
                body_height * (0.88 if short else 0.78),
                72.0 if short else 80.0,
            ),
        )
        bottom_sweep.setColorAt(0.00, QColor(176, 208, 236, 58))
        bottom_sweep.setColorAt(0.36, QColor(208, 226, 244, 24))
        bottom_sweep.setColorAt(0.68, QColor(232, 242, 250, 6))
        bottom_sweep.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillRect(
            QRectF(0, title_height, width, body_height),
            bottom_sweep,
        )


class CafeCard(GradientPanel):
    def __init__(self, title: str, parent=None):
        super().__init__(parent, object_name="cafeCard", title_h=42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(150)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(14, 10, 14, 12)
        self.root.setSpacing(8)
        self.root.setAlignment(Qt.AlignTop)

        self.title_lbl = QLabel(title, self)
        self.title_lbl.setFixedHeight(24)
        self.title_lbl.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:15px;'
            'font-weight:600;color:#1a1a1a;background:transparent;'
        )
        self.root.addWidget(self.title_lbl, 0, Qt.AlignTop)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 12, 0, 0)
        self.body.setSpacing(8)
        self.body.setAlignment(Qt.AlignTop)
        self.root.addLayout(self.body, 0)
        self.root.addStretch(1)
        self.set_active(True)

    def set_active(self, active: bool, *, animate: bool = False):
        background = "palette(base)" if active else "palette(alternate-base)"
        border = (
            "rgba(80, 120, 170, 40)"
            if active
            else "rgba(0, 0, 0, 30)"
        )
        self.setStyleSheet(
            "QFrame#cafeCard {"
            f"  border: 1px solid {border};"
            "  border-radius: 10px;"
            f"  background: {background};"
            "}"
        )
        self.title_lbl.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:15px;'
            f'font-weight:600;color:{"#1a1a1a" if active else "#666"};'
            'background:transparent;'
        )
        self._set_body_enabled(active)

    def _set_body_enabled(self, on: bool):
        for i in range(self.body.count()):
            item = self.body.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setEnabled(on)
            lay = item.layout()
            if lay is not None:
                self._enable_layout(lay, on)

    def _enable_layout(self, layout, on: bool):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setEnabled(on)
            sub = item.layout()
            if sub is not None:
                self._enable_layout(sub, on)


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.setMinimumHeight(0)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.name_dict = {
            self.tr("邀请最低好感度学生"): "lowest_affection",
            self.tr("邀请最高好感度学生"): "highest_affection",
            self.tr("邀请收藏的学生"): "starred",
            self.tr("指定姓名邀请"): "name",
        }
        self.name_dict_rev = {v: k for k, v in self.name_dict.items()}

        self.student_name = []
        try:
            students = list(getattr(self.config.static_config, "student_names", None) or [])
        except Exception:
            students = []
        mode = getattr(self.config, "server_mode", "CN")
        for student in students:
            try:
                if not student.get(mode + "_implementation"):
                    continue
                name = student.get(mode + "_name") or ""
                if name:
                    self.student_name.append(name)
                    if not bt.isChinese():
                        bt.addStudent(student.get("CN_name") or name, name)
            except Exception:
                continue

        self.pat_round = self.config.get("cafe_reward_affection_pat_round")
        self.pat_styles = [bt.tr("ConfigTranslation", "拖动礼物")]
        self.pat_style = self.config.get("patStyle") or self.pat_styles[0]
        if self.pat_style not in self.pat_styles:
            self.pat_style = self.pat_styles[0]

        self.root_layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        self.root_layout.setContentsMargins(16, 12, 16, 12)
        self.root_layout.setSpacing(14)

        # ----- LEFT shared panel with title-bar gradient -----
        self.shared_panel = GradientPanel(
            self,
            object_name="cafeShared",
            title_h=40,
        )
        left = self.shared_panel
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(14, 10, 14, 12)
        left_lay.setSpacing(10)

        left_title = QLabel(self.tr("通用设置"), left)
        left_title.setFixedHeight(24)
        left_title.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:15px;'
            'font-weight:600;color:#1a1a1a;background:transparent;'
        )
        left_lay.addWidget(left_title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 10, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        self.swCollect = self._make_switch("cafe_reward_collect_hour_reward")
        self.swInvite = self._make_switch("cafe_reward_use_invitation_ticket")
        self.swExchange = self._make_switch("cafe_reward_allow_exchange_student")
        self.swDup = self._make_switch("cafe_reward_allow_duplicate_invite")

        grid.addWidget(self._stack_cell(self.tr("是否领取奖励:"), self.swCollect), 0, 0)
        grid.addWidget(self._stack_cell(self.tr("是否使用邀请券:"), self.swInvite), 0, 1)
        grid.addWidget(self._stack_cell(self.tr("是否允许学生更换服饰:"), self.swExchange), 1, 0)
        grid.addWidget(self._stack_cell(self.tr("是否允许重复邀请:"), self.swDup), 1, 1)

        self.inputPatRound = LineEdit()
        self.inputPatRound.setFixedWidth(56)
        self.inputPatRound.setText(str(self.pat_round))
        self.inputPatRound.editingFinished.connect(self.__accept_pat_round)
        grid.addWidget(
            self._inline_cell(self.tr("摸头轮数 (轮数越高越不会漏摸):"), self.inputPatRound),
            2, 0, 1, 2,
        )

        # Locked dropdown (still a ComboBox — unlock by setEnabled(True) later).
        self.inputPatStyle = _CafeComboBox()
        self.inputPatStyle.addItems(self.pat_styles)
        self.inputPatStyle.setCurrentText(self.pat_style)
        _tune_combo(self.inputPatStyle, len(self.pat_styles))
        self.inputPatStyle.setEnabled(False)  # locked; keep widget for future options
        self.inputPatStyle.setToolTip(self.tr("当前仅支持「拖动礼物」，选项已锁定"))
        grid.addWidget(
            self._inline_cell(self.tr("摸头方式:"), self.inputPatStyle),
            3, 0, 1, 2,
        )

        left_lay.addLayout(grid)
        left_lay.addStretch(1)
        self.root_layout.addWidget(left, 2)

        # ----- RIGHT -----
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(12)

        self.card1 = CafeCard(self.tr("1号咖啡厅"), self)
        self.card1.setProperty("cafeNumber", 1)
        self._cafe1_body_host = QWidget()
        self._cafe1_body = QVBoxLayout(self._cafe1_body_host)
        self._cafe1_body.setContentsMargins(0, 0, 0, 0)
        self._cafe1_body.setSpacing(8)
        self.card1.body.addWidget(self._cafe1_body_host)
        self.card1.set_active(True)
        right.addWidget(self.card1, 1)

        self.card2 = CafeCard(self.tr("2号咖啡厅"), self)
        self.card2.setProperty("cafeNumber", 2)
        en_host = QWidget()
        en_row = QHBoxLayout(en_host)
        en_row.setContentsMargins(0, 0, 0, 0)
        en_lab = QLabel(self.tr("是否有二号咖啡厅:"))
        en_lab.setStyleSheet("background: transparent;")
        en_row.addWidget(en_lab, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.second_switch = SwitchButton()
        self.second_switch.setChecked(bool(self.config.get("cafe_reward_has_no2_cafe")))
        self.second_switch.checkedChanged.connect(self.Slot_for_no_2_cafe_Checkbox)
        en_row.addWidget(self.second_switch, 0, Qt.AlignLeft | Qt.AlignVCenter)
        en_row.addStretch(1)
        self.card2.body.addWidget(en_host)

        self._cafe2_body_host = QWidget()
        self._cafe2_body = QVBoxLayout(self._cafe2_body_host)
        self._cafe2_body.setContentsMargins(0, 0, 0, 0)
        self._cafe2_body.setSpacing(8)
        self.card2.body.addWidget(self._cafe2_body_host)
        right.addWidget(self.card2, 1)

        self.root_layout.addLayout(right, 3)
        self._rebuild_cafe_bodies()
        self._update_layout_direction(self.width())

    def _update_layout_direction(self, width: int):
        direction = (
            QBoxLayout.TopToBottom
            if int(width or 0) < 640
            else QBoxLayout.LeftToRight
        )
        if self.root_layout.direction() != direction:
            self.root_layout.setDirection(direction)
            self.setProperty(
                "layoutMode",
                "narrow" if direction == QBoxLayout.TopToBottom else "wide",
            )
            self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_layout_direction(event.size().width())

    def _make_switch(self, config_name: str) -> SwitchButton:
        sw = SwitchButton()
        sw.setChecked(bool(self.config.get(config_name)))
        sw.checkedChanged.connect(lambda state, k=config_name: self.config.set(k, state))
        return sw

    def _stack_cell(self, label: str, switch: SwitchButton) -> QFrame:
        """Solid white cell — gradient must not show through controls."""
        box = QFrame()
        box.setObjectName("cafeCell")
        box.setStyleSheet(
            "QFrame#cafeCell {"
            "  background: palette(base);"
            "  border: 1px solid rgba(0,0,0,18);"
            "  border-radius: 8px;"
            "}"
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)
        lb = QLabel(label)
        lb.setWordWrap(True)
        lb.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        lb.setStyleSheet("background: transparent;")
        lay.addWidget(lb)
        lay.addWidget(switch, 0, Qt.AlignHCenter)
        return box

    def _inline_cell(self, label: str, widget: QWidget) -> QFrame:
        box = QFrame()
        box.setObjectName("cafeCell")
        box.setStyleSheet(
            "QFrame#cafeCell {"
            "  background: palette(base);"
            "  border: 1px solid rgba(0,0,0,18);"
            "  border-radius: 8px;"
            "}"
        )
        lay = QHBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 8)
        lb = QLabel(label)
        lb.setWordWrap(True)
        lb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        lb.setStyleSheet("background: transparent;")
        lay.addWidget(lb, 1)
        lay.addWidget(widget, 0)
        return box

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sub = item.layout()
                if sub is not None:
                    self._clear_layout(sub)
            del item

    def _rebuild_cafe_bodies(self):
        self._clear_layout(self._cafe1_body)
        self._clear_layout(self._cafe2_body)
        self.cafe_reward_invite1_criterion = self.config.get("cafe_reward_invite1_criterion")
        self.cafe_reward_invite2_criterion = self.config.get("cafe_reward_invite2_criterion")
        self._fill_cafe_invite(self._cafe1_body, 1)
        self._fill_cafe_invite(self._cafe2_body, 2)
        has2 = bool(self.config.get("cafe_reward_has_no2_cafe"))
        self.card2.set_active(has2)
        if self.card2.body.count() >= 1:
            w = self.card2.body.itemAt(0).widget()
            if w is not None:
                w.setEnabled(True)

    def _fill_cafe_invite(self, body: QVBoxLayout, cafe_no: int):
        cur_mode = getattr(self, f"cafe_reward_invite{cafe_no}_criterion")
        mode_row = QHBoxLayout()
        lab = QLabel(self.tr("邀请券选择模式："))
        lab.setWordWrap(True)
        lab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        lab.setStyleSheet("background: transparent;")
        mode_row.addWidget(lab, 0)
        mode_select = _CafeComboBox()
        keys = list(self.name_dict.keys())
        mode_select.addItems(keys)
        _tune_combo(mode_select, len(keys))
        current_text = self.name_dict_rev.get(cur_mode, keys[0])
        mode_select.blockSignals(True)
        mode_select.setCurrentText(current_text)
        mode_select.blockSignals(False)
        mode_select.currentTextChanged.connect(partial(self._alt_cafe_mode, cafe_no))
        mode_row.addWidget(mode_select, 1)
        body.addLayout(mode_row)

        if cur_mode == "starred":
            body.addLayout(self._init_student_com_(cafe_no))
        elif cur_mode == "name":
            for layout in self._init_student_sel(cafe_no):
                body.addLayout(layout)

    def _init_student_sel(self, no):
        label = QLabel(self.tr("列表选择你要添加邀请的学生，失焦后写入草稿："))
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        label.setStyleSheet("background: transparent;")
        laySelect, layInput = QHBoxLayout(), QHBoxLayout()
        comboStudent = _CafeComboBox()
        comboStudent.addItem(self.tr("添加学生"))
        comboStudent.addItems(self.student_name)
        _tune_combo(comboStudent, len(self.student_name) + 1)
        lineEditStudent = LineEdit()
        lineEditStudent.setMinimumWidth(160)
        favor_student = self.check_valid_student_names(self.config.get(f"favorStudent{no}"))
        lineEditStudent.setText(",".join(favor_student))
        laySelect.addWidget(label, 1)
        laySelect.addWidget(comboStudent, 0)
        layInput.addWidget(lineEditStudent, 1)
        comboStudent.currentTextChanged.connect(
            partial(self.__add_student_name, no, lineEditStudent, comboStudent)
        )
        lineEditStudent.editingFinished.connect(
            partial(self.__student_name_changed, no, lineEditStudent)
        )
        return [laySelect, layInput]

    def _init_student_com_(self, no):
        layout = QHBoxLayout()
        label = QLabel(self.tr("选择收藏学生的序号"))
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        label.setStyleSheet("background: transparent;")
        comboPosition = _CafeComboBox()
        comboPosition.addItems(["1", "2", "3", "4", "5"])
        _tune_combo(comboPosition, 5)
        comboPosition.blockSignals(True)
        comboPosition.setCurrentText(
            str(self.config.get(f"cafe_reward_invite{no}_starred_student_position"))
        )
        comboPosition.blockSignals(False)
        comboPosition.currentTextChanged.connect(
            lambda text: self.config.set(
                f"cafe_reward_invite{no}_starred_student_position", int(text)
            )
        )
        layout.addWidget(label, 1)
        layout.addWidget(comboPosition, 0)
        return layout

    def __add_student_name(self, no, lineEdit, comboStudent, text):
        if text == self.tr("添加学生"):
            return
        favor_student = list(self.config.get(f"favorStudent{no}") or [])
        favor_student.append(text)
        favor_student = self.check_valid_student_names(favor_student)
        self.config.set(f"favorStudent{no}", favor_student)
        lineEdit.setText(",".join(favor_student))
        comboStudent.blockSignals(True)
        comboStudent.setCurrentIndex(0)
        comboStudent.blockSignals(False)

    def __student_name_changed(self, no, lineEdit):
        favor_student = self.check_valid_student_names(lineEdit.text().split(","))
        self.config.set(f"favorStudent{no}", favor_student)
        lineEdit.setText(",".join(favor_student))

    def __accept_pat_round(self, *_):
        text = self.inputPatRound.text().strip()
        if text not in (str(i) for i in range(4, 16)):
            notification.error("摸头轮数设置错误", "请设置为4-15之间的整数", self.config)
        else:
            self.pat_round = int(text)
            self.config.set("cafe_reward_affection_pat_round", self.pat_round)
            if not getattr(self.config, "is_draft", False):
                notification.success(
                    "摸头轮数设置成功", f"当前值为：{self.pat_round}", self.config
                )

    @staticmethod
    def check_valid_student_names(favor_student):
        temp, appeared = [], set()
        for name in favor_student or []:
            name = name.strip()
            if name and name not in appeared:
                temp.append(name)
                appeared.add(name)
        return temp

    def Slot_for_no_2_cafe_Checkbox(self, state):
        self.config.set("cafe_reward_has_no2_cafe", state)
        self.card2.set_active(bool(state))
        if self.card2.body.count() >= 1:
            w = self.card2.body.itemAt(0).widget()
            if w is not None:
                w.setEnabled(True)

    def _alt_cafe_mode(self, no, text):
        if text not in self.name_dict:
            return
        self.config.set(f"cafe_reward_invite{no}_criterion", self.name_dict[text])
        body = self._cafe1_body if no == 1 else self._cafe2_body
        self._clear_layout(body)
        setattr(self, f"cafe_reward_invite{no}_criterion", self.name_dict[text])
        self._fill_cafe_invite(body, no)
