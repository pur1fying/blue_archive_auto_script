import json

from PyQt5.QtWidgets import QWidget, QLabel
from qfluentwidgets import FlowLayout, CheckBox

from core import EVENT_CONFIG_PATH
from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._event_config = None
        self._read_config()
        assert self._event_config is not None
        self.enable_list = [item['enabled'] for item in self._event_config]
        self.labels = [item['event_name'] for item in self._event_config]

        # self.setFixedHeight(120)

        # self.goods = self.get(key='CommonShopList')

        layout = FlowLayout(self, needAni=True)
        layout.setContentsMargins(30, 30, 30, 30)
        # layout.setVerticalSpacing(20)
        # layout.setHorizontalSpacing(10)

        self.setFixedHeight(200)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')
        self.boxes = []
        for i in range(len(self.enable_list)):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.enable_list[i])
            ccs = QLabel(self.labels[i])
            ccs.setFixedWidth(100)
            layout.addWidget(ccs)
            layout.addWidget(t_cbx)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.boxes.append(t_cbx)

    def alter_status(self, index):
        self.boxes[index].setChecked(self.boxes[index].isChecked())
        self._read_config()
        for i in range(len(self.enable_list)):
            self._event_config[i]['enabled'] = self.boxes[i].isChecked()
        self._save_config()

    def _read_config(self):
        with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self._event_config = json.load(f)

    def _save_config(self):
        with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)

    def __accept(self, input_content=None):
        self.set('ShopRefreshTime', self.input.text())
