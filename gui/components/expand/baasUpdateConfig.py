import time
import binascii
import threading

import dulwich
import requests
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from qfluentwidgets import TableWidget, ComboBox, PrimaryPushButton, TextEdit, PushButton
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QWidget, QLabel, QVBoxLayout, QHBoxLayout

from core.utils import delay
from gui.util.notification import success, error
from deploy.installer.mirrorc_update.const import MirrorCErrorCode
from deploy.installer.const import GetShaMethod, get_remote_sha_methods
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater, RequestReturn


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
            sha_value = self.tr("未知方法")
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


class MirrorCCDKTestThread(QThread):
    finished = pyqtSignal(RequestReturn, bool)

    def __init__(self, layout, cdk, save=False, parent=None):
        super().__init__(parent)
        self.layout = layout
        self.cdk = cdk
        self.save = save
        self.is_finished = False
        self.req_ret = None

    def run(self):
        try:
            self.req_ret = self.layout._mirrorc_inst.get_latest_version(cdk=self.cdk, timeout=3.0)
            self.finished.emit(self.req_ret, self.save)
        except Exception as e:
            error("CDK" + self.tr("测试错误"), str(e), self.layout.config)
        self.is_finished = True

class Layout(QWidget):

    def __init__(self, parent=None, config=None):
        BAASUpdateConfig = QObject()
        super().__init__(parent=parent)
        self.config = config
        self.REPO_URL_NAME_mapping = {
            "https://github.com/pur1fying/blue_archive_auto_script.git": self.tr("github远程仓库"),
            "https://gitee.com/pur1fy/blue_archive_auto_script.git": self.tr("gitee远程仓库"),
            "https://gitcode.com/m0_74686738/blue_archive_auto_script.git": self.tr("gitcode远程仓库"),
            "https://e.coding.net/g-jbio0266/baas/blue_archive_auto_script.git": self.tr("腾讯云远程仓库")
        }
        self._revert_REPO_URL_NAME_mapping = {v: k for k, v in self.REPO_URL_NAME_mapping.items()}
        self.REPO_URL_CHECK_UPDATE_METHOD_mapping = {
            "https://github.com/pur1fying/blue_archive_auto_script.git": "github",
            "https://gitee.com/pur1fy/blue_archive_auto_script.git": "gitee",
            "https://gitcode.com/m0_74686738/blue_archive_auto_script.git": "gitcode",
            "https://e.coding.net/g-jbio0266/baas/blue_archive_auto_script.git": "tencent_c_coding"
        }

        self._vBoxLayout = QVBoxLayout(self)

        self._repo = None
        self._init_local_version_layout()
        self._init_remote_version_layout()
        self._init_current_update_method_layout()
        self._init_mirrorc_cdk_layout()
        self._init_repo_url_http_layout()
        self._init_get_remote_sha_method_layout()

        self._detect_update_method_and_update_ui()

    def _init_repo_url_http_layout(self):
        self._repo_url_http = self.config.get("URLs.REPO_URL_HTTP", None)
        self._repo_url_http_hBoxLayout = QHBoxLayout()
        self._repo_url_http_hBoxLayout.setAlignment(Qt.AlignLeft)

        self._repo_url_http_label = QLabel(self)
        self._repo_url_http_label.setText(self.tr("git更新仓库:"))
        self._repo_url_http_ComboBox = ComboBox(self)
        self._repo_url_http_ComboBox_items = list(self.REPO_URL_NAME_mapping.values())
        for item in self._repo_url_http_ComboBox_items:
            self._repo_url_http_ComboBox.addItem(item)
        if self._repo_url_http is not None and self._repo_url_http in self.REPO_URL_NAME_mapping:
            self._repo_url_http_ComboBox.setCurrentIndex(self._repo_url_http_ComboBox_items .index(self.REPO_URL_NAME_mapping[self._repo_url_http]))

        def on_repo_url_http_changed(index):
            selected_text = self._repo_url_http_ComboBox_items[index]
            if selected_text in self.REPO_URL_NAME_mapping.values():
                url = self._revert_REPO_URL_NAME_mapping.get(selected_text, "")
                if url == "":
                    return
                else:
                    self.__set_config_and_display_message("URLs.REPO_URL_HTTP", url)
            self._detect_update_method_and_update_ui()

        self._repo_url_http_ComboBox.currentIndexChanged.connect(on_repo_url_http_changed)
        self._repo_url_http_hBoxLayout.addWidget(self._repo_url_http_label)
        self._repo_url_http_hBoxLayout.addWidget(self._repo_url_http_ComboBox)
        self._vBoxLayout.addLayout(self._repo_url_http_hBoxLayout)

    def _init_get_remote_sha_method_layout(self):
        self._get_remote_sha_method = self.config.get("General.get_remote_sha_method", None)
        if self._get_remote_sha_method is not None:
            self._get_remote_sha_method_hBoxLayout = QHBoxLayout()
            self._get_remote_sha_method_hBoxLayout.setAlignment(Qt.AlignLeft)
            self._init_get_remote_sha_method_ComboBox()
            self._initialize_test_table()
            self._get_remote_sha_method_hBoxLayout.addWidget(self._get_remote_sha_method_label)
            self._get_remote_sha_method_hBoxLayout.addWidget(self.get_remote_sha_method_ComboBox)
            self._get_remote_sha_method_hBoxLayout.addWidget(self._test_get_remote_sha_method_push_button)
            self._vBoxLayout.addLayout(self._get_remote_sha_method_hBoxLayout)
            self._vBoxLayout.addWidget(self.test_result_table)
            self._vBoxLayout.addWidget(self.status_label)

    def _init_remote_version_layout(self):
        self._BAAS_remote_version_hBoxLayout = QHBoxLayout()
        self._BAAS_remote_version_hBoxLayout.setAlignment(Qt.AlignLeft)
        self._BAAS_remote_version_desc_label = QLabel(self)
        self._BAAS_remote_version_desc_label.setText(self.tr("远程BAAS版本:"))
        self._BAAS_remote_version_label = QLabel(self)
        self._BAAS_remote_version_get_method_label = QLabel(self)
        self._BAAS_remote_version_sha = ""
        self._BAAS_remote_version_get_method = ""

        self._BAAS_remote_version_hBoxLayout.addWidget(self._BAAS_remote_version_desc_label)
        self._BAAS_remote_version_hBoxLayout.addWidget(self._BAAS_remote_version_label)
        self._BAAS_remote_version_hBoxLayout.addWidget(self._BAAS_remote_version_get_method_label)
        self._vBoxLayout.addLayout(self._BAAS_remote_version_hBoxLayout)


    def _init_local_version_layout(self):
        self._BAAS_local_version_hBoxLayout = QHBoxLayout()
        self._BAAS_local_version_hBoxLayout.setAlignment(Qt.AlignLeft)
        self._BAAS_local_version_desc_label = QLabel(self)
        self._BAAS_local_version_desc_label.setText(self.tr("本地BAAS版本:"))
        self._BAAS_local_version_label = QLabel(self)
        self._BAAS_local_version_get_method_label = QLabel(self)
        self._BAAS_local_version_state = QLabel(self)
        self._BAAS_local_version_hBoxLayout.addWidget(self._BAAS_local_version_desc_label)
        self._BAAS_local_version_hBoxLayout.addWidget(self._BAAS_local_version_label)
        self._BAAS_local_version_hBoxLayout.addWidget(self._BAAS_local_version_get_method_label)
        self._BAAS_local_version_hBoxLayout.addWidget(self._BAAS_local_version_state)
        self._vBoxLayout.addLayout(self._BAAS_local_version_hBoxLayout)

        method = self._get_local_version()
        if method is None:
            self._BAAS_local_version_label.setText(self.tr("无法获取本地版本"))
            palette = self._BAAS_local_version_label.palette()
            palette.setColor(palette.WindowText, QColor("#a80000"))
            self._BAAS_local_version_label.setPalette(palette)
            self._BAAS_local_version_get_method_label.setText("")
            self._BAAS_local_version_state.setText("")
        else:
            self._BAAS_local_version_label.setText(self._BAAS_local_version_sha)
            if method == "setup.toml":
                self._BAAS_local_version_get_method_label.setText(f"({self.tr('从setup.toml读取')})")
            elif method == ".git":
                self._BAAS_local_version_get_method_label.setText(f"({self.tr('从本地git仓库读取')})")

    def _get_local_version(self):
        self._BAAS_local_version_sha = self.config.get("General.current_BAAS_version", None)
        if self._BAAS_local_version_sha is not None:
            return "setup.toml"
        try:
            self._repo = dulwich.repo.Repo(".")
            self._BAAS_local_version_sha = self._repo.head().decode("utf-8")
            return ".git"
        except:
            return None

    def _init_mirrorc_cdk_layout(self):
        self._mirrorc_cdk = self.config.get("General.mirrorc_cdk", None)
        self._mirrorc_update_available = False if self._mirrorc_cdk is None else True
        self._mirrorc_cdk_hBoxLayout = QHBoxLayout()
        self._mirrorc_cdk_hBoxLayout.setAlignment(Qt.AlignLeft)

        if self._mirrorc_update_available:
            self._setup_mirrorc_valid_layout()
        else:
            self._set_mirrorc_invalid_layout()
        self._vBoxLayout.addLayout(self._mirrorc_cdk_hBoxLayout)

    def _setup_mirrorc_valid_layout(self):
        self._cdk_test_thread = None
        self._mirrorc_cdk_is_valid = False
        self._mirrorc_inst = MirrorC_Updater(app="BAAS_repo", current_version="")

        # label TextEdit label button button
        self._mirrorc_cdk_label = QLabel(self)
        self._mirrorc_cdk_label.setText(self.tr("Mirror酱CDK"))
        self._mirrorc_cdk_TextEdit = TextEdit(self)
        self._mirrorc_cdk_TextEdit.setFixedWidth(250)
        self._mirrorc_cdk_TextEdit.setFixedHeight(35)
        if self._mirrorc_cdk == "":
            self._mirrorc_cdk_TextEdit.setPlaceholderText(self.tr("在此处填写CDK"))
        else:
            self._mirrorc_cdk_TextEdit.setText(self._mirrorc_cdk)

        self._mirrorc_cdk_state_label = QLabel(self)
        self._test_mirrorc_cdk_button = PushButton()
        self._test_mirrorc_cdk_button.setText(self.tr("测试CDK"))
        self._test_mirrorc_cdk_button.setFixedWidth(100)

        # slot
        def on_test_mirrorc_cdk_clicked():
            self._test_and_set_mirrorc_cdk_state(save=False)

        self._test_mirrorc_cdk_button.clicked.connect(on_test_mirrorc_cdk_clicked)

        if self._mirrorc_cdk != "":
            self._test_and_set_mirrorc_cdk_state(save=False)

        @delay(0.6)
        def on_cdk_text_changed():
            self._test_and_set_mirrorc_cdk_state(save=True)

        self._mirrorc_cdk_TextEdit.textChanged.connect(on_cdk_text_changed)

        # layout
        self._mirrorc_cdk_hBoxLayout.addWidget(self._mirrorc_cdk_label)
        self._mirrorc_cdk_hBoxLayout.addWidget(self._mirrorc_cdk_TextEdit)
        self._mirrorc_cdk_hBoxLayout.addWidget(self._mirrorc_cdk_state_label)
        self._mirrorc_cdk_hBoxLayout.addWidget(self._test_mirrorc_cdk_button)
        self._setup_what_is_mirrorc()

    def _setup_what_is_mirrorc(self):
        self._what_is_mirrorc_cdk_pushbutton = PushButton(self)
        self._what_is_mirrorc_cdk_pushbutton.setText(self.tr("什么是Mirror酱?"))
        self._what_is_mirrorc_cdk_pushbutton.setFixedWidth(150)
        def on_what_is_mirrorc_cdk_clicked():
            import webbrowser
            webbrowser.open("https://baas.wiki/usage_doc/install/Windows.html#mirror%E9%85%B1cdk")
        self._what_is_mirrorc_cdk_pushbutton.clicked.connect(on_what_is_mirrorc_cdk_clicked)
        self._mirrorc_cdk_hBoxLayout.addWidget(self._what_is_mirrorc_cdk_pushbutton)

    def _set_mirrorc_invalid_layout(self):
        self._mirrorc_invalid_label = QLabel(self)
        self._mirrorc_invalid_label.setText(self.tr("无法使用Mirror酱更新"))
        palette = self._mirrorc_invalid_label.palette()
        palette.setColor(palette.WindowText, QColor("#a80000"))
        self._mirrorc_invalid_label.setPalette(palette)
        self._mirrorc_invalid_update_BAAS_installer_button = PushButton(self)
        self._mirrorc_invalid_update_BAAS_installer_button.setText(self.tr("更新BAAS启动器版本 >= 1.4.0以使用Mirror酱更新"))
        def on_mirrorc_invalid_update_BAAS_installer_button_clicked():
            import webbrowser
            webbrowser.open("https://github.com/pur1fying/blue_archive_auto_script/releases")

        self._mirrorc_invalid_update_BAAS_installer_button.clicked.connect(on_mirrorc_invalid_update_BAAS_installer_button_clicked)

        self._mirrorc_cdk_hBoxLayout.addWidget(self._mirrorc_invalid_label)
        self._mirrorc_cdk_hBoxLayout.addWidget(self._mirrorc_invalid_update_BAAS_installer_button)
        self._setup_what_is_mirrorc()

    def _test_and_set_mirrorc_cdk_state(self, save=False):
        cdk = self._mirrorc_cdk_TextEdit.toPlainText().strip()
        if cdk == "":
            return
        self._update_cdk_state_label(self.tr("测试中"), "testing")
        self._cdk_test_thread = MirrorCCDKTestThread(self, cdk, save=save)
        self._cdk_test_thread.finished.connect(self._handle_cdk_test_result)
        self._cdk_test_thread.start()

    def _handle_cdk_test_result(self, request_ret, save=False):
        code = request_ret.code
        message = "CDK"
        if code == MirrorCErrorCode.SUCCESS.value:
            expire_time = request_ret.cdk_expired_time
            message += self.tr("到期时间") + time.strftime(":%Y-%m-%d %H:%M:%S", time.localtime(expire_time))
            self._update_cdk_state_label(message, "valid")
            if save:
                self.__set_config_and_display_message("General.mirrorc_cdk", self._mirrorc_cdk_TextEdit.toPlainText().strip())
        elif code == MirrorCErrorCode.KEY_EXPIRED.value:
            message += self.tr("已过期")
            self._update_cdk_state_label(message, "error")
            error(self.tr("错误"), message, self.config)
        elif code == MirrorCErrorCode.KEY_INVALID.value:
            message += self.tr("无效")
            self._update_cdk_state_label(message, "error")
            error(self.tr("错误"), message, self.config)
        elif code == MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value:
            message += self.tr("今日下载次数已用完")
            self._update_cdk_state_label(message, "error")
            error(self.tr("错误"), message, self.config)
        elif code == MirrorCErrorCode.KEY_MISMATCHED.value:
            message += self.tr("与请求资源不匹配")
            self._update_cdk_state_label(message, "error")
            error(self.tr("错误"), message, self.config)
        elif code == MirrorCErrorCode.KEY_BLOCKED.value:
            message += self.tr("已被封禁")
            self._update_cdk_state_label(message, "error")
            error(self.tr("错误"), message, self.config)

        if code == MirrorCErrorCode.SUCCESS.value:
            self._BAAS_remote_version_sha = request_ret.latest_version_name
            self._BAAS_remote_version_get_method = "mirrorc"
            self._mirrorc_cdk_is_valid = True
        else:
            self._mirrorc_cdk_is_valid = False

        if not save and self._mirrorc_cdk_is_valid:
            success(self.tr("测试完毕"), self.tr("CDK测试完毕"), self.config, 800)
        self._detect_update_method_and_update_ui()


    def _update_cdk_state_label(self, text, state):
        self._mirrorc_cdk_state_label.setText(text)
        if state == "valid":
            palette = self._mirrorc_cdk_state_label.palette()
            palette.setColor(palette.WindowText, QColor("#107c10"))
            self._mirrorc_cdk_state_label.setPalette(palette)
        elif state == "testing":
            palette = self._mirrorc_cdk_state_label.palette()
            palette.setColor(palette.WindowText, QColor("#0078d7"))
            self._mirrorc_cdk_state_label.setPalette(palette)
        elif state == "error":
            palette = self._mirrorc_cdk_state_label.palette()
            palette.setColor(palette.WindowText, QColor("#a80000"))
            self._mirrorc_cdk_state_label.setPalette(palette)
        else:
            self._mirrorc_cdk_state_label.setStyleSheet("")

    def _init_current_update_method_layout(self):
        self._current_update_method_hBoxLayout = QHBoxLayout()
        self._current_update_method_hBoxLayout.setAlignment(Qt.AlignLeft)
        self._current_update_method_desc_label = QLabel(self)
        self._current_update_method_desc_label.setText(self.tr("当前更新方法:"))
        self._current_update_method_label  = QLabel(self)
        self._current_update_method_hBoxLayout.addWidget(self._current_update_method_desc_label)
        self._current_update_method_hBoxLayout.addWidget(self._current_update_method_label)
        self._vBoxLayout.addLayout(self._current_update_method_hBoxLayout)

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
            method_item = QTableWidgetItem(self.get_remote_sha_method_display_names[i + self._table_method_display_name_offset])
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
            self.test_result_table.item(row, 1).setForeground(QColor("#0078d7"))
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
        self._table_method_display_name_offset = 0
        if self._get_remote_sha_method in self.get_remote_sha_method_origin_names:
            matched_index = self.get_remote_sha_method_origin_names.index(self._get_remote_sha_method)

        if matched_index is None:
            self._table_method_display_name_offset = 1
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

    def _detect_update_method_and_update_ui(self):
        self._current_update_method_label.setText(self.tr("读取中"))
        threading.Thread(target=self._detect_update_method_thread).start()

    def _detect_update_method_thread(self):
        self._update_method = None
        # try mirrorc detect
        if self._mirrorc_update_available and self._cdk_test_thread is not None:
            if not self._cdk_test_thread.is_finished:
                self._cdk_test_thread.wait()
            if self._cdk_test_thread.req_ret is not None:
                if self._cdk_test_thread.req_ret.code == MirrorCErrorCode.SUCCESS.value:
                    self._BAAS_remote_version_sha = self._cdk_test_thread.req_ret.latest_version_name
                    self._BAAS_remote_version_get_method = "mirrorc"
                    self._update_method = "mirrorc"

        if self._update_method is None:
            self._repo_url_http = self.config.get("URLs.REPO_URL_HTTP", None)
            if self._repo_url_http is not None and self._repo_url_http in self.REPO_URL_NAME_mapping:
                self._BAAS_remote_version_get_method = "git"
                self._update_method = "git"
                method = self.REPO_URL_CHECK_UPDATE_METHOD_mapping.get(self._repo_url_http, None)
                if method is not None:
                    for config in get_remote_sha_methods:
                        if config["name"] == method:
                            method = config["method"]
                            success = False
                            if method == GetShaMethod.GITHUB_API:
                                success, sha_value = TestGetRemoteShaMethodWorker.github_api_get_latest_sha(config)
                            elif method == GetShaMethod.PYGIT2:
                                success, sha_value = TestGetRemoteShaMethodWorker.dulwich_get_latest_sha(config)
                            if success:
                                self._BAAS_remote_version_sha = sha_value
                            else:
                                self._BAAS_remote_version_sha = ""
                            break
            else:
                self._update_method = None

        if self._BAAS_remote_version_sha == "":
            error(self.tr("错误"), self.tr("无法获取远程BAAS版本信息"), self.config)
        self._update_BAAS_update_method_layout()
        self._update_BAAS_remote_version_layout()

    def _update_BAAS_update_method_layout(self):
        if self._update_method == "mirrorc":
            self._current_update_method_label.setText(self.tr("使用Mirror酱更新"))
            palette = self._current_update_method_label.palette()
            palette.setColor(palette.WindowText, QColor("#107c10"))
            self._current_update_method_label.setPalette(palette)
        elif self._update_method == "git":
            self._current_update_method_label.setText(f"{self.tr('从')}{self.REPO_URL_NAME_mapping.get(self._repo_url_http)}{self.tr('拉取更新')}")
            palette = self._current_update_method_label.palette()
            palette.setColor(palette.WindowText, QColor("#107c10"))
            self._current_update_method_label.setPalette(palette)
        else:
            self._current_update_method_label.setText(self.tr("无法获取更新方法"))
            palette = self._current_update_method_label.palette()
            palette.setColor(palette.WindowText, QColor("#a80000"))
            self._current_update_method_label.setPalette(palette)

    def _update_BAAS_remote_version_layout(self):
        if  self._BAAS_remote_version_sha == "" or \
            self._BAAS_remote_version_get_method not in ["mirrorc", "git"] or \
            self._BAAS_remote_version_get_method != self._update_method:
            return

        self._BAAS_remote_version_label.setText(self._BAAS_remote_version_sha)
        if self._BAAS_remote_version_get_method == "mirrorc":
            self._BAAS_remote_version_get_method_label.setText(f"({self.tr('Mirror酱获取')})")
        if self._BAAS_remote_version_get_method == "git":
            self._BAAS_remote_version_get_method_label.setText(f"({self.tr('从')}{self.REPO_URL_NAME_mapping.get(self._repo_url_http)}{self.tr('获取')})")
        self._check_has_update()

    def _check_has_update(self):
        if self._BAAS_remote_version_sha != "" and self._BAAS_local_version_sha is not None:
            if self._BAAS_local_version_sha == self._BAAS_remote_version_sha:
                self._BAAS_local_version_state.setText(self.tr("最新版本"))
                palette = self._BAAS_local_version_state.palette()
                palette.setColor(palette.WindowText, QColor("#107c10"))
                self._BAAS_local_version_state.setPalette(palette)
            if self._BAAS_local_version_sha != self._BAAS_remote_version_sha:
                self._BAAS_local_version_state.setText(self.tr("有新版本可用, 重启即可更新"))
                palette = self._BAAS_local_version_state.palette()
                palette.setColor(palette.WindowText, QColor("#a80000"))
                self._BAAS_local_version_state.setPalette(palette)

