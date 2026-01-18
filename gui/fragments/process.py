import threading
import time
from hashlib import md5
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (ScrollArea, TitleLabel, SubtitleLabel, ListWidget, StrongBodyLabel, ComboBox,
                            ToolTipPosition, ToolTipFilter)

from gui.components import expand
from gui.util.style_sheet import StyleSheet
from gui.util.translator import baasTranslator as bt
from core.utils import is_android

lock = threading.Lock()
DISPLAY_CONFIG_PATH = './config/display.json'


class ProcessFragment(ScrollArea):
    def __init__(self, parent, config):
        super().__init__(parent=parent)
        self.processWidget = QWidget()
        self.displayWidget = QWidget()
        self.displayWidget.setFixedHeight(200)
        self.settingLabel = TitleLabel(self.tr("调度状态"), self)
        # Scheduler switch
        self.titleLineLayout = QHBoxLayout()
        _scheduler_selector = config.get('new_event_enable_state')
        _scheduler_selector_layout = QHBoxLayout()
        _scheduler_selector_label = SubtitleLabel(self.tr("调度状态"), self)
        _scheduler_selector_label.setToolTip(self.tr("当BAAS新增调度任务时的启用状态"))
        _scheduler_selector_label.installEventFilter(ToolTipFilter(_scheduler_selector_label, position=ToolTipPosition.TOP))

        __dict__for_scheduler_selector = {
            '开': 'on',
            '关': 'off',
            '默认': 'default',
        }
        __reverse_dict__for_scheduler_selector = {v: k for k, v in __dict__for_scheduler_selector.items()}
        _raw_scheduler_selector = __reverse_dict__for_scheduler_selector[_scheduler_selector]
        self.scheduler_selector = ComboBox(self)
        self.scheduler_selector.addItems([
            bt.tr('ConfigTranslation', '开'),
            bt.tr('ConfigTranslation', '关'),
            bt.tr('ConfigTranslation', '默认'),
        ])
        self.scheduler_selector.setCurrentText(bt.tr('ConfigTranslation', _raw_scheduler_selector))
        self.scheduler_selector.currentTextChanged.connect(
            lambda x: config.set('new_event_enable_state', __dict__for_scheduler_selector[bt.undo(x)]))
        _scheduler_selector_layout.addWidget(_scheduler_selector_label)
        _scheduler_selector_layout.addWidget(self.scheduler_selector)

        self.titleLineLayout.addWidget(self.settingLabel, 1, Qt.AlignLeft)
        self.titleLineLayout.addLayout(_scheduler_selector_layout, 0)

        # Process display
        self.VBoxWrapperLayout = QVBoxLayout()
        self.VBoxLayout = QVBoxLayout()
        self.HBoxLayout = QHBoxLayout()

        self.vBox1 = QVBoxLayout()
        self.label_running = SubtitleLabel(self.tr("执行中"), self)
        self.label_running.setFixedHeight(30)
        self.on_status = StrongBodyLabel(self.tr("暂无正在执行的任务"), self)
        # self.on_status.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.on_status.setFixedWidth(300)
        self.on_status.setAlignment(Qt.AlignCenter)
        self.vBox1.addWidget(self.label_running)
        self.vBox1.addWidget(self.on_status)

        self.vBox2 = QVBoxLayout()
        self.listWidget = ListWidget(self)
        self.label_queuing = SubtitleLabel(self.tr("任务队列"), self)

        self.vBox2.addWidget(self.label_queuing)
        self.vBox2.addWidget(self.listWidget)

        self.HBoxLayout.addLayout(self.vBox1)
        self.HBoxLayout.addLayout(self.vBox2)

        self.VBoxLayout.addLayout(self.titleLineLayout)
        self.VBoxLayout.addLayout(self.HBoxLayout)
        self.displayWidget.setLayout(self.VBoxLayout)

        if is_android():
            self.label_running.setVisible(False)
            self.on_status.setVisible(False)
            self.label_queuing.setVisible(False)
            self.listWidget.setVisible(False)
            self.displayWidget.setFixedHeight(0)

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
        self.setObjectName(f"{self.object_name}.ProcessFragment")

    def refresh_status(self):
        while True:
            if self.baas_thread is not None:
                crt_task = self.baas_thread.scheduler.getCurrentTaskName()
                task_list = self.baas_thread.scheduler.getWaitingTaskList()

                crt_task = crt_task if crt_task else self.tr("暂无正在执行的任务")
                task_list = [bt.tr('ConfigTranslation', task) for task in task_list] if task_list else [
                    self.tr("暂无队列中的任务")]
                self.on_status.setText(bt.tr('ConfigTranslation', crt_task))

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

        self.on_status.setObjectName('on_status')
        self.listWidget.setObjectName('listWidget')
        StyleSheet.PROCESS.apply(self.on_status)
        StyleSheet.PROCESS.apply(self.listWidget)
