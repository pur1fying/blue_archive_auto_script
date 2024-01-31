from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from qfluentwidgets import LineEdit, InfoBar, InfoBarIcon, InfoBarPosition, PushButton

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    """ Folder item """

    def __init__(self, parent=None, config_dir: str = 'config.json'):
        super().__init__(parent=parent)
        ConfigSet.__init__(self, config_dir)
        print(self.config_dir)
        self.info_widget = self.parent().parent().parent()
        self.serverLabel = QLabel('请填写您的截图间隔：', self)
        self.screenshot_box = LineEdit(self)
        validator = QDoubleValidator(0.0, 65535.0, 2, self)
        self.screenshot_box.setValidator(validator)
        self.screenshot_box.setText(self.get('screenshot_interval'))

        self.screenshot_box.textChanged.connect(self._save_port)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(48, 10, 60, 15)
        # self.setFixedHeight(50)

        self.lay1 = QHBoxLayout(self.vBoxLayout.widget())
        self.lay1.addWidget(self.serverLabel, 17, Qt.AlignLeft)
        self.lay1.addWidget(self.screenshot_box, 0, Qt.AlignRight)

        self.lay1.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addLayout(self.lay1)

    def _save_port(self, changed_text=None):
        self.set('screenshot_interval', changed_text)
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'你的截屏间隔已经被设置为：{changed_text}',
            orient=Qt.Vertical,  # vertical layout
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.info_widget
        )
        w.show()
