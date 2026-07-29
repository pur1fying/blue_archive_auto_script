from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import ComboBox, SpinBox


METHOD_KEY = "final_restriction_rls_employ_formation_method"
UNAVAILABLE_KEY = (
    "final_restriction_rls_employ_formation_"
    "copy_clear_unit_max_unavailable_student_count"
)
REFRESH_KEY = (
    "final_restriction_rls_employ_formation_"
    "copy_clear_unit_max_refresh_count"
)
METHOD_VALUES = ("default", "copy_clear_unit")


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config

        self.formation_method_combo = ComboBox(self)
        method_labels = (
            self.tr("使用当前编队"),
            self.tr("复制通关队伍"),
        )
        self.formation_method_combo.addItems(method_labels)

        stored_method = str(config.get(METHOD_KEY))
        self.formation_method_combo.setCurrentIndex(
            METHOD_VALUES.index(stored_method)
            if stored_method in METHOD_VALUES
            else 0
        )

        self.max_unavailable_spin = SpinBox(self)
        self.max_unavailable_spin.setRange(0, 10)
        self.max_unavailable_spin.setValue(int(config.get(UNAVAILABLE_KEY)))

        self.max_refresh_spin = SpinBox(self)
        self.max_refresh_spin.setRange(0, 2_147_483_647)
        self.max_refresh_spin.setValue(int(config.get(REFRESH_KEY)))

        self.formation_method_combo.currentIndexChanged.connect(
            self._on_method_changed
        )
        self.max_unavailable_spin.valueChanged.connect(
            lambda value: self.config.set(UNAVAILABLE_KEY, int(value))
        )
        self.max_refresh_spin.valueChanged.connect(
            lambda value: self.config.set(REFRESH_KEY, int(value))
        )
        self._update_copy_controls(stored_method)

        self.v_box_layout = QVBoxLayout(self)
        self.v_box_layout.addSpacing(16)
        self.v_box_layout.setAlignment(Qt.AlignCenter)
        for label, control in (
            (self.tr("编队方式"), self.formation_method_combo),
            (self.tr("最多允许不可用学生数"), self.max_unavailable_spin),
            (self.tr("通关队伍最大刷新次数"), self.max_refresh_spin),
        ):
            row = QHBoxLayout()
            row.addWidget(QLabel(label, self), 0, Qt.AlignLeft)
            row.addStretch(1)
            row.addWidget(control, 0, Qt.AlignRight)
            self.v_box_layout.addLayout(row)
        self.v_box_layout.setContentsMargins(20, 0, 20, 20)

    def _on_method_changed(self, index):
        raw_method = METHOD_VALUES[index]
        self.config.set(METHOD_KEY, raw_method)
        self._update_copy_controls(raw_method)

    def _update_copy_controls(self, raw_method):
        enabled = raw_method == "copy_clear_unit"
        self.max_unavailable_spin.setEnabled(enabled)
        self.max_refresh_spin.setEnabled(enabled)
