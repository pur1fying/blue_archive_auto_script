from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    PrimaryPushSettingCard,
    SubtitleLabel,
    setFont,
    ExpandLayout
)

from gui.components.logger_box import LoggerBox
from window import Window

MAIN_BANNER = 'gui/assets/banner_home_bg.png'


class HomeFragment(QFrame):
    updateButtonState = pyqtSignal(bool)  # 创建用于更新按钮状态的信号

    def __init__(self, parent:Window=None):
        super().__init__(parent=parent)
        # self._main_thread = None
        self.expandLayout = ExpandLayout(self)
        self.vBoxLayout = QVBoxLayout(self)

        title = '蔚蓝档案自动脚本'
        self.once = True
        self.label = SubtitleLabel(title, self)
        setFont(self.label, 24)
        self.banner = QLabel(self)
        self.banner.setFixedHeight(200)
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)

        self.startupCard = PrimaryPushSettingCard(
            self.tr('启动'),
            FIF.CARE_RIGHT_SOLID,
            self.tr('档案，启动'),
            '开始你的档案之旅',
            self
        )
        self.__initLayout()

        self._main_thread = MainThread()
        self._main_thread.button_signal.connect(self.set_button_state)
        self._main_thread.logger_signal.connect(self.logger.lineEdit.append)
        self._main_thread.update_signal.connect(parent.call_update)
        self.startupCard.clicked.connect(self._main_thread.start)
        self.setObjectName("0x00000003")

    def set_button_state(self, state):
        self.startupCard.button.setText(state)
        self._main_thread.running = False if state == "停止" else True

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
        self.expandLayout.addWidget(self.banner)
        self.expandLayout.addWidget(self.label)
        self.expandLayout.addWidget(self.startupCard)
        self.logger = LoggerBox(self.expandLayout, self)
        # self.startupCard.clicked.connect(self.__init_starter)

    # def __init_starter(self):
    # if self._main_thread is None:
    #     from main import Main
    #     self._main_thread = Main(logger_box=self.logger)
    # threading.Thread(target=self.__worker, daemon=True).start()

    # def __worker(self):
    #     if self._main_thread.flag_run:
    #         self._main_thread.flag_run = False
    #         self.updateButtonState.emit(False)  # 发送信号，更新按钮状态
    #         self._main_thread.send('stop')
    #     else:
    #         self._main_thread.flag_run = True
    #         self.updateButtonState.emit(True)  # 发送信号，更新按钮状态
    #         self._main_thread.send('start')


class MainThread(QThread):
    button_signal = pyqtSignal(str)
    logger_signal = pyqtSignal(str)
    update_signal = pyqtSignal()

    def __init__(self):
        super(MainThread, self).__init__()
        self._main_thread = None
        self.Main = None
        self.running = False

    def run(self):
        self.button_signal.emit("停止")
        if self.Main is None:
            from main import Main
            self.Main = Main
            self._main_thread = self.Main(logger_box=self.logger_signal, button_signal=self.button_signal,
                                          update_signal=self.update_signal)

        if not self.running:
            self._main_thread.send('start')
            self.running = True
        else:
            self._main_thread.send('stop')
            self.running = False
