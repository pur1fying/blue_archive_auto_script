import cv2
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem
from qfluentwidgets import TableWidget

from .expandTemplate import TemplateLayout
from ...util.common_methods import get_context_thread


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
                'label': '常用端口号一览，请根据你的模拟器设置端口，多开请自行查询。',
                'type': 'label'
            },
            {
                'label': 'MuMu：7555；蓝叠/雷电：5555；夜神：62001或59865；',
                'type': 'label'
            },
            {
                'label': 'Mumu12：16384；逍遥：21503；',
                'type': 'label'
            },
            {
                'label': '截图测试',
                'type': 'button',
                'selection': self.screenshot
            },
            {
                'label': '请填写您的adb端口号',
                'type': 'text',
                'key': 'adbPort'
            },
            {
                'label': '检测adb地址',
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
        self.tableView.setHorizontalHeaderLabels([self.tr('ADB地址')])

    def detect_adb_addr(self):
        import device_operation
        results = device_operation.autosearch()
        self.tableView.setRowCount(len(results))
        for i in range(len(results)):
            self.tableView.setItem(i, 0, QTableWidgetItem(results[i]))

    def screenshot(self):
        test_img = get_context_thread(self).get_screen()
        cv2.imshow('Test Screenshot', test_img)
        cv2.waitKey(-1)
