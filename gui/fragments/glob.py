import os.path
import time
from hashlib import md5
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QHBoxLayout, QSizePolicy
from qfluentwidgets import SettingCardGroup, PushButton, VBoxLayout, ComboBox, ExpandLayout, TitleLabel, ScrollArea

from deploy.installer.toml_config import TOML_Config
from gui.components import expand
from gui.components.template_card import SimpleSettingCard
from gui.util.customized_ui import ColorSvgWidget
from gui.util.notification import success

from gui.util.config_gui import configGui, COLOR_THEME



class GlobalFragment(ScrollArea):

    def __init__(self, parent=None, config=None):
        super(GlobalFragment, self).__init__(parent=parent)
        self.config_set = config
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f"{self.object_name}.GlobalFragment")
        self.__initialized__ = False
        self._warning_svg = None
        self._optimize_window()


    def repaint_labels(self):
        """
        Repaint all labels in the fragment to apply the current theme.
        This is useful when the theme changes dynamically.
        """

        def recurse_widgets(widget):
            for child in widget.children():
                if isinstance(child, QLabel):
                    palette = child.palette()
                    palette.setColor(QPalette.WindowText, QColor(COLOR_THEME[configGui.theme.value]['text']))  # 绿色
                    child.setPalette(palette)
                recurse_widgets(child)

        recurse_widgets(self)

    def repaint_page(self):
        if self._warning_svg:
            self._warning_svg.setColor(COLOR_THEME[configGui.theme.value]['text'])
        self.repaint_labels()

    def lazy_init(self):
        if self.__initialized__:
            return self.repaint_page()
        self.__initialized__ = True

        if not os.path.exists("setup.toml"):
            self.display_require_update_message()
            return self.repaint_page()

        self.display_update_config()
        self.repaint_page()


    def _optimize_window(self):
        self.setStyleSheet('''
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        ''')
        self.viewport().setStyleSheet("background-color: transparent;")

    def display_update_config(self):
        self.config = TOML_Config("setup.toml")
        self.config.set_signals(self.config_set.get_signals())
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = TitleLabel(self.scrollWidget)
        self.settingLabel.setText(self.tr("全局更新设置"))
        self.basicGroup = SettingCardGroup(self.tr("基本"), self.scrollWidget)
        self.basicGroupItems = [
            SimpleSettingCard(
                title=self.tr('BAAS更新设置'),
                content=self.tr('选择合适的更新渠道, 填写Mirror酱CDK'),
                sub_view=expand.__dict__['baasUpdateConfig'],
                parent=self.basicGroup,
                config=self.config
            )
        ]
        self.basicGroup.addSettingCards(self.basicGroupItems)
        self.__init_display_config_layout()

    def __init_display_config_layout(self):
        self.expandLayout.setSpacing(28)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.basicGroup)
        self.setWidget(self.scrollWidget)

    def display_require_update_message(self):
        layout = VBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addStretch(1)
        layout.setSpacing(15)

        sub_layout_1 = QHBoxLayout()
        self._warning_svg = ColorSvgWidget("gui/assets/icons/ic_warning.svg", color="#ffffff", parent=self)

        self._warning_svg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._warning_svg.setFixedSize(100, 88)

        sub_layout_1.addStretch()
        sub_layout_1.addWidget(self._warning_svg)
        sub_layout_1.addStretch()
        self._warning_svg.setContentsMargins(0, 0, 0, 0)

        layout.addLayout(sub_layout_1)

        title = QLabel(self.tr("不兼容的版本"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-family: \"Microsoft YaHei\";font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("请升级 BAAS版本 ≥ 1.2.0 以使用更新配置", self)
        # --- OPTIMIZATION: Enable word wrap for subtitle ---
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-family: \"Microsoft YaHei\"; font-size: 14px;")
        layout.addWidget(subtitle)

        sub_layout_0 = QHBoxLayout(self)
        sub_layout_0.addStretch()

        github_button = PushButton("前往 GitHub 下载", self)

        def on_github_button_clicked():
            import webbrowser
            webbrowser.open("https://github.com/pur1fying/blue_archive_auto_script/releases")

        github_button.clicked.connect(on_github_button_clicked)
        sub_layout_0.addWidget(github_button, alignment=Qt.AlignCenter)

        qq_combo = ComboBox(self)
        qq_combo.addItem(self.tr("前往qq群下载"), None)

        qq_groups = [
            ("一群", "658302636"),
            ("二群", "1027430247"),
        ]

        for name, number in qq_groups:
            qq_combo.addItem(f"{name}: {number}")

        def on_qq_selected(index):
            if index == 0:
                return
            _number = qq_combo.itemText(index).split(": ")[1]
            QApplication.clipboard().setText(_number)
            success(
                self.tr("复制成功"),
                self.tr(f"已将 {_number} 复制到剪贴板, 请前往QQ添加群聊"),
                self.config_set,
                duration=1600
            )

        qq_combo.currentIndexChanged.connect(on_qq_selected)
        sub_layout_0.addWidget(qq_combo, alignment=Qt.AlignCenter)

        sub_layout_0.addStretch()

        layout.addLayout(sub_layout_0)

        layout.addStretch(2)
