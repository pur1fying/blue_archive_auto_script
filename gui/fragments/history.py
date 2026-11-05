from random import random
import threading
import time
import traceback
from datetime import datetime
from hashlib import md5

from PyQt5.QtWidgets import QAbstractItemView, QTableWidgetItem, QHeaderView
from qfluentwidgets import TableWidget

from gui.util.customized_ui import PureWindow

def read_history_entries(repo_path):
    """Read local history through pygit2, including merge commits."""
    import pygit2

    repo = pygit2.Repository(str(repo_path))
    try:
        if repo.head_is_unborn:
            return []
        return [{
            'id': str(commit.id)[:6],
            'author': commit.author.name.strip(),
            'date': datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S"),
            'message': commit.message.strip(),
        } for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TIME)]
    finally:
        repo.free()


class HistoryWindow(PureWindow):
    def __init__(self):
        super().__init__()
        self.table_view = TableWidget(self)
        self.table_view.setColumnCount(4)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        # Enable column resizing
        self.table_view.setColumnWidth(0, 100)  # Fixed width for '内容'
        self.table_view.setColumnWidth(1, 150)  # Fixed width for '贡献者'
        self.table_view.setColumnWidth(2, 160)  # Fixed width for '提交时间'
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        # hide index column
        self.table_view.verticalHeader().setVisible(False)

        self.table_view.setHorizontalHeaderLabels(
            [self.tr('内容'), self.tr('贡献者'), self.tr('提交时间'), self.tr('提交信息')])

        threading.Thread(target=self.fetch_update_info, daemon=True).start()
        self.setWidget(self.table_view)

        # Set object name for CSS styling
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f'{self.object_name}.HistoryWindow')
        self.table_view.setObjectName(f"{self.object_name}.HistoryTable")

    def fetch_update_info(self):
        repo_path = '.'  # 仓库路径，可根据需要修改
        try:
            self.log_entries = read_history_entries(repo_path)

            self.table_view.setRowCount(len(self.log_entries))
            for i, entry in enumerate(self.log_entries):
                self.table_view.setItem(i, 0, QTableWidgetItem(entry['id']))
                self.table_view.setItem(i, 1, QTableWidgetItem(entry['author']))
                self.table_view.setItem(i, 2, QTableWidgetItem(entry['date']))
                self.table_view.setItem(i, 3, QTableWidgetItem(entry['message']))

        except Exception:
            traceback.print_exc()
