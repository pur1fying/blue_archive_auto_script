import json
import time
from copy import deepcopy
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QHeaderView, QVBoxLayout, QPushButton
from qfluentwidgets import CheckBox, TableWidget, LineEdit, PushButton, ComboBox


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self._event_config = None
        self._read_config()
        assert self._event_config is not None
        self.enable_list = [item['enabled'] for item in self._event_config]
        self.labels = [item['event_name'] for item in self._event_config]
        self.next_ticks = [item['next_tick'] for item in self._event_config]

        self.setFixedHeight(250)
        self.boxes, self.qLabels, self.times, self.check_boxes = [], [], [], []
        for i in range(len(self.enable_list)):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.enable_list[i])
            cbx_wrapper = QWidget()
            cbx_layout = QHBoxLayout(cbx_wrapper)
            cbx_layout.addWidget(t_cbx, 1, Qt.AlignCenter)
            cbx_layout.setContentsMargins(30, 0, 0, 0)
            cbx_wrapper.setLayout(cbx_layout)
            t_ccs = QLabel(self.labels[i])
            t_ncs = LineEdit(self)
            t_ncs.setText(str(datetime.fromtimestamp(self.next_ticks[i])))

            t_ncs.textChanged.connect(self._update_config)
            t_cbx.stateChanged.connect(self._update_config)
            self.times.append(t_ncs)
            self.qLabels.append(t_ccs)
            self.boxes.append(cbx_wrapper)
            self.check_boxes.append(t_cbx)

        self.vBox = QVBoxLayout(self)
        self.option_layout = QHBoxLayout(self)
        self.all_check_box = QPushButton('全部(不)启用', self)

        self.all_check_box.clicked.connect(self.all_check)
        self.option_layout.addWidget(self.all_check_box)
        self.option_layout.addStretch(1)

        self.op_2 = PushButton('刷新执行时间', self)
        self.option_layout.addWidget(self.op_2)
        self.op_2.clicked.connect(self._refresh)

        self.option_layout.addStretch(1)
        self.label_3 = QLabel('排序方式：', self)
        self.op_3 = ComboBox(self)
        self.op_3.addItems(['默认排序', '按下次执行时间排序'])

        self.op_3.currentIndexChanged.connect(self._sort)
        self.option_layout.addWidget(self.label_3)
        self.option_layout.addWidget(self.op_3)

        self.tableView = TableWidget(self)
        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(len(self.qLabels))
        self.tableView.setColumnCount(3)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setHorizontalHeaderLabels(['事件', '下次刷新时间', '启用'])
        self.tableView.setColumnWidth(0, 200)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.setColumnWidth(2, 50)
        for i in range(len(self.enable_list)):
            self.tableView.setCellWidget(i, 0, self.qLabels[i])
            self.tableView.setCellWidget(i, 1, self.times[i])
            self.tableView.setCellWidget(i, 2, self.boxes[i])
        self.vBox.addLayout(self.option_layout)
        self.vBox.addWidget(self.tableView)


    def _read_config(self):
        with open('./config/' + self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
            self._event_config = json.load(f)

    def _save_config(self):
        with open('./config/' + self.config.config_dir + '/event.json', 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)

    def __accept(self, input_content=None):
        self.config.set('ShopRefreshTime', self.input.text())

    def _sort(self):
        temp = deepcopy(self._event_config)
        self.tableView.clearContents()
        temp.sort(key=lambda x: x['priority'])
        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(len(self.qLabels))
        self.tableView.setColumnCount(3)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setHorizontalHeaderLabels(['事件', '下次刷新时间', '启用'])
        self.tableView.setColumnWidth(0, 200)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.setColumnWidth(2, 50)
        if self.op_3.currentIndex() == 0:
            for i in range(0, len(self._event_config)):
                for j in range(0, len(self._event_config)):
                    if self.qLabels[j].text() == temp[i]['event_name']:
                        self.tableView.setCellWidget(i, 0, self.qLabels[j])
                        self.tableView.setCellWidget(i, 1, self.times[j])
                        self.tableView.setCellWidget(i, 2, self.boxes[j])
                        break
        elif self.op_3.currentIndex() == 1:
            cnt = 0
            temp.sort(key=lambda x: x['next_tick'])
            end_indexes = []
            for i in range(len(self._event_config)):
                for j in range(len(self._event_config)):
                    if self.qLabels[j].text() == temp[i]['event_name']: # 未启用的事件记录位置
                        if not self.check_boxes[j].isChecked():
                            end_indexes.append(j)
                        else:
                            self.tableView.setCellWidget(cnt, 0, self.qLabels[j])
                            self.tableView.setCellWidget(cnt, 1, self.times[j])
                            self.tableView.setCellWidget(cnt, 2, self.boxes[j])
                            cnt += 1
                        break
            for i in end_indexes:
                self.tableView.setCellWidget(cnt, 0, self.qLabels[i])
                self.tableView.setCellWidget(cnt, 1, self.times[i])
                self.tableView.setCellWidget(cnt, 2, self.boxes[i])
                cnt += 1
        self.tableView = self.tableView
        self.tableView.update()

    def _update_config(self):
        for i in range(len(self.enable_list)):
            dic = {
                'event_name': self.qLabels[i].text(),
                'next_tick': self.get_next_tick(self.times[i].text()),
                'enabled': self.check_boxes[i].isChecked()
            }
            for j in range(0, len(self._event_config)):
                if self._event_config[j]['event_name'] == dic['event_name']:
                    self._event_config[j].update(dic)
        self._save_config()

    def _refresh(self):
        t = time.time()
        for i in range(len(self.enable_list)):
            self.times[i].blockSignals(True)
            self.times[i].setText(str(datetime.fromtimestamp(t)))
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
            except Exception as e:
                print(e)
                return 0

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
