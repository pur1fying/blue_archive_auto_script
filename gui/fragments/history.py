import random
import subprocess
import threading
from datetime import datetime
import platform

from PyQt5.QtWidgets import QAbstractItemView, QTableWidgetItem
from qfluentwidgets import FluentWindow, TableWidget, FluentIcon as FIF


class HistoryWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName('HistoryWindow' + random.randint(0, 100000).__str__())
        self.table_view = TableWidget(self)
        self.table_view.setColumnCount(4)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setColumnWidth(0, 80)
        self.table_view.setColumnWidth(2, 160)
        self.table_view.horizontalHeader().setSectionResizeMode(3, 1)
        # hide index column
        self.table_view.verticalHeader().setVisible(False)

        self.table_view.setHorizontalHeaderLabels([self.tr('内容'), self.tr('贡献者'), self.tr('提交时间'), self.tr('提交信息')])

        self.table_view.setObjectName('HistoryTable' + random.randint(0, 100000).__str__())
        threading.Thread(target=self.fetch_update_info, daemon=True).start()
        self.addSubInterface(icon=FIF.CARE_RIGHT_SOLID, interface=self.table_view, text=self.tr('更新日志'))

        self.show()

    def fetch_update_info(self):
        if platform.system() == "Windows":
            GIT_HOME = './toolkit/Git/bin/git.exe'
        elif platform.system() == 'Linux':
            GIT_HOME = subprocess.run(['which', 'git'], capture_output=True, text=True, encoding='utf-8').stdout.split('\n')[0]

        # 获取提交日志
        result = subprocess.run([GIT_HOME, 'log', '--date', 'unix'], capture_output=True, text=True, encoding='utf-8')
        output = result.stdout
        # print(output)
        # 解析提交日志
        self.log_entries = []
        current_entry = {}
        for line in output.split('\n'):
            if line.startswith('commit'):
                if current_entry:
                    self.log_entries.append(current_entry)
                current_entry = {'id': line.split()[1][0:6]}
            elif line.startswith('Author:'):
                _author = line.split(':')[1].strip()
                _author = _author.split('<')[0].strip()
                current_entry['author'] = _author
            elif line.startswith('Date:'):
                _date = line.split(': ')[1].strip()
                _date = datetime.fromtimestamp(int(_date)).strftime("%Y-%m-%d %H:%M:%S")
                current_entry['date'] = _date
            elif line.startswith('    '):
                if 'message' in current_entry:
                    current_entry['message'] += line.strip()
                else:
                    current_entry['message'] = line.strip()

        if current_entry:
            self.log_entries.append(current_entry)

        self.table_view.setRowCount(len(self.log_entries))
        for i, entry in enumerate(self.log_entries):
            self.table_view.setItem(i, 0, QTableWidgetItem(entry['id']))
            self.table_view.setItem(i, 1, QTableWidgetItem(entry['author']))
            self.table_view.setItem(i, 2, QTableWidgetItem(entry['date']))
            self.table_view.setItem(i, 3, QTableWidgetItem(entry['message']))
