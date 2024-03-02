from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem
from qfluentwidgets import TableWidget

from .expandTemplate import TemplateLayout


def get_address_from_str(st):
    res = []
    for i in st.split('\n'):
        if i.find('\t') != -1:
            res.append(i.split('\t')[0])
    return res


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '请选择您的服务器，请慎重切换服务器，切换服务器后请重新启动脚本',
                'type': 'combo',
                'key': 'server',
                'selection': ['官服', 'B服', '国际服', '日服']
            },
            {
                'label': '请填写您的adb端口号',
                'type': 'text',
                'key': 'adbPort'
            },
            {
                'label': '检测adb地址(检测目前开启的模拟器adb地址)',
                'type': 'button',
                'selection': self.detect_adb_addr,
            }
        ]
        super().__init__(parent=parent, configItems=configItems, config=config)

        self.tableView = TableWidget(self)
        self.tableView.setFixedHeight(100)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vBoxLayout.addWidget(self.tableView)
        self.tableView.setWordWrap(False)
        self.tableView.setColumnCount(1)
        self.tableView.setHorizontalHeaderLabels([self.tr('ADB地址(点击选择)')])

    def detect_adb_addr(self):
        import threading
        t = threading.Thread(target=self.detect_adb_addr_thread)
        t.start()

    def detect_adb_addr_thread(self):
        try:
            # command = ["adb", "devices"]
            # target_directory = "env/Lib/site-packages/adbutils/binaries"
            # results = get_address_from_str(subprocess.run(command, cwd=target_directory, check=True, capture_output=True, text=True).stdout)
            import device_operation
            results = device_operation.autosearch()
            if len(results) == 0:
                results = ["自动查询模拟器失败！请尝试手动输入端口"]
            self.tableView.setRowCount(len(results))
            for i in range(len(results)):
                self.tableView.setItem(i, 0, QTableWidgetItem(results[i]))
            self.tableView.itemClicked.connect(self._commit_port_change)
        except Exception as e:
            print(e)
            self.tableView.setRowCount(1)
            self.tableView.setItem(0, 0, QTableWidgetItem("adb地址获取失败"))
        # import device_operation
        # results = device_operation.autosearch()

    def _commit_port_change(self, x):
        addr = x.text()
        if addr.find(':') != -1:
            port = x.text().split(':')[1]
            self.patch_signal.emit(port)
            self.config.set('adbPort', port)
