import json
import time
from hashlib import md5
from json import JSONDecodeError
from random import random

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF, TextEdit
from qfluentwidgets import (
    PrimaryPushSettingCard,
    SubtitleLabel,
    setFont,
    ExpandLayout
)

from core.notification import notify
from window import Window

MAIN_BANNER = 'gui/assets/banner_home_bg.png'


class MyQLabel(QLabel):
    button_clicked_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(MyQLabel, self).__init__(parent)

    def mouseReleaseEvent(self, QMouseEvent):
        self.button_clicked_signal.emit()

    def connect_customized_slot(self, func):
        self.button_clicked_signal.connect(func)


class HomeFragment(QFrame):
    updateButtonState = pyqtSignal(bool)  # 创建用于更新按钮状态的信号

    def __init__(self, parent: Window = None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.once = True
        self.expandLayout = ExpandLayout(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.info_box = QFrame(self)
        self.info_box.setFixedHeight(45)
        self.infoLayout = QHBoxLayout(self.info_box)

        title = f'蔚蓝档案自动脚本 {self.config.get("name")}'
        self.banner_visible = self.config.get('bannerVisibility')
        self.label = SubtitleLabel(title, self)
        self.info = SubtitleLabel('无任务', self)
        setFont(self.label, 24)
        setFont(self.info, 24)

        self.infoLayout.addWidget(self.label, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        self.infoLayout.addWidget(self.info, 0, Qt.AlignRight)

        self.banner = MyQLabel(self)
        self.banner.setFixedHeight(200)
        self.banner.setMaximumHeight(200)
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)
        self.banner.setVisible(self.banner_visible)

        self.startup_card = PrimaryPushSettingCard(
            self.tr('启动'),
            FIF.CARE_RIGHT_SOLID,
            self.tr('档案，启动'),
            '开始你的档案之旅',
            self
        )

        self.logger_box = TextEdit(self)
        self.logger_box.setReadOnly(True)

        self.__initLayout()

        self._main_thread_attach = MainThread()
        self._main_thread_attach.config = self.config
        self._main_thread_attach.button_signal.connect(self.set_button_state)
        self._main_thread_attach.logger_signal.connect(self.logger_box.append)
        self._main_thread_attach.update_signal.connect(self.call_update)
        config.add_signal('update_signal', self._main_thread_attach.update_signal)
        # self.banner.button_clicked_signal.connect(self._main_thread_attach.get_screen)
        self.startup_card.clicked.connect(self._start_clicked)
        # set a hash object name for this widget
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(self.object_name)

    def resizeEvent(self, event):
        # 自动调整banner尺寸（保持比例）
        _s = self.banner.size().width() / 1920.0
        self.banner.setFixedHeight(min(int(_s * 450), 200))
        # 重新设置banner图片以保持清晰度
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)
        if self.banner_visible:
            self.logger_box.setFixedHeight(int(self.parent().height() * 0.35))
        else:
            self.logger_box.setFixedHeight(int(self.parent().height() * 0.7))

    def call_update(self, parent=None):
        try:
            with open('./config/' + self.config.config_dir + '/display.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            if config['running'] is None or config['running'] == 'Empty':
                self.info.setText('无任务')
            else:
                self.info.setText('正在运行：' + config['running'])
            if parent:
                parent.call_update()
        except JSONDecodeError:
            # 有时json会是空值报错, 原因未知
            print("Empty JSON data")

    def set_button_state(self, state):
        self.startup_card.button.setText(state)
        self._main_thread_attach.running = True if state == "停止" else False

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
        if self.banner_visible:
            self.expandLayout.addWidget(self.banner)
        self.expandLayout.addWidget(self.info_box)
        self.expandLayout.addWidget(self.startup_card)
        self.expandLayout.addWidget(self.logger_box)
        # self.startupCard.clicked.connect(self.__init_starter)

    def _start_clicked(self):
        self.call_update()
        if self._main_thread_attach.running:
            self._main_thread_attach.stop_play()
        else:
            self._main_thread_attach.start()

    def get_main_thread(self):
        return self._main_thread_attach

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
        self.config = None
        self.hash_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self._main_thread = None
        self.Main = None
        self.running = False

    def run(self):
        self.running = True
        self.display('停止')
        self._init_script()
        self._main_thread.logger.info("Starting Blue Archive Auto Script...")
        self._main_thread.send('start')

    def stop_play(self):
        self.running = False
        if self._main_thread is None:
            return
        self.display('启动')
        self._main_thread.send('stop')
        self.exit(0)

    def _init_script(self):
        while self.Main is None:
            time.sleep(0.01)
        if self._main_thread is None:
            self._main_thread = self.Main.get_thread(self.config, name=self.hash_name, logger_signal=self.logger_signal,
                                                     button_signal=self.button_signal, update_signal=self.update_signal)
        self._main_thread.init_all_data()

    def display(self, text):
        self.button_signal.emit(text)


    def start_hard_task(self):
        self._init_script()
        self.display('停止')
        if self._main_thread.send('solve', 'explore_hard_task'):
            notify(title='BAAS', body='困难图推图已完成')

    def start_normal_task(self):
        self._init_script()
        self.display('停止')
        if self._main_thread.send('solve', 'explore_normal_task'):
            notify(title='BAAS', body='普通图推图已完成')

    def start_fhx(self):
        self._init_script()
        if self._main_thread.send('solve', 'de_clothes'):
            notify(title='BAAS', body='反和谐成功，请重启BA下载资源')

    def start_main_story(self):
        self._init_script()
        if self._main_thread.send('solve', 'main_story'):
            notify(title='BAAS', body='主线剧情已完成')

    def start_group_story(self):
        self._init_script()
        if self._main_thread.send('solve', 'group_story'):
            notify(title='BAAS', body='团队剧情已完成')

    def start_mini_story(self):
        self._init_script()
        if self._main_thread.send('solve', 'mini_story'):
            notify(title='BAAS', body='支线剧情已完成')
