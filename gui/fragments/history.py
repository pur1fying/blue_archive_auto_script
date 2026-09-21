from random import random
import shutil
import subprocess
import threading
import time
import traceback
from datetime import datetime
from hashlib import md5

from PyQt5.QtWidgets import QAbstractItemView, QTableWidgetItem, QHeaderView
from qfluentwidgets import TableWidget

from gui.util.customized_ui import PureWindow

NONINTERACTIVE_GIT_CONFIG = [
    "-c", "credential.helper=",
    "-c", "credential.interactive=never",
    "-c", "core.askPass=echo",
    "-c", "core.sshCommand=ssh -o BatchMode=yes",
]


def _noninteractive_git_env():
    """Return a Git environment that prevents GUI credential prompts."""
    import os

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    env["GCM_MODAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    env["SSH_ASKPASS"] = "echo"
    return env


def _read_history_with_git(repo_path):
    """Read commit history with the system git executable."""
    git_executable = shutil.which("git")
    if not git_executable:
        raise FileNotFoundError("System git not found")
    result = subprocess.run(
        [
            git_executable,
            *NONINTERACTIVE_GIT_CONFIG,
            "log",
            "--date=format:%Y-%m-%d %H:%M:%S",
            "--pretty=format:%h%x1f%an%x1f%ad%x1f%s%x1e",
        ],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
        env=_noninteractive_git_env(),
    )
    entries = []
    for raw_entry in result.stdout.split("\x1e"):
        raw_entry = raw_entry.strip()
        if not raw_entry:
            continue
        commit_id, author, commit_time, message = raw_entry.split("\x1f", 3)
        entries.append({
            'id': commit_id,
            'author': author.strip(),
            'date': commit_time,
            'message': message.strip(),
        })
    return entries


def _read_history_with_pygit2(repo_path):
    """Read commit history with pygit2 when system git is unavailable."""
    import pygit2

    repo = pygit2.Repository(repo_path)
    entries = []
    for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TIME):
        entries.append({
            'id': str(commit.id)[:6],
            'author': commit.author.name.strip(),
            'date': datetime.fromtimestamp(commit.commit_time).strftime("%Y-%m-%d %H:%M:%S"),
            'message': commit.message.strip(),
        })
    return entries


def read_history_entries(repo_path):
    """Read local commit history using system git first and pygit2 as fallback."""
    try:
        return _read_history_with_git(repo_path)
    except Exception:
        return _read_history_with_pygit2(repo_path)


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
