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
        self.warningLabel = QLabel(self.tr('警告：在运行多个实例时，这些功能可能无法按预期工作。'))
        self.autostartLabel = QLabel(self.tr('启动Baas后直接运行'), self) # Auto Run task after launched
        self.autostartSwitch = SwitchButton(self)
        self.thenLabel = QLabel(self.tr('完成后'), self) # Then
        self.thenCombo = ComboBox(self)
        
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

        self.screenshot_box.textChanged.connect(self._save_port)
        self.autostartSwitch.checkedChanged.connect(self._save_autostart)
        self.thenCombo.currentTextChanged.connect(self._save_then)

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

        self.lay3.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addLayout(self.lay3)

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
            f'{self.tr("你的截图间隔已经被设置为：")}{option}. If the script is running, restart it for the effects to take place.',
            self.config
        )
