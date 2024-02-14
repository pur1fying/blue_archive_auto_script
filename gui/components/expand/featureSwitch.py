import json

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QHeaderView, QVBoxLayout
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
        self.boxes, self.qLabels, self.times = [], [], []
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
            t_ncs.setText(str(self.next_ticks[i]))
            # TODO: 这里需要设置一个信号槽，当文本框内容改变时，更新配置文件
            # t_ncs.textChanged.connect(lambda x, index=i: self._event_config[index].update({'next_tick': x}))
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.times.append(t_ncs)
            self.qLabels.append(t_ccs)
            self.boxes.append(cbx_wrapper)

        self.vBox = QVBoxLayout(self)
        self.option_layout = QHBoxLayout(self)
        label_1 = QLabel('全选/全不选', self)
        self.all_check_box = CheckBox(self)
        # TODO: 这里写全选/全不选的信号槽
        # self.all_check_box.stateChanged.connect(self.all_check)
        self.option_layout.addWidget(label_1)
        self.option_layout.addWidget(self.all_check_box)
        self.option_layout.addStretch(1)

        self.op_2 = PushButton('刷新执行时间', self)
        self.option_layout.addWidget(self.op_2)
        # TODO: 这里写按刷新事件信号槽
        # self.op_2.clicked.connect(self._refresh)
        # 插空
        self.option_layout.addStretch(1)
        self.label_3 = QLabel('排序方式：', self)
        self.op_3 = ComboBox(self)
        self.op_3.addItems(['默认排序', '按下次执行时间排序'])
        # TODO: 这里写排序方式信号槽
        # self.op_3.currentIndexChanged.connect(self._sort)
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

    def alter_status(self, index):
        self.boxes[index].setChecked(self.boxes[index].isChecked())
        self._read_config()
        for i in range(len(self.enable_list)):
            self._event_config[i]['enabled'] = self.boxes[i].isChecked()
        self._save_config()

    def _read_config(self):
        with open('./config/' + self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
            self._event_config = json.load(f)

    def _save_config(self):
        with open('./config/' + self.config.config_dir + '/event.json', 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)

    def __accept(self, input_content=None):
        self.config.set('ShopRefreshTime', self.input.text())
