import binascii
import threading
import time
import webbrowser

import dulwich
import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QHeaderView, QTableWidgetItem, QWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox)
from qfluentwidgets import (TableWidget, ComboBox, PrimaryPushButton, TextEdit,
                            PushButton, BodyLabel)

from core.utils import delay
from deploy.installer.const import GetShaMethod, get_remote_sha_methods
from deploy.installer.mirrorc_update.const import MirrorCErrorCode
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater, RequestReturn
from gui.util.config_gui import COLOR_THEME, configGui
from gui.util.notification import success, error


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
        super().__init__(parent=parent)
        self.config = config
        self._repo = None
        self._cdk_test_thread = None
        self.workers = []

        self.REPO_URL_NAME_mapping = {
            "https://github.com/pur1fying/blue_archive_auto_script.git": self.tr("GitHub (主仓库)"),
            "https://gitee.com/pur1fy/blue_archive_auto_script.git": self.tr("Gitee (国内镜像)"),
            "https://gitcode.com/m0_74686738/blue_archive_auto_script.git": self.tr("GitCode (国内镜像)"),
            "https://e.coding.net/g-jbio0266/baas/blue_archive_auto_script.git": self.tr("腾讯工蜂 (国内镜像)")
        }
        self._revert_REPO_URL_NAME_mapping = {v: k for k, v in self.REPO_URL_NAME_mapping.items()}
        self.REPO_URL_CHECK_UPDATE_METHOD_mapping = {
            "https://github.com/pur1fying/blue_archive_auto_script.git": "github",
            "https://gitee.com/pur1fy/blue_archive_auto_script.git": "gitee",
            "https://gitcode.com/m0_74686738/blue_archive_auto_script.git": "gitcode",
            "https://e.coding.net/g-jbio0266/baas/blue_archive_auto_script.git": "tencent_c_coding"
        }

        self._main_vBoxLayout = QVBoxLayout(self)
        self._setup_styles()

        # 初始化UI组件
        self._create_version_info_group()
        self._create_update_method_group()
        self._create_repo_settings_group()
        self._create_connectivity_test_group()

        self._main_vBoxLayout.addStretch(1)

        # 初始化数据和状态
        self._init_data_and_state()
        configGui.themeChanged.connect(self._setup_styles)

    def _setup_styles(self):
        """统一设置界面样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding: 20px 10px 10px 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
                color: %(title_text_color)s;
            }
            QLabel {
                font-size: 14px;
            }
            QLabel[state="success"] {
                color: %(success_text_color)s;
            }
            QLabel[state="error"] {
                color: %(error_text_color)s;
            }
            QLabel[state="testing"] {
                color: %(testing_text_color)s;
            }
            QLabel[state="info"] {
                color: %(info_text_color)s;
            }
        """ % {
            'success_text_color': COLOR_THEME[configGui.theme.value]['text__success'],
            'error_text_color': COLOR_THEME[configGui.theme.value]['text__error'],
            'testing_text_color': COLOR_THEME[configGui.theme.value]['text__gray'],
            'info_text_color': COLOR_THEME[configGui.theme.value]['text__info'],
            'title_text_color': COLOR_THEME[configGui.theme.value]['text']
        })

    def _create_version_info_group(self):
        """创建版本信息区域"""
        version_group = QGroupBox(self.tr("版本信息"), self)
        layout = QGridLayout(version_group)

        self._BAAS_local_version_label = BodyLabel(self.tr("正在获取..."))
        self._BAAS_local_version_method_label = BodyLabel("")
        self._BAAS_local_version_state_label = BodyLabel("")
        self._BAAS_local_version_state_label.setWordWrap(True)

        self._BAAS_remote_version_label = BodyLabel(self.tr("待检测"))
        self._BAAS_remote_version_method_label = BodyLabel("")

        layout.addWidget(BodyLabel(self.tr("当前版本:")), 0, 0)
        layout.addWidget(self._BAAS_local_version_label, 0, 1)
        layout.addWidget(self._BAAS_local_version_method_label, 0, 2)
        layout.addWidget(self._BAAS_local_version_state_label, 1, 1, 1, 2)

        layout.addWidget(BodyLabel(self.tr("远程版本:")), 2, 0)
        layout.addWidget(self._BAAS_remote_version_label, 2, 1)
        layout.addWidget(self._BAAS_remote_version_method_label, 2, 2)

        layout.setColumnStretch(1, 1)
        self._main_vBoxLayout.addWidget(version_group)

    def _create_update_method_group(self):
        """创建更新方式和Mirror酱CDK区域"""
        method_group = QGroupBox(self.tr("更新方式"), self)
        layout = QGridLayout(method_group)

        self._current_update_method_label = BodyLabel(self.tr("检测中..."))
        self._current_update_method_label.setWordWrap(True)
        layout.addWidget(BodyLabel(self.tr("当前更新方式:")), 0, 0)
        layout.addWidget(self._current_update_method_label, 0, 1, 1, 3)

        self._mirrorc_cdk = self.config.get("General.mirrorc_cdk", None)
        self._mirrorc_update_available = self._mirrorc_cdk is not None

        if self._mirrorc_update_available:
            self._mirrorc_inst = MirrorC_Updater(app="BAAS_repo", current_version="")
            self._mirrorc_cdk_TextEdit = TextEdit(self)
            self._mirrorc_cdk_TextEdit.setPlaceholderText(self.tr("在此处粘贴Mirror酱CDK"))
            self._mirrorc_cdk_TextEdit.setFixedHeight(35)
            self._mirrorc_cdk_state_label = BodyLabel(self.tr("待测试"))
            self._mirrorc_cdk_state_label.setWordWrap(True)
            self._test_mirrorc_cdk_button = PushButton(self.tr("测试"))

            layout.addWidget(BodyLabel(self.tr("Mirror酱CDK:")), 1, 0)
            layout.addWidget(self._mirrorc_cdk_TextEdit, 1, 1)
            layout.addWidget(self._test_mirrorc_cdk_button, 1, 2)
            layout.addWidget(self._mirrorc_cdk_state_label, 2, 1)
            layout.setColumnStretch(1, 1)
        else:
            self._mirrorc_invalid_label = BodyLabel(self.tr("当前启动器版本过低(<1.4.0)，无法使用Mirror酱更新。"))
            # self._mirrorc_invalid_label.setWordWrap(True)
            self._update_status_label(self._mirrorc_invalid_label, "error")
            self._mirrorc_invalid_update_button = PrimaryPushButton(self.tr("前往下载新版启动器"))

            layout.addWidget(self._mirrorc_invalid_label, 1, 0, 1, 2)
            layout.addWidget(self._mirrorc_invalid_update_button, 1, 3)

        what_is_mirrorc_button = PushButton(self.tr("什么是Mirror酱?"))
        what_is_mirrorc_button.clicked.connect(
            lambda: webbrowser.open("https://baas.wiki/usage_doc/install/Windows.html#mirror%E9%85%B1cdk"))
        layout.addWidget(what_is_mirrorc_button, 1, 3 if self._mirrorc_update_available else 4)

        self._main_vBoxLayout.addWidget(method_group)

    def _create_repo_settings_group(self):
        """创建Git仓库相关设置区域"""
        repo_group = QGroupBox(self.tr("仓库设置"), self)
        layout = QGridLayout(repo_group)

        self._repo_url_http_ComboBox = ComboBox(self)
        self._repo_url_http_ComboBox.addItems(list(self.REPO_URL_NAME_mapping.values()))

        self.get_remote_sha_method_ComboBox = ComboBox(self)

        layout.addWidget(BodyLabel(self.tr("Git更新仓库:")), 0, 0)
        layout.addWidget(self._repo_url_http_ComboBox, 0, 1)
        layout.addWidget(BodyLabel(self.tr("SHA获取方式:")), 1, 0)
        layout.addWidget(self.get_remote_sha_method_ComboBox, 1, 1)
        layout.setColumnStretch(1, 1)

        self._main_vBoxLayout.addWidget(repo_group)

    def _create_connectivity_test_group(self):
        """创建连通性测试区域"""
        test_group = QGroupBox(self.tr("连通性测试"), self)

        layout = QVBoxLayout(test_group)

        h_layout = QHBoxLayout()
        self.status_label = BodyLabel(self.tr("点击按钮开始测试所有远程仓库的连接速度和可用性。"))
        self.status_label.setWordWrap(True)
        self._test_get_remote_sha_method_push_button = PrimaryPushButton(self.tr("测试所有方法"))
        h_layout.addWidget(self.status_label)
        h_layout.addStretch(1)
        h_layout.addWidget(self._test_get_remote_sha_method_push_button)

        self.test_result_table = TableWidget(self)
        self.test_result_table.setColumnCount(4)
        self.test_result_table.setHorizontalHeaderLabels([
            self.tr("方法"), self.tr("状态"), self.tr("耗时(秒)"), self.tr("获取的SHA值")
        ])
        header = self.test_result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.test_result_table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        layout.addLayout(h_layout)
        layout.addWidget(self.test_result_table)
        self._main_vBoxLayout.addWidget(test_group)

    def _init_data_and_state(self):
        """初始化所有数据和UI状态"""
        # 获取本地版本
        self._get_local_version()

        # 绑定仓库设置的信号
        self._repo_url_http = self.config.get("URLs.REPO_URL_HTTP", None)
        if self._repo_url_http and self._repo_url_http in self.REPO_URL_NAME_mapping:
            self._repo_url_http_ComboBox.setCurrentText(self.REPO_URL_NAME_mapping[self._repo_url_http])
        self._repo_url_http_ComboBox.currentIndexChanged.connect(self._on_repo_url_changed)

        # 初始化SHA获取方式下拉框
        self._init_get_remote_sha_method_ComboBox()

        # 绑定Mirror酱CDK相关信号
        if self._mirrorc_update_available:
            cdk_text = self.config.get("General.mirrorc_cdk", "")
            if cdk_text:
                self._mirrorc_cdk_TextEdit.setText(cdk_text)
                self._test_and_set_mirrorc_cdk_state(save=False)  # 启动时自动测试一次已保存的CDK
            self._test_mirrorc_cdk_button.clicked.connect(lambda: self._test_and_set_mirrorc_cdk_state(save=False))
            self._mirrorc_cdk_TextEdit.textChanged.connect(self._on_cdk_text_changed_debounced)
        else:
            self._mirrorc_invalid_update_button.clicked.connect(
                lambda: webbrowser.open("https://github.com/pur1fying/blue_archive_auto_script/releases"))

        # 连通性测试
        self._init_test_table_content()
        self._test_get_remote_sha_method_push_button.clicked.connect(self._test_all_get_remote_sha_method)

        # 首次检测更新方式
        self._detect_update_method_and_update_ui()

    def _get_local_version(self):
        self._BAAS_local_version_sha = self.config.get("General.current_BAAS_version", None)
        method = "setup.toml"
        if not self._BAAS_local_version_sha:
            try:
                self._repo = dulwich.repo.Repo(".")
                self._BAAS_local_version_sha = self._repo.head().decode("utf-8")
                method = ".git"
            except Exception:
                method = None

        if self._BAAS_local_version_sha:
            sha_display = self._BAAS_local_version_sha
            self._BAAS_local_version_label.setText(sha_display)
            method_text = f"({self.tr('从 setup.toml 读取')})" if method == "setup.toml" else f"({self.tr('从 .git 读取')})"
            self._BAAS_local_version_method_label.setText(method_text)
        else:
            self._BAAS_local_version_label.setText(self.tr("无法获取"))
            self._update_status_label(self._BAAS_local_version_label, "error")
            self._BAAS_local_version_method_label.setText("")

    def _on_repo_url_changed(self):
        selected_text = self._repo_url_http_ComboBox.currentText()
        url = self._revert_REPO_URL_NAME_mapping.get(selected_text)
        if url:
            self.__set_config_and_display_message("URLs.REPO_URL_HTTP", url)
            self._detect_update_method_and_update_ui()

    @delay(0.8)  # 防抖，避免输入过程中频繁触发
    def _on_cdk_text_changed_debounced(self):
        self._test_and_set_mirrorc_cdk_state(save=True)

    def __set_config_and_display_message(self, key, value):
        self.config.set_and_save(key, value)
        success(self.tr("设置已保存"), f"{key} = {value}", self.config)

    def _update_status_label(self, label: QLabel, state: str, text: str = None):
        """
        统一更新标签样式和文本
        :param label: 要更新的QLabel控件
        :param state: 状态 'success', 'error', 'testing', 'info' 或 ''
        :param text: 要显示的文本，如果为None则不改变文本
        """
        if text is not None:
            label.setText(text)
        label.setProperty("state", state)
        # 刷新样式表以应用新属性
        label.style().polish(label)

    # --- MirrorC CDK ---
    def _test_and_set_mirrorc_cdk_state(self, save=False):
        cdk = self._mirrorc_cdk_TextEdit.toPlainText().strip()
        if not cdk:
            self._update_status_label(self._mirrorc_cdk_state_label, "info", self.tr("请输入CDK"))
            return

        self._update_status_label(self._mirrorc_cdk_state_label, "testing", self.tr("测试中..."))
        self._mirrorc_cdk_TextEdit.setEnabled(False)
        self._test_mirrorc_cdk_button.setEnabled(False)

        self._cdk_test_thread = MirrorCCDKTestThread(self, cdk, save=save)
        self._cdk_test_thread.finished.connect(self._handle_cdk_test_result)
        self._cdk_test_thread.start()

    def _handle_cdk_test_result(self, request_ret, save=False):
        code = request_ret.code
        if code is MirrorCErrorCode.SUCCESS.value:
            expired_time = time.localtime(request_ret.cdk_expired_time)
            expired_time_str = time.strftime("%Y-%m-%d %H:%M:%S", expired_time)
        else:
            expired_time_str = ""

        messages = {
            MirrorCErrorCode.SUCCESS.value: self.tr("有效，到期时间: ") + expired_time_str,
            MirrorCErrorCode.KEY_EXPIRED.value: self.tr("CDK已过期"),
            MirrorCErrorCode.KEY_INVALID.value: self.tr("CDK无效"),
            MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value: self.tr("今日下载次数已用完"),
            MirrorCErrorCode.KEY_MISMATCHED.value: self.tr("CDK与请求资源不匹配"),
            MirrorCErrorCode.KEY_BLOCKED.value: self.tr("CDK已被封禁"),
        }
        message = messages.get(code, self.tr("未知错误"))

        self._mirrorc_cdk_is_valid = (code == MirrorCErrorCode.SUCCESS.value)

        if self._mirrorc_cdk_is_valid:
            self._update_status_label(self._mirrorc_cdk_state_label, "success", message)
            if save:
                self.__set_config_and_display_message("General.mirrorc_cdk",
                                                      self._mirrorc_cdk_TextEdit.toPlainText().strip())
            else:
                success(self.tr("CDK测试成功"), message, self.config)
            self._BAAS_remote_version_sha = request_ret.latest_version_name
            self._BAAS_remote_version_get_method = "mirrorc"
        else:
            self._update_status_label(self._mirrorc_cdk_state_label, "error", message)
            error(self.tr("CDK错误"), message, self.config)

        self._mirrorc_cdk_TextEdit.setEnabled(True)
        self._test_mirrorc_cdk_button.setEnabled(True)
        self._detect_update_method_and_update_ui()

    # --- SHA获取方式 ---
    def _init_get_remote_sha_method_ComboBox(self):
        self.get_remote_sha_method_origin_names = [item["name"] for item in get_remote_sha_methods]
        self.get_remote_sha_method_display_names = [
            self.tr("GitHub API"), self.tr("Mirror酱免费API"), self.tr("Gitee仓库读取"),
            self.tr("GitCode仓库读取"), self.tr("腾讯工蜂仓库读取")
        ]

        # TODO: Handle case where saved method is not in the list
        if not self._mirrorc_update_available:
            self.get_remote_sha_method_display_names.pop(1)
            get_remote_sha_methods.pop(1)

        header = self.test_result_table.horizontalHeader()
        row_count = len(get_remote_sha_methods)
        self.test_result_table.setRowCount(row_count)
        table_height = min(400, row_count * 35 + header.height() + 5)
        self.test_result_table.setFixedHeight(table_height)

        self._get_remote_sha_method = self.config.get("General.get_remote_sha_method")
        self.get_remote_sha_method_ComboBox.addItems(self.get_remote_sha_method_display_names)

        if self._get_remote_sha_method in self.get_remote_sha_method_origin_names:
            idx = self.get_remote_sha_method_origin_names.index(self._get_remote_sha_method)
            self.get_remote_sha_method_ComboBox.setCurrentIndex(idx)

        self.get_remote_sha_method_ComboBox.currentIndexChanged.connect(self._on_sha_method_changed)

    def _on_sha_method_changed(self, index):
        selected_method = self.get_remote_sha_method_origin_names[index]
        self.__set_config_and_display_message("General.get_remote_sha_method", selected_method)

    # --- 连通性测试 ---
    def _init_test_table_content(self):
        for i, config in enumerate(get_remote_sha_methods):
            method_item = QTableWidgetItem(self.get_remote_sha_method_display_names[i])
            status_item = QTableWidgetItem(self.tr("待测试"))
            time_item = QTableWidgetItem("-")
            sha_item = QTableWidgetItem("-")

            for item in [method_item, status_item, time_item, sha_item]:
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

            self.test_result_table.setItem(i, 0, method_item)
            self.test_result_table.setItem(i, 1, status_item)
            self.test_result_table.setItem(i, 2, time_item)
            self.test_result_table.setItem(i, 3, sha_item)
            self.test_result_table.item(i, 0).setData(Qt.UserRole, config)

    def _test_all_get_remote_sha_method(self):
        self._test_get_remote_sha_method_push_button.setEnabled(False)
        self._update_status_label(self.status_label, "testing", self.tr("测试进行中..."))

        for row in range(self.test_result_table.rowCount()):
            self.test_result_table.item(row, 1).setText(self.tr("测试中..."))
            self.test_result_table.item(row, 1).setForeground(QColor(
                COLOR_THEME[configGui.theme.value]['text__warning']
            ))
            self.test_result_table.item(row, 2).setText("-")
            self.test_result_table.item(row, 3).setText("-")

        self.workers = []
        self.completed_count = 0
        for row in range(self.test_result_table.rowCount()):
            config = self.test_result_table.item(row, 0).data(Qt.UserRole)
            worker = TestGetRemoteShaMethodWorker(config)
            worker.test_completed.connect(self._update_test_result)
            worker.start()
            self.workers.append(worker)

    def _update_test_result(self, config, _success, sha_value, elapsed_time):
        for row in range(self.test_result_table.rowCount()):
            if self.test_result_table.item(row, 0).data(Qt.UserRole) == config:
                status_item = self.test_result_table.item(row, 1)
                if _success:
                    status_item.setText(self.tr("成功"))
                    status_item.setForeground(QColor(
                        COLOR_THEME[configGui.theme.value]['text__success']
                    ))
                    self.test_result_table.item(row, 2).setText(f"{elapsed_time:.3f}")
                    self.test_result_table.item(row, 3).setText(sha_value)
                    self.test_result_table.item(row, 3).setToolTip(sha_value)
                else:
                    status_item.setText(self.tr("失败"))
                    status_item.setForeground(QColor(
                        COLOR_THEME[configGui.theme.value]['text__error']
                    ))
                    self.test_result_table.item(row, 3).setText("/")  # Show error message

                self.completed_count += 1
                self._update_status_label(self.status_label, "testing",
                                          f"测试进度: {self.completed_count}/{len(get_remote_sha_methods)}")
                if self.completed_count == len(get_remote_sha_methods):
                    self._test_get_remote_sha_method_push_button.setEnabled(True)
                    self._update_status_label(self.status_label, "success", self.tr("所有测试已完成。"))
                    success(self.tr("测试完成"), self.tr("所有远程方法均已测试完毕。"), self.config)
                break

    # --- 核心逻辑: 检测和更新UI ---
    def _detect_update_method_and_update_ui(self):
        self._update_status_label(self._current_update_method_label, "testing", self.tr("正在检测最佳更新方式..."))
        threading.Thread(target=self._detect_update_method_thread, daemon=True).start()

    def _detect_update_method_thread(self):
        self._update_method = None
        # 1. 优先检查有效的MirrorC
        if self._mirrorc_update_available and len(self._mirrorc_cdk) > 0:
            if self._cdk_test_thread and not self._cdk_test_thread.is_finished:
                self._cdk_test_thread.wait()  # 等待当前测试完成

            try:
                fx = self._mirrorc_cdk_is_valid
            except AttributeError:
                print("TRIGGER: MirrorC CDK is not valid or not tested yet.")
                time.sleep(0.5)
                self._detect_update_method_thread()
                return None

            if fx:
                self._update_method = "mirrorc"

        # 2. 如果MirrorC不可用，再检查Git
        if self._update_method is None:
            self._repo_url_http = self.config.get("URLs.REPO_URL_HTTP", None)
            if self._repo_url_http and self._repo_url_http in self.REPO_URL_NAME_mapping:
                self._update_method = "git"
                method_name = self.REPO_URL_CHECK_UPDATE_METHOD_mapping.get(self._repo_url_http)
                if method_name:
                    config = next((c for c in get_remote_sha_methods if c["name"] == method_name), None)
                    if config:
                        method_type = config["method"]
                        is_ok, sha = (TestGetRemoteShaMethodWorker.github_api_get_latest_sha(config)
                                      if method_type == GetShaMethod.GITHUB_API
                                      else TestGetRemoteShaMethodWorker.dulwich_get_latest_sha(config))
                        if is_ok:
                            self._BAAS_remote_version_sha = sha
                            self._BAAS_remote_version_get_method = "git"
                        else:
                            self._BAAS_remote_version_sha = ""  # 获取失败

        # 在主线程更新UI
        # self.sender().thread().msleep(100)  # 确保在主线程执行
        self._update_ui_after_detection()
        return None

    def _update_ui_after_detection(self):
        # 更新当前更新方式的显示
        if self._update_method == "mirrorc":
            self._update_status_label(self._current_update_method_label, "success", self.tr("将通过 Mirror酱 进行更新"))
        elif self._update_method == "git":
            repo_name = self.REPO_URL_NAME_mapping.get(self._repo_url_http)
            self._update_status_label(self._current_update_method_label, "success",
                                      f"{self.tr('将从')} {repo_name} {self.tr('拉取更新')}")
        else:
            self._update_status_label(self._current_update_method_label, "error",
                                      self.tr("无可用更新方法，请检查CDK或仓库设置"))

        while (not hasattr(self, "_BAAS_remote_version_sha")):
            time.sleep(0.1)  # Wait until the attribute is set

        # 更新远程版本号的显示
        if self._BAAS_remote_version_sha:
            sha_display = self._BAAS_remote_version_sha
            self._BAAS_remote_version_label.setText(sha_display)
            if self._BAAS_remote_version_get_method == "mirrorc":
                self._BAAS_remote_version_method_label.setText(f"({self.tr('由Mirror酱提供')})")
            elif self._BAAS_remote_version_get_method == "git":
                repo_name = self.REPO_URL_NAME_mapping.get(self._repo_url_http, "Git")
                self._BAAS_remote_version_method_label.setText(f"({self.tr('从')}{repo_name}{self.tr('获取')})")
        else:
            self._BAAS_remote_version_label.setText(self.tr("获取失败"))
            self._update_status_label(self._BAAS_remote_version_label, "error")
            self._BAAS_remote_version_method_label.setText("")

        self._check_and_display_update_status()

    def _check_and_display_update_status(self):
        if self._BAAS_remote_version_sha and self._BAAS_local_version_sha:
            if self._BAAS_local_version_sha == self._BAAS_remote_version_sha:
                self._update_status_label(self._BAAS_local_version_state_label, "success", self.tr("已是最新版本"))
            else:
                self._update_status_label(self._BAAS_local_version_state_label, "error",
                                          self.tr("检测到新版本，重启程序即可自动更新"))
        else:
            self._update_status_label(self._BAAS_local_version_state_label, "info", "")
