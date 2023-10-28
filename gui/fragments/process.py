import json
import threading
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (ExpandLayout, ScrollArea, TitleLabel, SubtitleLabel, ListWidget, StrongBodyLabel)

lock = threading.Lock()
DISPLAY_CONFIG_PATH = './config/display.json'


class ProcessFragment(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.listWidget = ListWidget(self)
        self.settingLabel = TitleLabel(self.tr("调度状态"), self)

        self.label_running = SubtitleLabel(self.tr("执行中"), self)
        self.on_status = StrongBodyLabel(self.tr("暂无正在执行的任务"), self)
        self.on_status.resize(800, 35)
        self.on_status.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        self.on_status.setAlignment(Qt.AlignCenter)
        self.label_queuing = SubtitleLabel(self.tr("队列中"), self)
        self.listWidget.setFixedSize(800, 380)

        t_daemon = threading.Thread(target=self.refresh_status, daemon=True)
        t_daemon.start()

        self.__initLayout()
        self.setObjectName("0x00000005")

    def refresh_status(self):
        while True:
            with lock:
                with open(DISPLAY_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    _event_display = json.load(f)
                    if _event_display['running'] is not None:
                        self.on_status.setText(_event_display['running'])
                    else:
                        self.on_status.setText("暂无正在执行的任务")
                    if _event_display['queue'] is not None:
                        self.listWidget.clear()
                        self.listWidget.addItems(_event_display['queue'])
                    else:
                        self.listWidget.clear()
                        self.listWidget.addItems(["暂无队列中的任务"])
            time.sleep(2)

    def __initLayout(self):
        self.expandLayout.setSpacing(28)
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
        self.expandLayout.addWidget(self.settingLabel)
        self.expandLayout.addWidget(self.label_running)
        self.expandLayout.addWidget(self.on_status)
        self.expandLayout.addWidget(self.label_queuing)
        self.expandLayout.addWidget(self.listWidget)
        self.setWidget(self.scrollWidget)
