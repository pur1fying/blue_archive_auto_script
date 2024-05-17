import threading
import time
from hashlib import md5
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (ScrollArea, TitleLabel, SubtitleLabel, ListWidget, StrongBodyLabel)

from gui.components import expand

from gui.util.translator import baasTranslator as bt


lock = threading.Lock()
DISPLAY_CONFIG_PATH = './config/display.json'


class ProcessFragment(ScrollArea):
    def __init__(self, parent, config):
        super().__init__(parent=parent)
        self.processWidget = QWidget()
        self.displayWidget = QWidget()
        self.displayWidget.setFixedHeight(200)
        self.settingLabel = TitleLabel(self.tr("调度状态"), self)

        self.VBoxWrapperLayout = QVBoxLayout()
        self.VBoxLayout = QVBoxLayout()
        self.HBoxLayout = QHBoxLayout()

        self.vBox1 = QVBoxLayout()
        self.label_running = SubtitleLabel(self.tr("执行中"), self)
        self.label_running.setFixedHeight(30)
        self.on_status = StrongBodyLabel(self.tr("暂无正在执行的任务"), self)
        # self.on_status.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.on_status.setStyleSheet('''
                        font-size:18px;
                        padding:10px;
                        font-weight:bold;
                        background-color:#e0f0e0;
                        border-radius: 10px;''')
        self.on_status.setFixedWidth(300)
        self.on_status.setAlignment(Qt.AlignCenter)
        self.vBox1.addWidget(self.label_running)
        self.vBox1.addWidget(self.on_status)


        self.vBox2 = QVBoxLayout()
        self.listWidget = ListWidget(self)
        self.listWidget.setStyleSheet('''
                background-color: #e0e0f0;
                padding: 10px;
                border-radius: 10px;
            ''')
        self.label_queuing = SubtitleLabel(self.tr("任务队列"), self)

        self.vBox2.addWidget(self.label_queuing)
        self.vBox2.addWidget(self.listWidget)

        self.HBoxLayout.addLayout(self.vBox1)
        self.HBoxLayout.addLayout(self.vBox2)

        self.VBoxLayout.addWidget(self.settingLabel)
        self.VBoxLayout.addLayout(self.HBoxLayout)
        self.displayWidget.setLayout(self.VBoxLayout)

        feature_panel = expand.__dict__['featureSwitch'].Layout(config=config)
        self.VBoxWrapperLayout.addWidget(self.displayWidget)
        self.VBoxWrapperLayout.addWidget(feature_panel)

        self.processWidget.setLayout(self.VBoxWrapperLayout)

        self.baas_thread = None
        self.config = config
        t_daemon = threading.Thread(target=self.refresh_status, daemon=True)
        t_daemon.start()
        self.__initLayout()
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(self.object_name)

    def refresh_status(self):
        while True:
            if self.baas_thread is not None:
                crt_task = self.baas_thread.scheduler.get_current_task()
                task_list = self.baas_thread.scheduler.get_current_task_list()
                print(crt_task, task_list)

                crt_task = crt_task if crt_task else self.tr("暂无正在执行的任务")
                task_list = [task for task in task_list] if task_list else [self.tr("暂无队列中的任务")]
                self.on_status.setText(crt_task)
                self.listWidget.clear()
                self.listWidget.addItems(task_list)
            else:
                self.on_status.setText(self.tr("暂无正在执行的任务"))
                self.listWidget.clear()
                self.listWidget.addItems([self.tr("暂无队列中的任务")])
                main_thread = self.config.get_main_thread()
                self.baas_thread = main_thread.get_baas_thread() if main_thread else None
            time.sleep(2)

    def __initLayout(self):
        # self.expandLayout.setSpacing(28)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.settingLabel.setObjectName('settingLabel')
        self.setStyleSheet('''
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        ''')
        self.viewport().setStyleSheet("background-color: transparent;")
        self.setWidget(self.processWidget)
