import json
import time
from copy import deepcopy
from datetime import datetime
from functools import partial

from PyQt5 import sip
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHeaderView, QVBoxLayout
from qfluentwidgets import CheckBox, TableWidget, PushButton, ComboBox, CaptionLabel, MessageBoxBase, \
    SubtitleLabel

from gui.components.expand.expandTemplate import TemplateLayoutV2
from gui.util.config_gui import configGui, COLOR_THEME
from gui.util.customized_ui import ClickFocusLineEdit
from gui.util.translator import baasTranslator as bt


class DetailSettingMessageBox(MessageBoxBase):
    def __init__(self, detail_config: dict, all_label_list: list, parent=None, cs=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr('配置详情'), self)
        configItems = [
            {
                'label': self.tr('事件名称'),
                'dataType': 'str',
                'key': 'event_name',
                'readOnly': True
            },
            {
                'label': self.tr('优先级'),
                'dataType': 'int',
                'key': 'priority'
            },
            {
                'label': self.tr('执行间隔'),
                'dataType': 'int',
                'key': 'interval',
            },
            {
                'label': self.tr('每日重置'),
                'dataType': 'list',
                'key': 'daily_reset',
            },
            {
                'label': self.tr('禁用时间段'),
                'dataType': 'list',
                'key': 'disabled_time_range',
            },
            {
                'label': self.tr('前置任务'),
                'dataType': 'list',
                'key': 'pre_task',
                'presets': []
            },
            {
                'label': self.tr('后置任务'),
                'dataType': 'list',
                'key': 'post_task',
                'presets': []
            }
        ]

        self.configWidget = TemplateLayoutV2(configItems, self, detail_config, all_label_list=all_label_list, cs=cs)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.configWidget)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))
        self.widget.setMinimumWidth(350)


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self._event_config = None
        self._read_config()
        assert self._event_config is not None
        self._crt_order_config = self._event_config
        self.config.get_signal('update_signal').connect(self._refresh_time)
        configGui.themeChanged.connect(self._on_theme_changed)

        self.boxes, self.qLabels, self.times, self.check_boxes, self.config_buttons = [], [], [], [], []
        self._init_components(self._event_config)

        self.vBox = QVBoxLayout(self)
        self.option_layout = QHBoxLayout()
        self.all_check_box = PushButton(self.tr('全部(不)启用'), self)

        self.all_check_box.clicked.connect(self.all_check)
        self.option_layout.addWidget(self.all_check_box)
        self.option_layout.addStretch(1)

        self.op_2 = PushButton(self.tr('刷新执行时间'), self)
        self.option_layout.addWidget(self.op_2)
        self.op_2.clicked.connect(self._refresh)

        self.option_layout.addStretch(1)
        self.label_3 = self._make_event_label(self.tr('排序方式：'))
        self.op_3 = ComboBox(self)
        self.op_3.addItems([self.tr('默认排序'), self.tr('按下次执行时间排序')])

        self.op_3.currentIndexChanged.connect(self._sort)
        self.option_layout.addWidget(self.label_3)
        self.option_layout.addWidget(self.op_3)

        self.tableView = TableWidget(self)
        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(len(self.qLabels))
        self.tableView.setColumnCount(4)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setHorizontalHeaderLabels(
            [self.tr('事件'), self.tr('下次刷新时间'), self.tr('启用'), self.tr('更多配置')])
        self.tableView.setColumnWidth(0, 175)
        self.tableView.setColumnWidth(1, 175)
        self.tableView.setColumnWidth(2, 50)
        self.tableView.setColumnWidth(3, 50)
        for i in range(len(self.enable_list)):
            self.tableView.setCellWidget(i, 0, self.qLabels[i])
            self.tableView.setCellWidget(i, 1, self.times[i])
            self.tableView.setCellWidget(i, 2, self.boxes[i])
            self.tableView.setCellWidget(i, 3, self.config_buttons[i])
        self.vBox.addLayout(self.option_layout)
        self.vBox.addWidget(self.tableView)

    def _init_components(self, config_list):
        self.enable_list = [item['enabled'] for item in config_list]
        self.labels = [item['event_name'] for item in config_list]
        self.next_ticks = [item['next_tick'] for item in config_list]
        for i in range(len(self.enable_list)):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.enable_list[i])
            cbx_wrapper = QWidget()
            cbx_layout = QHBoxLayout(cbx_wrapper)
            cbx_layout.addWidget(t_cbx, 1, Qt.AlignCenter)
            cbx_layout.setContentsMargins(30, 0, 0, 0)
            cbx_wrapper.setLayout(cbx_layout)
            t_ccs = self._make_event_label(bt.tr('ConfigTranslation', self.labels[i]))
            t_ncs = ClickFocusLineEdit(self)
            t_ncs.setClearButtonEnabled(True)
            t_ncs.setText(str(datetime.fromtimestamp(self.next_ticks[i])).split('.')[0])
            t_ncs.textChanged.connect(self._update_config)
            t_cbx.stateChanged.connect(self._update_config)
            self.times.append(t_ncs)
            self.qLabels.append(t_ccs)
            self.boxes.append(cbx_wrapper)
            self.check_boxes.append(t_cbx)

            t_cfbs = PushButton(self.tr('详细配置'), self)
            t_cfbs.clicked.connect(partial(self._update_detail, i))
            cfbs_wrapper = QWidget()
            cfbs_layout = QHBoxLayout()
            cfbs_layout.setContentsMargins(0, 0, 0, 0)
            cfbs_layout.addWidget(t_cfbs, 1, Qt.AlignCenter)
            cfbs_wrapper.setLayout(cfbs_layout)
            self.config_buttons.append(cfbs_wrapper)

    def _make_event_label(self, text: str) -> CaptionLabel:
        """Create a CaptionLabel with correct text color for the current theme."""
        label = CaptionLabel(text)
        # Intentionally keep the default alignment (AlignLeft | AlignVCenter).
        # Forcing Qt.AlignCenter pushes the text down to the vertical middle
        # of the row, which looks noticeably different from the initial
        # render where the cell height fits the text -- so the row appears
        # to "jump" the moment the user picks a different sort mode.
        color = COLOR_THEME[configGui.theme.value]['text']
        label.setStyleSheet(f'color: {color};')
        return label

    def _on_theme_changed(self):
        """Update all event labels when the theme switches."""
        color = COLOR_THEME[configGui.theme.value]['text']
        for label in self.qLabels:
            label.setStyleSheet(f'color: {color};')
        if hasattr(self, 'label_3'):
            self.label_3.setStyleSheet(f'color: {color};')

    def _read_config(self):
        with open(self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
            s = f.read()
            if s == '':
                return
            self._event_config = json.loads(s)

    def _save_config(self):
        with open(self.config.config_dir + '/event.json', 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)

    def _sort(self):
        temp = deepcopy(self._event_config)

        # mode 0: default, mode 1: by next_tick
        if self.op_3.currentIndex() == 0:
            temp.sort(key=lambda x: x['priority'])
        elif self.op_3.currentIndex() == 1:
            temp.sort(key=lambda x: (not x['enabled'], x['next_tick']))
        self._crt_order_config = temp

        # IMPORTANT: do NOT tear down and rebuild the cell widgets here.
        # The previous implementation did ``self.tableView.deleteLater()``
        # + ``TableWidget(self)`` to recreate the table on every sort, which
        # left the old cell widgets alive (children of ``self``) until the
        # event loop processed the deferred deletions. Combined with the
        # global ``styleSheetManager`` sweep that runs on every theme change
        # (``updateStyleSheet`` in qfluentwidgets), this raced with the
        # deferred deletion and crashed the app (0xC0000409, STATUS_STACK_
        # BUFFER_OVERRUN, raised by Qt's Q_ASSERT / __fastfail).
        #
        # The fix is to keep one set of cell widgets for the lifetime of the
        # table and just *update their data in place* when the sort order
        # changes. The widgets are created once in ``__init__`` /
        # ``_init_components``; ``_sort`` only rewrites the visible state.
        self._refresh_cell_contents(temp)

    def _refresh_cell_contents(self, temp):
        """Rewrite each row's widget data to reflect a new ordering.

        Called both on the very first sort (after the table is built) and on
        every subsequent sort. If the number of events somehow changed
        between the table's creation and now, rebuild the widgets from
        scratch -- this should never happen in practice (events are only
        reordered, never added or removed at runtime), but the fallback keeps
        the table self-healing.
        """
        if len(temp) != len(self.qLabels):
            self._rebuild_cell_widgets(temp)
            return

        for ind, unit in enumerate(temp):
            label = self.qLabels[ind]
            label.setText(bt.tr('ConfigTranslation', unit['event_name']))

            line_edit = self.times[ind]
            line_edit.blockSignals(True)
            line_edit.setText(str(datetime.fromtimestamp(unit['next_tick'])).split('.')[0])
            line_edit.blockSignals(False)

            cbx = self.check_boxes[ind]
            cbx.blockSignals(True)
            cbx.setChecked(unit['enabled'])
            cbx.blockSignals(False)

        self.enable_list = [unit['enabled'] for unit in temp]
        self.labels = [unit['event_name'] for unit in temp]
        self.next_ticks = [unit['next_tick'] for unit in temp]

    def _rebuild_cell_widgets(self, temp):
        """Tear down and recreate every cell widget.

        Used as a fallback when the number of rows changes between sorts
        (which doesn't happen in the current code path). Kept for
        completeness / future-proofing.
        """
        self._remove_all_cell_widgets()
        self.tableView.clearContents()
        self.tableView.setRowCount(len(temp))

        self.qLabels, self.times, self.check_boxes = [], [], []
        self.boxes, self.config_buttons = [], []

        for ind, unit in enumerate(temp):
            t_ccs = self._make_event_label(bt.tr('ConfigTranslation', unit['event_name']))
            self.tableView.setCellWidget(ind, 0, t_ccs)
            self.qLabels.append(t_ccs)

            t_ncs = ClickFocusLineEdit(self)
            t_ncs.setText(str(datetime.fromtimestamp(unit['next_tick'])).split('.')[0])
            t_ncs.textChanged.connect(self._update_config)
            self.tableView.setCellWidget(ind, 1, t_ncs)
            self.times.append(t_ncs)

            t_cbx = CheckBox(self)
            t_cbx.setChecked(unit['enabled'])
            t_cbx.stateChanged.connect(self._update_config)
            cbx_wrapper = QWidget()
            cbx_layout = QHBoxLayout(cbx_wrapper)
            cbx_layout.addWidget(t_cbx, 1, Qt.AlignCenter)
            cbx_layout.setContentsMargins(30, 0, 0, 0)
            cbx_wrapper.setLayout(cbx_layout)
            self.tableView.setCellWidget(ind, 2, cbx_wrapper)
            self.boxes.append(cbx_wrapper)
            self.check_boxes.append(t_cbx)

            t_cfbs = PushButton(self.tr('详细配置'), self)
            t_cfbs.clicked.connect(partial(self._update_detail, ind))
            cfbs_wrapper = QWidget()
            cfbs_layout = QHBoxLayout()
            cfbs_layout.setContentsMargins(0, 0, 0, 0)
            cfbs_layout.addWidget(t_cfbs, 1, Qt.AlignCenter)
            cfbs_wrapper.setLayout(cfbs_layout)
            self.config_buttons.append(cfbs_wrapper)
            self.tableView.setCellWidget(ind, 3, cfbs_wrapper)

        self.enable_list = [unit['enabled'] for unit in temp]
        self.labels = [unit['event_name'] for unit in temp]
        self.next_ticks = [unit['next_tick'] for unit in temp]

    def _remove_all_cell_widgets(self):
        """Detach every cell widget and immediately destroy its C++ object.

        QTableWidget.setCellWidget(row, col, None) only *detaches* the widget
        from the cell; the widget itself is kept alive as an orphan child of
        the viewport, stays registered in qfluentwidgets' global
        ``styleSheetManager`` (a ``WeakKeyDictionary``), and gets re-styled on
        every theme change. After many sorts this leaks memory and, more
        importantly, lets stale widgets linger long enough to race with
        ``setTheme``'s ``updateStyleSheet()`` sweep and crash the app.

        ``sip.delete`` forces immediate destruction of the underlying C++
        object, which fires ``destroyed`` and deregisters the widget from the
        style sheet manager. We must do this only after dropping every Python
        reference (the helper lists) so we never leave a wrapper pointing at a
        freed C++ object.
        """
        rows = self.tableView.rowCount()
        cols = self.tableView.columnCount()
        for row in range(rows):
            for col in range(cols):
                widget = self.tableView.cellWidget(row, col)
                if widget is None:
                    continue
                self.tableView.setCellWidget(row, col, None)
                widget.setParent(None)
                sip.delete(widget)

    def _update_config(self):
        for i in range(len(self.enable_list)):
            dic = {
                'event_name': bt.undo(self.qLabels[i].text()),
                'next_tick': self.get_next_tick(self.times[i].text()),
                'enabled': self.check_boxes[i].isChecked()
            }
            for j in range(0, len(self._event_config)):
                if self._event_config[j]['event_name'] == dic['event_name']:
                    self._event_config[j].update(dic)
        self._save_config()

    def _update_detail(self, index):
        top_window = self.parent().parent().parent().parent().parent().parent()
        dic = {
            'event_name': self._crt_order_config[index]['event_name'],
            'priority': self._crt_order_config[index]['priority'],
            'interval': self._crt_order_config[index]['interval'],
            'daily_reset': self._crt_order_config[index]['daily_reset'],
            'disabled_time_range': self._crt_order_config[index]['disabled_time_range'],
            'pre_task': self._crt_order_config[index]['pre_task'],
            'post_task': self._crt_order_config[index]['post_task'],
        }

        all_label_list = [
            [bt.tr('ConfigTranslation', x['event_name']), x['func_name']]
            for x in self._event_config
        ]

        detailMessageBox = DetailSettingMessageBox(detail_config=dic, parent=top_window, all_label_list=all_label_list,
                                                   cs=self.config)
        if not detailMessageBox.exec_():
            return
        config = detailMessageBox.configWidget.config
        for j in range(0, len(self._event_config)):
            if self._event_config[j]['event_name'] == dic['event_name']:
                self._event_config[j].update(config)
                break

        # Update Current Order Config
        for j in range(0, len(self._crt_order_config)):
            if self._crt_order_config[j]['event_name'] == dic['event_name']:
                self._crt_order_config[j].update(config)
                break
        self._save_config()

    def _refresh(self):
        t = time.time()
        for i in range(len(self.enable_list)):
            self.times[i].blockSignals(True)
            self.times[i].setText(str(datetime.fromtimestamp(t)).split('.')[0])
            self.times[i].blockSignals(False)
            self._event_config[i]['next_tick'] = t
        self._update_config()
        self.tableView.update()

    def get_next_tick(self, time_str):
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f').timestamp()
        except Exception:
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').timestamp()
            except Exception:
                # traceback.print_exc()
                print("Time format error Or Time is not set. Use 0 as default.")
                return datetime.strptime("2021-2-4 0:0:0", '%Y-%m-%d %H:%M:%S').timestamp()

    def _refresh_time(self):
        # abstract from self._event_config
        # get name and next_tick
        self._read_config()
        changed_map = [(item['event_name'], item['next_tick']) for item in self._event_config]

        for item in changed_map:
            for i in range(len(self.qLabels)):
                if bt.undo(self.qLabels[i].text()) == item[0]:
                    self.times[i].blockSignals(True)
                    self.times[i].setText(str(datetime.fromtimestamp(item[1])))
                    self.times[i].blockSignals(False)
                    break
        self.tableView.update()

    def all_check(self):
        flag = True
        for i in range(0, len(self.enable_list)):
            if not self.check_boxes[i].isChecked():
                flag = False
                for j in range(i, len(self.enable_list)):
                    self.check_boxes[j].blockSignals(True)
                    self.check_boxes[j].setChecked(True)
                    self.check_boxes[j].blockSignals(False)
                break
        if flag:
            for i in range(len(self.enable_list)):
                self.check_boxes[i].blockSignals(True)
                self.check_boxes[i].setChecked(False)
                self.check_boxes[i].blockSignals(False)
        self._update_config()
        self.tableView.update()
