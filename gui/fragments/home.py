import sys
import json
import time
from random import random
from typing import Callable
from hashlib import md5
from json import JSONDecodeError

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF, TextEdit, SwitchButton, IndicatorPosition, PushButton
from qfluentwidgets import (
    PrimaryPushSettingCard,
    SubtitleLabel,
)

from core.notification import notify
from gui.util.customized_ui import AssetsWidget, FuncLabel
from gui.util.translator import baasTranslator as bt
from window import Window

if sys.platform == "win32":
    from gui.util.hotkey_manager import GlobalHotkeyManager, HotkeyInputDialog
    _Callback = Callable[[], None]

MAIN_BANNER = 'gui/assets/banner_home_bg.png'
HUMAN_TAKE_OVER_MESSAGE = "BAAS Exited, Reason : Human Take Over"


class HomeFragment(QFrame):
    updateButtonState = pyqtSignal(bool)  # 创建用于更新按钮状态的信号
    thenSignal = pyqtSignal(str)
    exitSignal = pyqtSignal(int)

    def __init__(self, parent: Window = None, config=None):
        super().__init__(parent=parent)
        self.once = True
        self.event_map = {}
        self.config = config
        self.log_entries = None
        self.crt_line_index = -1
        self.expandLayout = QVBoxLayout(self)

        self.info_box = QFrame(self)
        self.info_box.setFixedHeight(45)
        self.infoLayout = QHBoxLayout(self.info_box)

        title = self.tr("蔚蓝档案自动脚本") + ' {name}'
        self.banner_visible = self.config.get('bannerVisibility')
        self.label = SubtitleLabel(self)
        config.inject(self.label, title)
        self.info = SubtitleLabel(self.tr('无任务'), self)

        self.infoLayout.addWidget(self.label, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        self.infoLayout.addWidget(self.info, 0, Qt.AlignRight)

        self.banner = FuncLabel(self)
        self.banner.setFixedHeight(200)
        self.banner.setMaximumHeight(200)
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)
        # HACK:
        self.banner.setVisible(False)

        self.startup_card = PrimaryPushSettingCard(
            self.tr('启动'),
            FIF.CARE_RIGHT_SOLID,
            self.tr('档案，启动'),
            self.tr('开始你的档案之旅') + ' - ' + self.tr("完成后") + f' {self.config.get("then")}',
            self
        )

        self.switch_assets = SwitchButton(self.startup_card, IndicatorPosition.RIGHT)
        self.switch_assets.setOnText(self.tr('资产显示：开'))
        self.switch_assets.setOffText(self.tr('资产显示：关'))
        self.switch_assets.setChecked(self.config.get("assetsVisibility"))
        self.switch_assets.checkedChanged.connect(self._change_assets_visibility)

        self.startup_card.hBoxLayout.insertWidget(5, self.switch_assets, 0, Qt.AlignRight)
        self.startup_card.hBoxLayout.insertSpacing(6, 20)
        self.startup_card.setContentsMargins(0, 0, 0, 0)

        self.column_2 = QVBoxLayout()
        self.column_2.setSpacing(10)
        self.bottomLayout = QHBoxLayout()
        self.label_update = QLabel(self)
        self.label_logger = QLabel(self)
        self.logger_box = TextEdit(self)
        self.logger_box.setReadOnly(True)

        handler_for_logger = QHBoxLayout()
        handler_for_logger.setSpacing(0)
        handler_for_logger.setContentsMargins(0, 0, 0, 0)
        self.assets_status = AssetsWidget(config, self)
        handler_for_logger.addWidget(self.assets_status)
        self.assets_status.start_patch()
        from core.utils import host_platform_is_android

        # HACK:
        self.assets_status.show() if not host_platform_is_android and self.config.get("assetsVisibility") else self.assets_status.hide()

        self.column_2.addLayout(handler_for_logger)
        self.column_2.addWidget(self.logger_box)

        self.bottomLayout.addLayout(self.column_2)

        self.__initLayout()
        self.__connectSignalToSlot()

        self.main_thread_attach = MainThread(self.config)
        self.config.set_main_thread(self.main_thread_attach)
        self.main_thread_attach.button_signal.connect(self.set_button_state)
        self.main_thread_attach.logger_signal.connect(self.logger_box.append)
        self.main_thread_attach.update_signal.connect(self.call_update)
        self.main_thread_attach.exit_signal.connect(lambda x: sys.exit(x))

        config.add_signal('update_signal', self.main_thread_attach.update_signal)
        if sys.platform == "win32":
            self.hk_callbacks = {}
            self.hk_mgr = GlobalHotkeyManager(self)
            self.hotkey_widgets = {}
            self._init_hotkey(
                key="hotkey_run",
                default="Ctrl+Shift+R",
                callback=self.startup_card.button.click
            )

            ht_k = "hotkey_run"
            self.hotkey_desc_label = QLabel(self.tr("启停快捷键"))
            self.hotkey_push_button = PushButton(text=self.config.get(ht_k, 'Ctrl+Shift+R'))
            font = self.hotkey_push_button.font()
            font.setBold(True)
            self.hotkey_push_button.setFont(font)

            hotkey_layout = QHBoxLayout()

            hotkey_layout.setContentsMargins(0, 0, 0, 0)
            hotkey_layout.addWidget(self.hotkey_desc_label)
            hotkey_layout.addStretch()
            hotkey_layout.addWidget(self.hotkey_push_button)

            container = QWidget()
            container.setLayout(hotkey_layout)

            self.startup_card.hBoxLayout.insertWidget(7, container, 0, Qt.AlignRight)
            self.hotkey_widgets[ht_k] = {
                "hotkey_push_button": self.hotkey_push_button,
                "callback": self.hk_callbacks.get(ht_k, lambda: None)
            }
            self.hotkey_push_button.clicked.connect(lambda _: self._change_hotkey(ht_k))


        self.startup_card.clicked.connect(self._start_clicked)
        # set a hash object name for this widget
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f"{self.object_name}.HomeFragment")
        if self.config.get('autostart'):
            self.startup_card.button.click()

    def _change_hotkey(self, key: str):
        """Handles the logic for changing a hotkey via the dialog."""
        widgets = self.hotkey_widgets[key]
        current_hotkey_str = widgets["hotkey_push_button"].text().replace("<b>", "").replace("</b>", "")
        new_hotkey, ok = HotkeyInputDialog.get_hotkey(
            self.config.get_window(),
            current_hotkey_str,
            self.hk_mgr
        )
        if ok and new_hotkey != current_hotkey_str:
            widgets["hotkey_push_button"].setText(new_hotkey)
            self.config.set(key, new_hotkey)

    def _change_assets_visibility(self, checked):
        self.config.set('assetsVisibility', checked)
        self.assets_status.show() if checked else self.assets_status.hide()

    def resizeEvent(self, event):
        # auto adjust banner size
        _s = self.banner.size().width() / 1920.0
        self.banner.setFixedHeight(min(int(_s * 450), 200))
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)

    def call_update(self, data=None):
        try:
            if self.event_map == {}:
                with open(self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
                    event_config = json.load(f)
                    for item in event_config:
                        self.event_map[item['func_name']] = item['event_name']

            if data:
                if type(data[0]) is dict:
                    self.info.setText(
                        self.tr("正在运行：") + bt.tr('ConfigTranslation', self.event_map[data[0]["func_name"]]))
                else:
                    self.info.setText(self.tr("正在运行：") + bt.tr('ConfigTranslation', data[0]))
                    _main_thread_ = self.config.get_main_thread()
                    _baas_thread_ = _main_thread_.get_baas_thread()
                    if _baas_thread_ is not None:
                        pass
                    else:
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
        state = bt.tr('MainThread', state)
        self.startup_card.button.setText(state)
        self.main_thread_attach.running = True if state == bt.tr("MainThread", "停止") else False

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

    def __connectSignalToSlot(self):
        self.thenSignal.connect(self.update_content_then)
        self.exitSignal.connect(lambda x: sys.exit(x))
        self.config.add_signal('then', self.thenSignal)

    def _start_clicked(self):
        self.call_update()
        if self.main_thread_attach.running:
            self.main_thread_attach.stop_play()
        else:
            self.main_thread_attach.start()

    def get_main_thread(self):
        return self.main_thread_attach

    def update_content_then(self, option: str):
        self.startup_card.setContent(self.tr('开始你的档案之旅') + ' - ' + self.tr("完成后") + f' {option}')

    def _init_hotkey(self, key: str, default: str, callback):
        self.hk_callbacks[key] = callback
        if not self.config.has(key):
            self.config.set(key, default)
        bind_key = self.config.get(key, default)
        self.hk_mgr.register(bind_key, callback)
        self.hk_mgr.start()


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
    exit_signal = pyqtSignal(int)

    def __init__(self, config):
        super(MainThread, self).__init__()
        self.config = config
        self.hash_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self._main_thread = None
        self.Main = None
        self.running = False

    def run(self):
        self.display(self.tr("停止"))
        if not self._init_script():
            self.display(self.tr("启动"))
            return
        self.running = True
        self.display(self.tr("停止"))
        self._main_thread.logger.info("Starting Blue Archive Auto Script...")
        self._main_thread.send('start')

    def stop_play(self):
        self.running = False
        if self._main_thread is None:
            return
        self.display(self.tr("启动"))
        self._main_thread.send('stop')
        self.exit(0)

    def _init_script(self):
        while self.Main is None:
            time.sleep(0.01)
        if self._main_thread is None:
            assert self.Main is not None
            self._main_thread = self.Main.get_thread(self.config, name=self.hash_name, logger_signal=self.logger_signal,
                                                     button_signal=self.button_signal, update_signal=self.update_signal,
                                                     exit_signal=self.exit_signal)
            self.config.add_signal('update_signal', self.update_signal)
        return self._main_thread.init_all_data()

    def display(self, text):
        self.button_signal.emit(text)

    def start_hard_task(self):
        self._init_script()
        self.update_signal.emit(['困难关推图'])
        self.display(self.tr("停止"))
        if self._main_thread.send('solve', 'explore_hard_task'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('困难图推图已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.update_signal.emit([self.tr('无任务')])
        self.display(self.tr("启动"))

    def start_normal_task(self):
        self._init_script()
        self.update_signal.emit([self.tr('普通关推图')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'explore_normal_task'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('普通图推图已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.update_signal.emit([self.tr('无任务')])
        self.display(self.tr('启动'))

    def start_fhx(self):
        self._init_script()
        if self._main_thread.send('solve', 'de_clothes'):
            notify(title='BAAS', body=self.tr('反和谐成功，请重启BA下载资源'))

    def start_main_story(self):
        self._init_script()
        self.update_signal.emit([self.tr('自动主线剧情')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'main_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('主线剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.update_signal.emit([self.tr('无任务')])
        self.display(self.tr('启动'))

    def start_group_story(self):
        self._init_script()
        self.update_signal.emit([self.tr('自动小组剧情')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'group_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('小组剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display('启动')
        self.update_signal.emit([self.tr('无任务')])

    def start_mini_story(self):
        self._init_script()
        self.display(self.tr('停止'))
        self.update_signal.emit([self.tr('自动支线剧情')])
        if self._main_thread.send('solve', 'mini_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('支线剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def start_explore_activity_story(self):
        self._init_script()
        self.display(self.tr('停止'))
        self.update_signal.emit([self.tr('自动活动剧情')])
        if self._main_thread.send('solve', 'explore_activity_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('活动剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def start_explore_activity_mission(self):
        self._init_script()
        self.display(self.tr('停止'))
        self.update_signal.emit([self.tr('自动活动任务')])
        if self._main_thread.send('solve', 'explore_activity_mission'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('活动任务已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def start_explore_activity_challenge(self):
        self._init_script()
        self.update_signal.emit([self.tr('自动活动挑战')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'explore_activity_challenge'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('活动挑战推图已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def get_baas_thread(self):
        return self._main_thread


