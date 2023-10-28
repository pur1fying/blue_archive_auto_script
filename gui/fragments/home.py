import json

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
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

    def __init__(self, parent: Window = None):
        super().__init__(parent=parent)
        # self._main_thread = None
        self.once = True
        self.expandLayout = ExpandLayout(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.infoBox = QFrame(self)
        self.infoBox.setFixedHeight(45)
        self.infoLayout = QHBoxLayout(self.infoBox)

        title = '蔚蓝档案自动脚本'
        self.label = SubtitleLabel(title, self)
        self.info = SubtitleLabel('正在运行：', self)
        setFont(self.label, 24)
        setFont(self.info, 24)

        self.infoLayout.addWidget(self.label, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        self.infoLayout.addWidget(self.info, 0, Qt.AlignRight)

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

        self._main_thread_attach = MainThread()
        self._main_thread_attach.button_signal.connect(self.set_button_state)
        self._main_thread_attach.logger_signal.connect(self.logger.lineEdit.append)
        self._main_thread_attach.update_signal.connect(self.call_update)
        self.startupCard.clicked.connect(self._start_clicked)
        self.setObjectName("0x00000003")

    def call_update(self, parent=None):
        with open('./config/display.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.info.setText('正在运行：' + config['running'])
        if parent:
            parent.call_update()

    def set_button_state(self, state):
        self.startupCard.button.setText(state)
        self._main_thread_attach.running = True if state == "停止" else False

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
        self.expandLayout.addWidget(self.banner)
        self.expandLayout.addWidget(self.infoBox)
        self.expandLayout.addWidget(self.startupCard)
        self.logger = LoggerBox(self.expandLayout, self)
        # self.startupCard.clicked.connect(self.__init_starter)

    def _start_clicked(self):
        self.call_update()
        if self._main_thread_attach.running:
            self._main_thread_attach.stop_play()
        else:
            self._main_thread_attach.start()

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
            self._main_thread.send('start')
            self.running = True
        else:
            self._main_thread = self.Main(logger_box=self.logger_signal, button_signal=self.button_signal,
                                          update_signal=self.update_signal)
            self._main_thread.send('start')
            self.running = True

    def stop_play(self):
        if self._main_thread is None:
            return
        self._main_thread.send('stop')
        self.running = False
        self.button_signal.emit("启动")
