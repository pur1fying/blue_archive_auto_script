from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from qfluentwidgets import LineEdit, SwitchButton, ComboBox

from gui.util import notification


class Layout(QWidget):
    """ Folder item """

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.info_widget = self.parent().parent().parent()
        self.serverLabel = QLabel(self.tr('请填写您的截图间隔：'), self)
        self.screenshot_box = LineEdit(self)
        self.warningLabel = QLabel(self.tr('这些功能在运行多个实例时可能无法按预期工作。涉及模拟器的操作将遵循“模拟器启动设置”中的设置。'))
        self.autostartLabel = QLabel(self.tr('启动Baas后直接运行'), self) # Auto Run task after launched
        self.autostartSwitch = SwitchButton(self)
        self.thenLabel = QLabel(self.tr('完成后'), self) # Then
        self.screenshotLabel = QLabel(self.tr('截图方式'), self) # Then
        self.controlLabel = QLabel(self.tr('控制方式'), self) # Then
        self.thenCombo = ComboBox(self)
        self.screenshotCombo = ComboBox(self)
        self.controlCombo = ComboBox(self)

        validator = QDoubleValidator(0.0, 65535.0, 2, self)
        self.screenshot_box.setValidator(validator)
        self.screenshot_box.setText(self.config.get('screenshot_interval'))
        self.autostartSwitch.setChecked(self.config.get('autostart'))
        self.thenCombo.addItems([
            self.tr('无动作'), # Do Nothing
            self.tr('退出 Baas'),  # Exit Baas
            self.tr('退出 模拟器'), # Exit Emulator
            self.tr('退出 Baas 和 模拟器'), # Exit Baas and Emulator
            self.tr('关机')]) # Shutdown
        self.thenCombo.setCurrentText(self.config.get('then'))

        self.screenshotCombo.addItems(self.config.static_config.get('screenshot_methods'))
        self.screenshotCombo.setCurrentText(self.config.get('screenshot_method'))

        self.controlCombo.addItems(self.config.static_config.get('control_methods'))
        self.controlCombo.setCurrentText(self.config.get('control_method'))

        self.screenshot_box.textChanged.connect(self._save_port)
        self.autostartSwitch.checkedChanged.connect(self._save_autostart)
        self.thenCombo.currentTextChanged.connect(self._save_then)
        self.screenshotCombo.currentTextChanged.connect(self._save_screenshot_method)
        self.controlCombo.currentTextChanged.connect(self._save_control_method)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(48, 10, 60, 15)

        self.lay1 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay1.addWidget(self.serverLabel, 17, Qt.AlignLeft)
        self.lay1.addWidget(self.screenshot_box, 0, Qt.AlignRight)

        self.lay1.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addLayout(self.lay1)

        self.warningLabel.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addWidget(self.warningLabel)

        self.lay2 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay2.addWidget(self.autostartLabel, 17, Qt.AlignLeft)
        self.lay2.addWidget(self.autostartSwitch, 0, Qt.AlignRight)

        self.lay2.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addLayout(self.lay2)

        self.lay3 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay3.addWidget(self.thenLabel, 17, Qt.AlignLeft)
        self.lay3.addWidget(self.thenCombo, 0, Qt.AlignRight)

        self.lay4 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay4.addWidget(self.screenshotLabel, 17, Qt.AlignLeft)
        self.lay4.addWidget(self.screenshotCombo, 0, Qt.AlignRight)

        self.lay5 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay5.addWidget(self.controlLabel, 17, Qt.AlignLeft)
        self.lay5.addWidget(self.controlCombo, 0, Qt.AlignRight)

        self.lay3.setAlignment(Qt.AlignVCenter)
        self.lay4.setAlignment(Qt.AlignVCenter)
        self.lay5.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addLayout(self.lay3)
        self.vBoxLayout.addLayout(self.lay4)
        self.vBoxLayout.addLayout(self.lay5)

    def _save_port(self, changed_text=None):
        self.config.set('screenshot_interval', changed_text)
        notification.success(self.tr('截图间隔'), f'{self.tr("你的截图间隔已经被设置为：")}{changed_text}', self.config)

    def _save_autostart(self, enable: bool):
        self.config.set('autostart', enable)

    def _save_then(self, option: str):
        self.config.set('then', option)
        then_signal = self.config.get_signal('then')
        if then_signal is not None:
            then_signal.emit(option)

        notification.success(
            self.tr('完成后'),
            f'{self.tr("你的截图间隔已经被设置为：")}{option}',
            self.config
        )

    def _save_screenshot_method(self, option: str):
        self.config.set('screenshot_method', option)
        notification.success(
            self.tr('截图方式'),
            f'{self.tr("你的截图方式已经被设置为：")}{option}',
            self.config
        )

    def _save_control_method(self, option: str):
        self.config.set('control_method', option)
        notification.success(
            self.tr('控制方式'),
            f'{self.tr("你的控制方式已经被设置为：")}{option}',
            self.config
        )
