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
    setFont
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
        self.once = True
        self.event_map = {}
        self.config = config
        self.log_entries = None
        self.crt_line_index = -1
        self.expandLayout = QVBoxLayout(self)
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

        self.bottomLayout = QHBoxLayout()
        self.label_update = QLabel(self)
        self.column_2 = QVBoxLayout(self)
        self.label_logger = QLabel(self)
        self.logger_box = TextEdit(self)
        self.logger_box.setReadOnly(True)
        self.column_2.addWidget(self.logger_box)

        self.bottomLayout.addLayout(self.column_2)
        self.bottomLayout.setSpacing(10)

        self.__initLayout()

        self._main_thread_attach = MainThread(self.config)
        self.config.set_main_thread(self._main_thread_attach)
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

    def call_update(self, data=None, parent=None):
        try:
            if self.event_map == {}:
                with open('./config/' + self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
                    event_config = json.load(f)
                    for item in event_config:
                        self.event_map[item['func_name']] = item['event_name']

            if data:
                if type(data[0]) is dict:
                    self.info.setText(f'正在运行：{self.event_map[data[0]["func_name"]]}')
                else:
                    self.info.setText(f'正在运行：{data[0]}')
                    _main_thread_ = self.config.get_main_thread()
                    _baas_thread_ = _main_thread_.get_baas_thread()
                    if _baas_thread_ is not None:
                        pass
                    else:
                        print('BAAS Thread is None')
                        _main_thread_._init_script()
                        _baas_thread_ = _main_thread_.get_baas_thread()

            # with open('./config/' + self.config.config_dir + '/display.json', 'r', encoding='utf-8') as f:
            #     config = json.load(f)
            # if config['running'] is None or config['running'] == 'Empty':
            #     self.info.setText('无任务')
            # else:
            #     self.info.setText('正在运行：' + config['running'])
            # print('call_update:', parent, args, kwargs)

            # if data:
            #     (self.parent().parent().parent()).call_update()
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
        # self.vBoxLayout.addWidget(self.logger_box)
        # self.logger_box.setLayout(self.logger_box_layout)

        self.expandLayout.addLayout(self.bottomLayout)
        self.setLayout(self.expandLayout)
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
    update_signal = pyqtSignal(list)

    def __init__(self, config):
        super(MainThread, self).__init__()
        self.config = config
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
            assert self.Main is not None
            self._main_thread = self.Main.get_thread(self.config, name=self.hash_name, logger_signal=self.logger_signal,
                                                     button_signal=self.button_signal, update_signal=self.update_signal)
            self.config.add_signal('update_signal', self.update_signal)
        self._main_thread.init_all_data()

    def display(self, text):
        self.button_signal.emit(text)

    def start_hard_task(self):
        self._init_script()
        self.update_signal.emit(['困难关推图'])
        self.display('停止')
        if self._main_thread.send('solve', 'explore_hard_task'):
            notify(title='BAAS', body='困难图推图已完成')
        self.update_signal.emit(['无任务'])
        self.display('启动')

    def start_normal_task(self):
        self._init_script()
        self.update_signal.emit(['普通关推图'])
        self.display('停止')
        if self._main_thread.send('solve', 'explore_normal_task'):
            notify(title='BAAS', body='普通图推图已完成')
        self.update_signal.emit(['无任务'])
        self.display('启动')

    def start_mumu_JP_login_fixer(self):
        self._init_script()
        if self._main_thread.send('solve', 'JP_server_mumu_login_fix'):
            notify(title='BAAS', body='成功修复')
        else:
            notify(title='BAAS', body='修复失败, 请阅读首页日志')

    def start_fhx(self):
        self._init_script()
        if self._main_thread.send('solve', 'de_clothes'):
            notify(title='BAAS', body='反和谐成功，请重启BA下载资源')

    def start_main_story(self):
        self._init_script()
        self.update_signal.emit(['自动主线剧情'])
        self.display('停止')
        if self._main_thread.send('solve', 'main_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body='主线剧情已完成')
        self.update_signal.emit(['无任务'])
        self.display('启动')

    def start_group_story(self):
        self._init_script()
        self.update_signal.emit(['自动小组剧情'])
        self.display('停止')
        if self._main_thread.send('solve', 'group_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body='小组剧情已完成')
        self.display('启动')
        self.update_signal.emit(['无任务'])

    def start_mini_story(self):
        self._init_script()
        self.display('停止')
        self.update_signal.emit(['自动支线剧情'])
        if self._main_thread.send('solve', 'mini_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body='支线剧情已完成')
        self.display('启动')
        self.update_signal.emit(['无任务'])

    def start_explore_activity_story(self):
        self._init_script()
        self.display('停止')
        self.update_signal.emit(['自动活动剧情'])
        if self._main_thread.send('solve', 'explore_activity_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body='活动剧情已完成')
        self.display('启动')
        self.update_signal.emit(['无任务'])

    def start_explore_activity_mission(self):
        self._init_script()
        self.display('停止')
        self.update_signal.emit(['自动活动任务'])
        if self._main_thread.send('solve', 'explore_activity_mission'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body='活动任务已完成')
        self.display('启动')
        self.update_signal.emit(['无任务'])

    def start_explore_activity_challenge(self):
        self._init_script()
        self.update_signal.emit(['自动活动挑战'])
        self.display('停止')
        if self._main_thread.send('solve', 'explore_activity_challenge'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body='活动挑战推图已完成')
        self.display('启动')
        self.update_signal.emit(['无任务'])

    def get_baas_thread(self):
        return self._main_thread
