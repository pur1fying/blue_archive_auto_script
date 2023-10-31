from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from qfluentwidgets import LineEdit, ComboBox, InfoBar, InfoBarIcon, InfoBarPosition

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    """ Folder item """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.info_widget = self.parent().parent().parent()
        self.folderLabel = QLabel('请选择您的服务器', self)
        self.serverLabel = QLabel('请填写您的adb端口号', self)
        server_type = ['官服', 'B服']
        self.portBox = LineEdit(self)
        self.combo = ComboBox(self)
        self.combo.addItems(server_type)
        self.combo.setCurrentIndex(0)

        self.portBox.setValidator(QIntValidator(0, 65535, self))
        self.portBox.setText(self.get('adbPort'))
        self.combo.setCurrentText(self.get('server'))

        self.portBox.textChanged.connect(self._save_port)
        self.combo.currentTextChanged.connect(self._save_server)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(48, 0, 60, 0)
        self.setFixedHeight(120)

        self.lay1 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay2 = QHBoxLayout(self.vBoxLayout.widget())

        self.lay1.addWidget(self.folderLabel, 17, Qt.AlignLeft)
        self.lay1.addWidget(self.combo, 0, Qt.AlignRight)
        self.lay1.setAlignment(Qt.AlignVCenter)

        self.lay2.addWidget(self.serverLabel, 17, Qt.AlignLeft)
        self.lay2.addWidget(self.portBox, 0, Qt.AlignRight)
        self.lay2.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addLayout(self.lay1)
        self.vBoxLayout.addLayout(self.lay2)

    def _save_port(self, changed_text=None):
        self.set('adbPort', self.portBox.text())
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的端口号已经被设置为：{changed_text}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()

    def _save_server(self):
        self.set('server', self.combo.currentText())
