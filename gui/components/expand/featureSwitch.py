import json

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from qfluentwidgets import FlowLayout, CheckBox


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self._event_config = None
        self._read_config()
        assert self._event_config is not None
        self.enable_list = [item['enabled'] for item in self._event_config]
        self.labels = [item['event_name'] for item in self._event_config]

        # self.goods = self.config.get(key='CommonShopList')

        layout = FlowLayout(self, needAni=True)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setVerticalSpacing(0)
        # layout.setHorizontalSpacing(10)

        self.setFixedHeight(200)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')
        self.boxes = []
        for i in range(len(self.enable_list)):
            t_cbx = CheckBox(self)
            t_cbx.setChecked(self.enable_list[i])
            ccs = QLabel(self.labels[i])
            ccs.setFixedWidth(100)
            wrapper_widget = QWidget()
            wrapper = QHBoxLayout()
            wrapper.addWidget(ccs)
            wrapper.addWidget(t_cbx)
            wrapper_widget.setLayout(wrapper)
            layout.addWidget(wrapper_widget)
            t_cbx.stateChanged.connect(lambda x, index=i: self.alter_status(index))
            self.boxes.append(t_cbx)

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
