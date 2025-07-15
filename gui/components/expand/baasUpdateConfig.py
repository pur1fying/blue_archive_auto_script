import time
import json
import binascii

import dulwich
import requests
import threading
from dulwich.client import get_transport_and_path
from dulwich.errors import NotGitRepository, HangupException
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from qfluentwidgets import TableWidget, ComboBox, PrimaryPushButton
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QWidget, QLabel, QVBoxLayout, QHBoxLayout

from deploy.installer.const import GetShaMethod, get_remote_sha_methods
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater
from gui.util.notification import success

class TestGetRemoteShaMethodWorker(QThread):
    test_completed = pyqtSignal(dict, bool, str, float)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.method = config["method"]

    def run(self):
        _t_start = time.time()
        if self.method == GetShaMethod.GITHUB_API:
            success, sha_value = self.github_api_get_latest_sha(self.config)
        elif self.method == GetShaMethod.MIRRORC_API:
            success, sha_value = self.mirrorc_api_get_latest_sha()
        elif self.method == GetShaMethod.PYGIT2:
            success, sha_value = self.dulwich_get_latest_sha(self.config)
        else:
            success = False
            sha_value = "未知方法"
        _t_end = time.time()

        self.test_completed.emit(self.config, success, sha_value, _t_end - _t_start)

    @staticmethod
    def github_api_get_latest_sha(data):
        owner = data["owner"]
        repo = data["repo"]
        branch = data["branch"]
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
        try:
            response = requests.get(url, timeout=3.0)
            if response.status_code != 200:
                return False, f"Request failed with status code {response.status_code}"
            response_json = response.json()
            return True, response_json.get("commit", {}).get("sha")
        except requests.RequestException as e:
            return False, str(e)

    @staticmethod
    def mirrorc_api_get_latest_sha():
        mirrorc_inst = MirrorC_Updater(app="BAAS_repo", current_version="")
        try:
            ret = mirrorc_inst.get_latest_version(cdk="")
            if ret.has_data:
                return True, ret.latest_version_name
            else:
                return False, ret.message
        except Exception as e:
            return False, str(e)

    @staticmethod
    def dulwich_get_latest_sha(data):
        url = data["url"]
        branch = data["branch"]
        target_ref = f"refs/heads/{branch}"

        try:
            remote_refs = dulwich.porcelain.ls_remote(url)
            for ref_name, sha in remote_refs.items():
                decoded_ref = ref_name.decode("utf-8")
                if decoded_ref == target_ref:
                    if len(sha) == 20:
                        return True, binascii.hexlify(sha).decode("utf-8")
                    try:
                        hex_str = sha.decode("utf-8")
                        if len(hex_str) == 40:
                            return True, hex_str
                    except:
                        pass
                    return True, binascii.hexlify(sha[:20]).decode("utf-8")
            ref = f"refs/heads/{branch}",
            sha = remote_refs[ref.encode("utf-8")]
            return True, binascii.hexlify(sha[:20]).decode("utf-8")
        except Exception as e:
            return False, str(e)


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        BAASUpdateConfig = QObject()
        super().__init__(parent=parent)
        self.config = config
        self.vBoxLayout = QVBoxLayout(self)
        self.get_remote_sha_method = self.config.get("General.get_remote_sha_method", None)
        if self.get_remote_sha_method is not None:
            self._get_remote_sha_method_hBoxLayout = QHBoxLayout()
            self._init_get_remote_sha_method_ComboBox()
            self._initialize_test_table()

            self._get_remote_sha_method_hBoxLayout.addWidget(self._get_remote_sha_method_label)
            self._get_remote_sha_method_hBoxLayout.addWidget(self.get_remote_sha_method_ComboBox)
            self._get_remote_sha_method_hBoxLayout.addWidget(self._test_get_remote_sha_method_push_button)
            self.vBoxLayout.addLayout(self._get_remote_sha_method_hBoxLayout)
            self.vBoxLayout.addWidget(self.test_result_table)
            self.vBoxLayout.addWidget(self.status_label)
        

    def _initialize_test_table(self):
        self._test_get_remote_sha_method_push_button = PrimaryPushButton(self)
        self._test_get_remote_sha_method_push_button.setText(self.tr("测试所有方法"))
        self._test_get_remote_sha_method_push_button.setFixedWidth(130)
        self._test_get_remote_sha_method_push_button.clicked.connect(self._test_all_get_remote_sha_method)
        self.test_result_table = TableWidget(self)
        self.test_result_table.setColumnCount(4)
        self.test_result_table.setHorizontalHeaderLabels([
            self.tr("方法"),
            self.tr("状态"),
            self.tr("耗时(秒)"),
            self.tr("获取的SHA值")
        ])

        header = self.test_result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.test_result_table.verticalHeader().setDefaultSectionSize(30)
        row_count = len(get_remote_sha_methods)
        self.test_result_table.setRowCount(row_count)
        table_height = min(400, row_count * 35)
        self.test_result_table.setFixedHeight(table_height)
        for i, config in enumerate(get_remote_sha_methods):
            method_item = QTableWidgetItem(self.get_remote_sha_method_display_names[i])
            method_item.setFlags(Qt.ItemIsEnabled)

            status_item = QTableWidgetItem(self.tr("等待测试"))
            status_item.setFlags(Qt.ItemIsEnabled)
            status_item.setForeground(QColor("yellow"))

            time_item = QTableWidgetItem("")
            time_item.setFlags(Qt.ItemIsEnabled)

            sha_item = QTableWidgetItem("")
            sha_item.setFlags(Qt.ItemIsEnabled)

            self.test_result_table.setItem(i, 0, method_item)
            self.test_result_table.setItem(i, 1, status_item)
            self.test_result_table.setItem(i, 2, time_item)
            self.test_result_table.setItem(i, 3, sha_item)

            self.test_result_table.item(i, 0).setData(Qt.UserRole, config)
        self.status_label = QLabel(self.tr("等待测试..."))

    def _test_all_get_remote_sha_method(self):
        self._test_get_remote_sha_method_push_button.setEnabled(False)
        self.status_label.setText(self.tr("测试进行中..."))

        for row in range(self.test_result_table.rowCount()):
            self.test_result_table.item(row, 1).setText(self.tr("测试中..."))
            self.test_result_table.item(row, 1).setForeground(QColor("blue"))
            self.test_result_table.item(row, 2).setText("")
            self.test_result_table.item(row, 3).setText("")

        self.workers = []
        self.completed_count = 0
        for row in range(self.test_result_table.rowCount()):
            config = self.test_result_table.item(row, 0).data(Qt.UserRole)
            worker = TestGetRemoteShaMethodWorker(config)
            worker.test_completed.connect(self._update_test_result)
            worker.start()
            self.workers.append(worker)

    def _update_test_result(self, config, success, sha_value, elapsed_time):
        for row in range(self.test_result_table.rowCount()):
            table_config = self.test_result_table.item(row, 0).data(Qt.UserRole)
            if table_config == config:
                status_item = self.test_result_table.item(row, 1)
                if success:
                    status_item.setText(self.tr("成功"))
                    status_item.setForeground(QColor("green"))
                else:
                    status_item.setText(self.tr("失败"))
                    status_item.setForeground(QColor("red"))

                time_item = self.test_result_table.item(row, 2)
                time_item.setText(f"{elapsed_time:.3f}")  # 显示3位小数

                sha_item = self.test_result_table.item(row, 3)
                sha_item.setText(sha_value)

                self.completed_count += 1
                self.status_label.setText(
                    self.tr("测试进度") + f":{self.completed_count}/{self.test_result_table.rowCount()}"
                )

                self._check_all_tests_completed()
                break

    def _check_all_tests_completed(self):
        if self.completed_count < self.test_result_table.rowCount():
            return

        self._test_get_remote_sha_method_push_button.setEnabled(True)
        self.status_label.setText(self.tr("所有测试已完成"))

        success(
            self.tr("测试完成"),
            self.tr("所有远程SHA获取方法测试已完成"),
            self.config,
            duration=2000
        )

    def _init_get_remote_sha_method_ComboBox(self):
        self._get_remote_sha_method_label = QLabel(self)
        self._get_remote_sha_method_label.setText(self.tr("获取远程sha码的方法(用于检查是否有更新)"))
        self.get_remote_sha_method_origin_names = [item["name"] for item in get_remote_sha_methods]
        self.get_remote_sha_method_display_names = [
            self.tr("github API"),
            self.tr("Mirror酱免费API"),
            self.tr("gitee远程仓库读取"),
            self.tr("gitcode远程仓库读取"),
            self.tr("腾讯云远程仓库读取")
        ]

        self.get_remote_sha_method_ComboBox = ComboBox()
        self.get_remote_sha_method_ComboBox.setFixedWidth(200)
        matched_index = None
        if self.get_remote_sha_method in self.get_remote_sha_method_origin_names:
            matched_index = self.get_remote_sha_method_origin_names.index(self.get_remote_sha_method)

        if matched_index is None:
            self.get_remote_sha_method_origin_names.insert(0, "")
            self.get_remote_sha_method_display_names.insert(0, self.tr("暂无"))
            matched_index = 0

        for display_name in self.get_remote_sha_method_display_names:
            self.get_remote_sha_method_ComboBox.addItem(display_name, None)

        self.get_remote_sha_method_ComboBox.setCurrentIndex(matched_index)

        def on_method_changed(index):
            selected_method = self.get_remote_sha_method_origin_names[index]
            if selected_method == "":
                return
            else:
                self.__set_config_and_display_message("General.get_remote_sha_method", selected_method)

        self.get_remote_sha_method_ComboBox.currentIndexChanged.connect(on_method_changed)


    def __set_config_and_display_message(self, key, value):
        self.config.set_and_save(key, value)
        success(
            self.tr("设置保存成功"),
            self.tr(f"已将 '{key}' 设置为 '{value}'"),
            self.config,
            duration=2000
        )
