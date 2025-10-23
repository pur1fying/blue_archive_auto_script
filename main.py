import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QGroupBox, QPushButton, QTextEdit, QHBoxLayout, QLineEdit

from core.android import shizuku
from core.utils import Logger

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shizuku Test")
        self.resize(600, 400)
        self.logger = Logger(None)
        self.shizuku_client = shizuku.ShizukuClient(self.logger)
        main_layout = QVBoxLayout(self)

        # Action GroupBox
        action_groupbox = QGroupBox("Action")
        action_layout = QVBoxLayout()

        # Button layout for horizontal arrangement
        button_layout = QHBoxLayout()
        self.request_permission_button = QPushButton("Request Permission")
        self.connect_button = QPushButton("Connect Service")
        self.disconnect_button = QPushButton("Disconnect Service")
        self.disconnect_button.setEnabled(False)  # Initially disabled

        button_layout.addWidget(self.request_permission_button)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        action_layout.addLayout(button_layout)

        # Command execution section
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command to execute...")
        self.execute_button = QPushButton("Execute Command")
        self.execute_button.setEnabled(False)  # Initially disabled
        self.exec_stream_button = QPushButton("Exec Stream")
        self.exec_stream_button.setEnabled(False)

        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.execute_button)
        command_layout.addWidget(self.exec_stream_button)
        action_layout.addLayout(command_layout)

        action_groupbox.setLayout(action_layout)

        # Log GroupBox
        log_groupbox = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_textarea = QTextEdit()
        self.log_textarea.setReadOnly(True)
        log_layout.addWidget(self.log_textarea)
        log_groupbox.setLayout(log_layout)

        main_layout.addWidget(action_groupbox)
        main_layout.addWidget(log_groupbox)
        
        # ============= FS Demo =============
        fs_groupbox = QGroupBox("Filesystem Demo")
        fs_v = QVBoxLayout()
        fs_paths_layout = QHBoxLayout()
        self.fs_dir_input = QLineEdit("/sdcard/boa_demo")
        self.fs_file_input = QLineEdit("/sdcard/boa_demo/file.txt")
        fs_paths_layout.addWidget(self.fs_dir_input)
        fs_paths_layout.addWidget(self.fs_file_input)
        fs_v.addLayout(fs_paths_layout)

        fs_content_layout = QHBoxLayout()
        self.fs_content_input = QLineEdit("hello from boa")
        self.fs_dst_input = QLineEdit("/sdcard/boa_demo/file_moved.txt")
        fs_content_layout.addWidget(self.fs_content_input)
        fs_content_layout.addWidget(self.fs_dst_input)
        fs_v.addLayout(fs_content_layout)

        fs_btns = QHBoxLayout()
        self.fs_mkdirs_btn = QPushButton("mkdirs(dir)")
        self.fs_write_btn = QPushButton("write(file)")
        self.fs_read_btn = QPushButton("read(file)")
        self.fs_stat_btn = QPushButton("stat(file)")
        self.fs_list_btn = QPushButton("ls(dir)")
        self.fs_move_btn = QPushButton("mv(file->dst)")
        self.fs_delete_btn = QPushButton("delete(dir,recursive)")
        for b in (self.fs_mkdirs_btn, self.fs_write_btn, self.fs_read_btn, self.fs_stat_btn, self.fs_list_btn, self.fs_move_btn, self.fs_delete_btn):
            b.setEnabled(False)
            fs_btns.addWidget(b)
        fs_v.addLayout(fs_btns)
        fs_groupbox.setLayout(fs_v)

        # FS wiring
        self.fs_mkdirs_btn.clicked.connect(self.__handle_fs_mkdirs)
        self.fs_write_btn.clicked.connect(self.__handle_fs_write)
        self.fs_read_btn.clicked.connect(self.__handle_fs_read)
        self.fs_stat_btn.clicked.connect(self.__handle_fs_stat)
        self.fs_list_btn.clicked.connect(self.__handle_fs_list)
        self.fs_move_btn.clicked.connect(self.__handle_fs_move)
        self.fs_delete_btn.clicked.connect(self.__handle_fs_delete)

        # ============= Package Manager Demo =============
        pm_groupbox = QGroupBox("Package Manager Demo")
        pm_v = QVBoxLayout()
        pm_row = QHBoxLayout()
        self.apk_path_input = QLineEdit("/sdcard/sample.apk")
        self.pkg_name_input = QLineEdit("com.example.sample")
        pm_row.addWidget(self.apk_path_input)
        pm_row.addWidget(self.pkg_name_input)
        pm_v.addLayout(pm_row)

        pm_btns = QHBoxLayout()
        self.pm_install_btn = QPushButton("pm install")
        self.pm_uninstall_btn = QPushButton("pm uninstall")
        self.pm_install_btn.setEnabled(False)
        self.pm_uninstall_btn.setEnabled(False)
        pm_btns.addWidget(self.pm_install_btn)
        pm_btns.addWidget(self.pm_uninstall_btn)
        pm_v.addLayout(pm_btns)
        pm_groupbox.setLayout(pm_v)

        self.pm_install_btn.clicked.connect(self.__handle_pm_install)
        self.pm_uninstall_btn.clicked.connect(self.__handle_pm_uninstall)

        main_layout.addWidget(fs_groupbox)
        main_layout.addWidget(pm_groupbox)

        main_layout.setStretchFactor(log_groupbox, 1)
        
        self.request_permission_button.clicked.connect(self.__handle_request_permission)
        self.connect_button.clicked.connect(self.__handle_connect_service)
        self.disconnect_button.clicked.connect(self.__handle_disconnect_service)
        self.execute_button.clicked.connect(self.__handle_execute_command)
        self.exec_stream_button.clicked.connect(self.__handle_exec_stream)

        # Shizuku listener instance
        self._shizuku_listener = None
        self.__init_shizuku()

    def __log(self, msg: str):
        self.log_textarea.append(msg)
    
    def __init_shizuku(self):
        try:
            available = shizuku.is_available()
        except Exception as e:
            self.__log(f'Shizuku availability check failed: {e}')
            return
        if not available:
            self.__log('Shizuku class not available (Shizuku may not be installed on device)')
            return

        def _on_permission_result(request_code: int, grant_result: int):
            try:
                granted = grant_result == shizuku.PackageManager.PERMISSION_GRANTED
            except Exception:
                granted = False
            self.__log('Permission granted' if granted else 'Permission denied')

        try:
            self._shizuku_listener = shizuku.add_request_permission_result_listener(_on_permission_result)
            self.__log('Shizuku permission listener registered')
        except Exception as e:
            self.__log(f'Failed to register permission listener: {e}')

    def __handle_request_permission(self):
        self.__log('Requesting Shizuku permission...')
        try:
            if not shizuku.is_available():
                self.__log('Shizuku class not available, cannot request permission')
                return
            if shizuku.check_permission():
                self.__log('Already have permission')
                return
            shizuku.request_permission()
            self.__log('Permission request initiated')
        except Exception as e:
            self.__log(f'Exception occurred while requesting permission: {e}')

    def __handle_connect_service(self):
        self.__log('Connecting to Shizuku service...')
        try:
            if self.shizuku_client.connect():
                self.__log('Successfully connected to Shizuku service')
                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.execute_button.setEnabled(True)
                self.exec_stream_button.setEnabled(True)
                for b in (self.fs_mkdirs_btn, self.fs_write_btn, self.fs_read_btn, self.fs_stat_btn, self.fs_list_btn, self.fs_move_btn, self.fs_delete_btn, self.pm_install_btn, self.pm_uninstall_btn):
                    b.setEnabled(True)
            else:
                self.__log('Failed to connect to Shizuku service')
        except Exception as e:
            self.__log(f'Exception occurred while connecting: {e}')

    def __handle_disconnect_service(self):
        self.__log('Disconnecting from Shizuku service...')
        try:
            if self.shizuku_client.disconnect():
                self.__log('Successfully disconnected from Shizuku service')
                self.disconnect_button.setEnabled(False)
                self.execute_button.setEnabled(False)
                self.exec_stream_button.setEnabled(False)
                for b in (self.fs_mkdirs_btn, self.fs_write_btn, self.fs_read_btn, self.fs_stat_btn, self.fs_list_btn, self.fs_move_btn, self.fs_delete_btn, self.pm_install_btn, self.pm_uninstall_btn):
                    b.setEnabled(False)
                self.connect_button.setEnabled(True)
            else:
                self.__log('Failed to disconnect from Shizuku service')
        except Exception as e:
            self.__log(f'Exception occurred while disconnecting: {e}')

    def __handle_execute_command(self):
        command = self.command_input.text().strip()
        if not command:
            self.__log('Please enter a command to execute')
            return

        self.__log(f'Executing command: {command}')
        try:
            success, result = self.shizuku_client.execute_command(command)
            if success:
                # result is a CommandResult namedtuple
                assert isinstance(result, shizuku.CommandResult)
                self.__log(f'Command executed successfully. Exit={result.exitCode}')
                if result.stdout:
                    self.__log(f'stdout:\n{result.stdout}')
                if result.stderr:
                    self.__log(f'stderr:\n{result.stderr}')
            else:
                self.__log(f'Command execution failed. Error: {result}')
        except Exception as e:
            self.__log(f'Exception occurred while executing command: {e}')

    def __handle_exec_stream(self):
        command = self.command_input.text().strip()
        if not command:
            self.__log('Please enter a command to execute (stream)')
            return
        self.__log(f'Exec stream: {command}')
        try:
            ok = self.shizuku_client.exec_stream(
                command,
                on_stdout=lambda line: self.__log(f'[out] {line}'),
                on_stderr=lambda line: self.__log(f'[err] {line}'),
                on_done=lambda code: self.__log(f'[done] exit={code}')
            )
            if not ok:
                self.__log('Exec stream failed to start')
        except Exception as e:
            self.__log(f'Exception during exec stream: {e}')

    # ===== Filesystem handlers =====
    def __handle_fs_mkdirs(self):
        path = self.fs_dir_input.text().strip()
        ok = self.shizuku_client.fs_mkdirs(path)
        self.__log(f'mkdirs("{path}") => {ok}')

    def __handle_fs_write(self):
        path = self.fs_file_input.text().strip()
        content = self.fs_content_input.text()
        ok = self.shizuku_client.fs_write(path, content, append=False)
        self.__log(f'write("{path}") => {ok}')

    def __handle_fs_read(self):
        path = self.fs_file_input.text().strip()
        data = self.shizuku_client.fs_read(path)
        if isinstance(data, (bytes, bytearray)):
            self.__log(f'read("{path}") => {len(data)} bytes (binary)')
        else:
            self.__log(f'read("{path}") =>\n{data}')

    def __handle_fs_stat(self):
        path = self.fs_file_input.text().strip()
        st = self.shizuku_client.fs_stat(path)
        self.__log(f'stat("{path}") => {st}')

    def __handle_fs_list(self):
        path = self.fs_dir_input.text().strip()
        items = self.shizuku_client.fs_list(path)
        self.__log(f'ls("{path}") => {items}')

    def __handle_fs_move(self):
        src = self.fs_file_input.text().strip()
        dst = self.fs_dst_input.text().strip()
        ok = self.shizuku_client.fs_move(src, dst, replace=True)
        self.__log(f'mv("{src}" -> "{dst}") => {ok}')

    def __handle_fs_delete(self):
        path = self.fs_dir_input.text().strip()
        ok = self.shizuku_client.fs_delete(path, recursive=True)
        self.__log(f'delete("{path}", recursive=True) => {ok}')

    # ===== Package manager handlers =====
    def __handle_pm_install(self):
        apk_path = self.apk_path_input.text().strip()
        try:
            ok = self.shizuku_client.pm_install(apk_path)
            self.__log(f'pm install => {ok}')
        except Exception as e:
            self.__log(f'pm install error: {e}')

    def __handle_pm_uninstall(self):
        pkg = self.pkg_name_input.text().strip()
        try:
            ok = self.shizuku_client.pm_uninstall(pkg)
            self.__log(f'pm uninstall => {ok}')
        except Exception as e:
            self.__log(f'pm uninstall error: {e}')

    def closeEvent(self, event):
        if self._shizuku_listener is not None:
            try:
                shizuku.remove_request_permission_result_listener(self._shizuku_listener)
                self.__log('Shizuku permission listener removed')
            except Exception as e:
                self.__log(f'Failed to remove permission listener: {e}')
            finally:
                self._shizuku_listener = None
        return super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
