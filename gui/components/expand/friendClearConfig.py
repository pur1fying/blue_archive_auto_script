from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import SpinBox


LEVEL_KEY = "clear_friend_level_limit"
LOGIN_DAYS_KEY = "clear_friend_last_login_time_days"
RANK_KEY = "clear_friend_last_total_assault_rank_limit"


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config

        self.disabled_tip_label = QLabel(
            self.tr("以下清理条件设为 -1 时表示禁用。"), self
        )

        self.level_limit_spin = SpinBox(self)
        self.last_login_days_spin = SpinBox(self)
        self.total_assault_rank_spin = SpinBox(self)

        for spin, key in (
            (self.level_limit_spin, LEVEL_KEY),
            (self.last_login_days_spin, LOGIN_DAYS_KEY),
            (self.total_assault_rank_spin, RANK_KEY),
        ):
            spin.setRange(-1, 2_147_483_647)
            spin.setValue(int(self.config.get(key)))
            spin.valueChanged.connect(
                lambda value, config_key=key: self.config.set(
                    config_key, int(value)
                )
            )

        self.v_box_layout = QVBoxLayout(self)
        self.v_box_layout.addSpacing(16)
        self.v_box_layout.addWidget(self.disabled_tip_label)
        for label, spin in (
            ("好友等级清理阈值", self.level_limit_spin),
            ("最后登录天数阈值", self.last_login_days_spin),
            ("上次总力战排名阈值", self.total_assault_rank_spin),
        ):
            row = QHBoxLayout()
            row.addWidget(QLabel(self.tr(label), self), 0, Qt.AlignLeft)
            row.addStretch(1)
            row.addWidget(spin, 0, Qt.AlignRight)
            self.v_box_layout.addLayout(row)
        self.v_box_layout.setContentsMargins(20, 0, 20, 20)
