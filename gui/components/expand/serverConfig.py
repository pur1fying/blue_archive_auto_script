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
        self.port_note = QLabel('常用端口：MuMu：7555；蓝叠/雷电：5555；夜神：62001或59865；', self)
        self.port_note_ = QLabel('Mumu12：16384；逍遥：21503；多开请自行查询端口。', self)
        server_type = ['官服', 'B服', '国际服']
        self.portBox = LineEdit(self)
        self.combo = ComboBox(self)
        self.combo.addItems(server_type)
        self.combo.setCurrentIndex(0)

        self.portBox.setValidator(QIntValidator(0, 65535, self))
        self.portBox.setText(self.get('adbPort'))
        self.combo.setCurrentText(self.get('server'))

        self.portBox.editingFinished.connect(self._save_port)
        self.combo.currentTextChanged.connect(self._save_server)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(48, 10, 60, 10)


        self.lay1 = QHBoxLayout(self.vBoxLayout.widget())
        self.note = QVBoxLayout(self.vBoxLayout.widget())
        self.lay2 = QHBoxLayout(self.vBoxLayout.widget())

        self.note.addWidget(self.port_note, 0, Qt.AlignLeft)
        self.note.addWidget(self.port_note_, 0, Qt.AlignLeft)
        self.note.setAlignment(Qt.AlignVCenter)

        self.lay1.addWidget(self.folderLabel, 17, Qt.AlignLeft)
        self.lay1.addWidget(self.combo, 0, Qt.AlignRight)
        self.lay1.setAlignment(Qt.AlignVCenter)

        self.lay2.addWidget(self.serverLabel, 17, Qt.AlignLeft)
        self.lay2.addWidget(self.portBox, 0, Qt.AlignRight)
        self.lay2.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addLayout(self.lay1)
        self.vBoxLayout.addLayout(self.note)
        self.vBoxLayout.addLayout(self.lay2)

    def _save_port(self):
        self.set('adbPort', self.portBox.text())
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的端口号已经被设置为：{self.portBox.text()}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()

    def _save_server(self):
        self.set('server', self.combo.currentText())
