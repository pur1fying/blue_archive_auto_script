import json
import time
from copy import deepcopy
from datetime import datetime
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHeaderView, QVBoxLayout
from qfluentwidgets import CheckBox, TableWidget, PushButton, ComboBox, CaptionLabel, MessageBoxBase, \
    SubtitleLabel

from gui.components.expand.expandTemplate import TemplateLayoutV2
from gui.util.customed_ui import ClickFocusLineEdit
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
        self.label_3 = CaptionLabel(self.tr('排序方式：'), self)
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
            t_ccs = CaptionLabel(bt.tr('ConfigTranslation', self.labels[i]), self)
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
        # clear original components
        self.qLabels, self.times, self.check_boxes = [], [], []
        self.tableView.clearContents()
        self.vBox.removeWidget(self.tableView)
        self.tableView.deleteLater()
        # recreate table
        self.tableView = TableWidget(self)
        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(len(temp))
        self.tableView.setColumnCount(4)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setHorizontalHeaderLabels(
            [self.tr('事件'), self.tr('下次刷新时间'), self.tr('启用'), self.tr('更多配置')])

        # mode 0: default, mode 1: by next_tick
        if self.op_3.currentIndex() == 0:
            temp.sort(key=lambda x: x['priority'])
        elif self.op_3.currentIndex() == 1:
            temp.sort(key=lambda x: (not x['enabled'], x['next_tick']))
        self._crt_order_config = temp
        # Add components to table
        for ind, unit in enumerate(temp):
            t_ccs = CaptionLabel(bt.tr('ConfigTranslation', unit['event_name']))
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

        # Add table to layout
        self.vBox.addWidget(self.tableView)

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
