import gc
import threading
import time
from hashlib import md5
from importlib import import_module
from random import random
from weakref import ref

from PyQt5 import sip
from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSignal
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


class _StatusUpdateEmitter(QObject):
    updated = pyqtSignal(object, object)


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
        self.listWidget.itemClicked.connect(
            self._clear_queue_interaction_state)
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
        self._status_stop = threading.Event()
        self._status_updates_enabled = True
        self._status_emitter = _StatusUpdateEmitter(self)
        fragment_ref = ref(self)

        def apply_status_update(current_task, task_list):
            fragment = fragment_ref()
            if fragment is not None:
                fragment._apply_status_update(current_task, task_list)

        self._status_update_slot = apply_status_update
        self._status_emitter.updated.connect(
            self._status_update_slot, type=Qt.QueuedConnection)
        self._status_connection_active = True
        self._status_thread = threading.Thread(
            target=self._run_status_refresh,
            args=(ref(self),),
            daemon=True,
        )
        self._status_thread.start()
        self.__initLayout()
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f"{self.object_name}.ProcessFragment")

    @staticmethod
    def _run_status_refresh(fragment_ref):
        fragment = fragment_ref()
        if fragment is not None:
            fragment.refresh_status()

    def refresh_status(self):
        while not self._status_stop.is_set():
            current_task, task_list = self._collect_status()
            if self._status_stop.is_set():
                break
            self._status_emitter.updated.emit(current_task, task_list)
            if self._status_stop.wait(2):
                break

    def _collect_status(self):
        baas_thread = self.baas_thread
        if baas_thread is None:
            main_thread = self.config.get_main_thread()
            baas_thread = (
                main_thread.get_baas_thread() if main_thread else None)
            self.baas_thread = baas_thread
        if baas_thread is None:
            return None, ()

        current_task = baas_thread.scheduler.getCurrentTaskName()
        task_list = baas_thread.scheduler.getWaitingTaskList()
        return current_task, tuple(task_list or ())

    def _apply_status_update(self, current_task, task_list):
        if (
            self._status_stop.is_set()
            or not self._status_updates_enabled
        ):
            return
        current_text = (
            bt.tr('ConfigTranslation', current_task)
            if current_task
            else self.tr("暂无正在执行的任务")
        )
        queue_items = (
            [bt.tr('ConfigTranslation', task) for task in task_list]
            if task_list
            else [self.tr("暂无队列中的任务")]
        )
        self.on_status.setText(current_text)
        self._set_queue_items(queue_items)

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
                # Avoid cyclic PyQt wrapper collection while Qt.py initializes.
                gc.collect()
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
        graph_view = getattr(self, "graph_view", None)
        if graph_view is not None and not sip.isdeleted(graph_view):
            graph_view.save_layout()

    def event(self, event):
        if event.type() == QEvent.DeferredDelete:
            self._stop_status_refresh()
            self._save_graph_layout()
        return super().event(event)

    def closeEvent(self, event):
        self._stop_status_refresh()
        self._save_graph_layout()
        super().closeEvent(event)

    def hideEvent(self, event):
        self._save_graph_layout()
        super().hideEvent(event)

    def _stop_status_refresh(self) -> None:
        self._status_updates_enabled = False
        self._status_stop.set()
        if (
            self._status_thread.is_alive()
            and threading.current_thread() is not self._status_thread
        ):
            self._status_thread.join()
        if self._status_connection_active:
            self._status_emitter.updated.disconnect(
                self._status_update_slot)
            self._status_connection_active = False

    @staticmethod
    def _create_queue_item(text):
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemIsEnabled)
        return item

    def _clear_queue_interaction_state(self, _item=None):
        self.listWidget.clearSelection()
        self.listWidget.setCurrentRow(-1)

    def _set_queue_items(self, task_list):
        self.listWidget.clear()
        for task in task_list:
            self.listWidget.addItem(self._create_queue_item(task))
        self._clear_queue_interaction_state()

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
