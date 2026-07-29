import threading
import time
from hashlib import md5
from importlib import import_module
from random import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QHBoxLayout, QListWidgetItem,
                             QStackedWidget, QVBoxLayout, QWidget)
from qfluentwidgets import (ScrollArea, TitleLabel, SubtitleLabel, ListWidget, StrongBodyLabel, ComboBox,
                            SegmentedWidget, ToolTipPosition, ToolTipFilter)

from gui.components import expand
from gui.util import notification
from gui.util.config_gui import configGui
from gui.util.style_sheet import StyleSheet
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
        # Scheduler switch
        self.titleLineLayout = QHBoxLayout()
        self.scheduler_controls_layout = QHBoxLayout()
        _scheduler_selector_label = SubtitleLabel(self.tr("调度状态"), self)
        _scheduler_selector_label.setToolTip(self.tr("当BAAS新增调度任务时的启用状态"))
        _scheduler_selector_label.installEventFilter(ToolTipFilter(_scheduler_selector_label, position=ToolTipPosition.TOP))

        self._scheduler_states = ("default", "on", "off")
        self.scheduler_selector = ComboBox(self)
        self.scheduler_selector.addItems([
            bt.tr('ConfigTranslation', '默认'),
            bt.tr('ConfigTranslation', '开'),
            bt.tr('ConfigTranslation', '关'),
        ])
        self.scheduler_selector.setCurrentIndex(
            self._scheduler_states.index(
                configGui.get(configGui.schedulerNewEventEnableState)))
        self.scheduler_selector.currentIndexChanged.connect(
            self._scheduler_state_changed)
        configGui.schedulerNewEventEnableState.valueChanged.connect(
            self._sync_scheduler_state)
        self.scheduler_controls_layout.addWidget(_scheduler_selector_label)
        self.scheduler_controls_layout.addWidget(self.scheduler_selector)

        self.view_selector = SegmentedWidget(self)
        self.table_view_button = self.view_selector.addItem(
            "table", self.tr("表格视图"), self.show_table_view)
        self.graph_view_button = self.view_selector.addItem(
            "graph", self.tr("图形视图"), self.show_graph_view)
        self.view_selector.setCurrentItem("table")
        self.scheduler_controls_layout.addWidget(self.view_selector)

        self.titleLineLayout.addWidget(self.settingLabel, 1, Qt.AlignLeft)
        self.titleLineLayout.addLayout(self.scheduler_controls_layout, 0)

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
        self.listWidget.setSelectionMode(QAbstractItemView.NoSelection)
        self.listWidget.setFocusPolicy(Qt.NoFocus)
        self.label_queuing = SubtitleLabel(self.tr("任务队列"), self)

        self.vBox2.addWidget(self.label_queuing)
        self.vBox2.addWidget(self.listWidget)

        self.HBoxLayout.addLayout(self.vBox1)
        self.HBoxLayout.addLayout(self.vBox2)

        self.VBoxLayout.addLayout(self.titleLineLayout)
        self.VBoxLayout.addLayout(self.HBoxLayout)
        self.displayWidget.setLayout(self.VBoxLayout)

        self.table_view = expand.__dict__['featureSwitch'].Layout(config=config)
        self.graph_view = None
        self._table_stale = False
        self.editor_stack = QStackedWidget(self)
        self.editor_stack.addWidget(self.table_view)
        self.VBoxWrapperLayout.addWidget(self.displayWidget)
        self.VBoxWrapperLayout.addWidget(self.editor_stack)

        self.processWidget.setLayout(self.VBoxWrapperLayout)

        self.baas_thread = None
        self.config = config
        self._status_thread = threading.Thread(
            target=self.refresh_status, daemon=True)
        self._status_thread.start()
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

                self._set_queue_items(task_list)
            else:
                self.on_status.setText(self.tr("暂无正在执行的任务"))
                self._set_queue_items([self.tr("暂无队列中的任务")])
                main_thread = self.config.get_main_thread()
                self.baas_thread = main_thread.get_baas_thread() if main_thread else None
            time.sleep(2)

    def _scheduler_state_changed(self, index):
        configGui.set(
            configGui.schedulerNewEventEnableState,
            self._scheduler_states[index])

    def _sync_scheduler_state(self, state):
        index = self._scheduler_states.index(state)
        if self.scheduler_selector.currentIndex() == index:
            return
        self.scheduler_selector.blockSignals(True)
        self.scheduler_selector.setCurrentIndex(index)
        self.scheduler_selector.blockSignals(False)

    def show_table_view(self) -> None:
        self.view_selector.setCurrentItem("table")
        if self.editor_stack.currentWidget() is self.table_view:
            return
        if self.graph_view is not None:
            self.graph_view.save_layout()
        self.editor_stack.setCurrentWidget(self.table_view)
        self.table_view.reload_from_disk()
        self._table_stale = False

    def show_graph_view(self) -> None:
        if self.editor_stack.currentWidget() is self.graph_view:
            self.view_selector.setCurrentItem("graph")
            return
        try:
            if self.graph_view is None:
                graph_module = import_module(
                    "gui.components.scheduler_graph")
                self.graph_view = graph_module.SchedulerGraphView(
                    self.config.config_dir, parent=self.editor_stack)
                self.graph_view.data_changed.connect(
                    self._on_graph_data_changed)
                self.editor_stack.addWidget(self.graph_view)
            self.graph_view.reload_from_disk()
        except ModuleNotFoundError as error:
            if error.name is None or not error.name.startswith("NodeGraphQt"):
                raise
            self.view_selector.setCurrentItem("table")
            notification.error(
                self.tr("图形视图"),
                self.tr("图形视图需要安装 NodeGraphQt"),
                self.config,
                duration=4000,
            )
            return
        self.editor_stack.setCurrentWidget(self.graph_view)
        self.view_selector.setCurrentItem("graph")

    def _on_graph_data_changed(self) -> None:
        self._table_stale = True
        if self.editor_stack.currentWidget() is self.table_view:
            self.table_view.reload_from_disk()
            self._table_stale = False

    def _save_graph_layout(self) -> None:
        if self.graph_view is not None:
            self.graph_view.save_layout()

    def hideEvent(self, event):
        self._save_graph_layout()
        super().hideEvent(event)

    @staticmethod
    def _create_queue_item(text):
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemIsEnabled)
        return item

    def _set_queue_items(self, task_list):
        self.listWidget.clear()
        for task in task_list:
            self.listWidget.addItem(self._create_queue_item(task))
        self.listWidget.clearSelection()
        self.listWidget.setCurrentRow(-1)

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
