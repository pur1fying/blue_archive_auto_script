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

        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.execute_button)
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

        main_layout.setStretchFactor(log_groupbox, 1)
        
        self.request_permission_button.clicked.connect(self.__handle_request_permission)
        self.connect_button.clicked.connect(self.__handle_connect_service)
        self.disconnect_button.clicked.connect(self.__handle_disconnect_service)
        self.execute_button.clicked.connect(self.__handle_execute_command)

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
                self.__log(f'Command executed successfully. Result: {result}')
            else:
                self.__log(f'Command execution failed. Error: {result}')
        except Exception as e:
            self.__log(f'Exception occurred while executing command: {e}')

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
