import base64
from typing import TYPE_CHECKING, Union, Any, NamedTuple

from jnius import autoclass, PythonJavaClass
from jnius import java_method # type: ignore

from .util import main_activity
if TYPE_CHECKING:
    from core import Baas_thread


class CommandResult(NamedTuple):
    exitCode: int
    stdout: str
    stderr: str


class FsStatResult(NamedTuple):
    exists: bool
    isDir: bool
    size: int
    mtime: int
    mode: int
    uid: int
    gid: int


_listeners = set()
_stream_callbacks = set()
PERMISSION_CODE_DEFAULT = 1024
_LISTENER_IFACE = 'rikka.shizuku.Shizuku$OnRequestPermissionResultListener'
_LISTENER_IFACE_JNI = _LISTENER_IFACE.replace('.', '/')

Shizuku = autoclass('rikka.shizuku.Shizuku')
Shizuku_UserServiceArgs = autoclass('rikka.shizuku.Shizuku$UserServiceArgs')
ShizukuBinderWrapper = autoclass('rikka.shizuku.ShizukuBinderWrapper')
SystemServiceHelper = autoclass('rikka.shizuku.SystemServiceHelper')
String = autoclass('java.lang.String')
PackageManager = autoclass('android.content.pm.PackageManager')
IUserService = autoclass('org.baas.boa.IUserService')
IUserService_Stub = autoclass('org.baas.boa.IUserService$Stub')
UserService = autoclass('org.baas.boa.UserService')
ComponentName = autoclass('android.content.ComponentName')
_ListenerInterfaceClass = autoclass('rikka.shizuku.Shizuku$OnRequestPermissionResultListener')
# These are required, otherwise you will get 'java.lang.NoClassDefFoundError: org.baas.boa.xxx'
autoclass('org.baas.boa.CommandResult')
autoclass('org.baas.boa.FsReadResult')
autoclass('org.baas.boa.FsStat')

def is_available() -> bool:
    """Check if Shizuku class is available.

    Returns:
        bool: True if Shizuku class is available, False otherwise.
    """
    return Shizuku is not None


def is_pre_v11() -> bool:
    """Check if this is a pre-v11 version of Shizuku (does not support dynamic permission requests).

    Returns:
        bool: True if this is a pre-v11 version of Shizuku, False otherwise.
    """
    try:
        return bool(Shizuku.isPreV11())
    except Exception:
        # If method does not exist, default to supporting dynamic requests
        return False


def check_permission() -> bool:
    """Check if Shizuku adb shell permission is granted.

    Returns:
        bool: True if permission is granted, False otherwise.
    """
    try:
        return Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
    except Exception:
        return False


def request_permission(activity=None, request_code: int = PERMISSION_CODE_DEFAULT):
    """Request Shizuku permission dynamically.

    - If already authorized, return immediately.
    - If Shizuku version is too old (pre v11), return immediately.
    - Otherwise, initiate permission request.

    Args:
        activity: The activity context.
        request_code (int): The request code for the permission request.
    """
    if check_permission():
        return

    if is_pre_v11():
        return

    Shizuku.requestPermission(int(request_code))


class _PermissionResultListener(PythonJavaClass):
    """
    Proxy for Shizuku permission result listener.
    Corresponds to Java interface: Shizuku.OnRequestPermissionResultListener
    """

    __javainterfaces__ = [_LISTENER_IFACE_JNI]
    __javacontext__ = 'app'

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    # Signature: void onRequestPermissionResult(int requestCode, int grantResult)
    @java_method('(II)V')
    def onRequestPermissionResult(self, requestCode, grantResult):
        try:
            if callable(self._callback):
                self._callback(int(requestCode), int(grantResult))
        except Exception:
            # Callback exceptions should not affect the main flow
            pass


def add_request_permission_result_listener(callback):
    """Add permission request result listener.

    Args:
        callback: The callback function to be called when permission request result is received.

    Returns:
        The listener instance for later removal.
    """
    listener = _PermissionResultListener(callback)
    Shizuku.addRequestPermissionResultListener(listener)
    _listeners.add(listener)
    return listener


def remove_request_permission_result_listener(listener) -> None:
    """Remove the specified permission request result listener.

    Args:
        listener: The listener instance to remove.
    """
    try:
        Shizuku.removeRequestPermissionResultListener(listener)
    finally:
        if listener in _listeners:
            _listeners.remove(listener)


class ShizukuClient:
    """Client for interacting with Shizuku service.

    This class provides methods to connect to the Shizuku service and execute
    various operations such as running commands, file system operations, and
    package management.
    """

    def __init__(self, logger: 'Baas_thread.Logger'):
        """Initialize the ShizukuClient.

        Args:
            logger (Baas_thread.Logger): The logger instance for logging messages.
        """
        activity = main_activity()
        if not activity:
            logger.error("ShuzikuClient: cannot load main activity.")
            return
        self.context = activity.getApplicationContext()
        self.i_user_service: Any = None
        self.logger = logger
        
        # 创建 ServiceConnection 的实现类
        class ShizukuServiceConnection(PythonJavaClass):
            __javainterfaces__ = ['android/content/ServiceConnection']
            __javacontext__ = 'app'

            def __init__(self, client):
                super().__init__()
                self.client = client

            @java_method('(Landroid/content/ComponentName;Landroid/os/IBinder;)V')
            def onServiceConnected(self, name, service_binder):
                logger.info("ShizukuClient: Service connected")
                # 将 IBinder 转换为我们的 AIDL 接口
                self.client.i_user_service = IUserService_Stub.asInterface(service_binder)

            @java_method('(Landroid/content/ComponentName;)V')
            def onServiceDisconnected(self, name):
                logger.info("ShizukuClient: Service disconnected")
                self.client.i_user_service = None

        # 准备 Shizuku 连接所需的参数
        package_name = self.context.getPackageName()
        service_class_name = "org.baas.boa.UserService"
        component_name = ComponentName(package_name, service_class_name)
        
        self.user_service_args = Shizuku_UserServiceArgs(component_name) \
            .daemon(False) \
            .processNameSuffix("p4a_service") \
            .debuggable(True) \
            .version(1)
            
        self.service_connection = ShizukuServiceConnection(self)

    def connect(self):
        """Connect to the Shizuku service.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        if not Shizuku:
            self.logger.error("ShizukuClient: Shizuku classes not found.")
            return False

        # 检查 Shizuku 权限
        if Shizuku.checkSelfPermission() != 0: # 0 is PERMISSION_GRANTED
            self.logger.warning("ShizukuClient: Shizuku permission not granted. Requesting...")
            Shizuku.requestPermission(0) # 0 is a request code
            return False

        self.logger.info("ShizukuClient: Binding Shizuku user service...")
        try:
            Shizuku.bindUserService(self.user_service_args, self.service_connection)
            return True
        except Exception as e:
            self.logger.error(f"ShizukuClient: Failed to bind service: {e}")
            return False

    def disconnect(self):
        """Disconnect from the Shizuku service.

        Returns:
            bool: True if disconnection successful, False otherwise.
        """
        if self.i_user_service:
            self.logger.info("ShizukuClient: Unbinding Shizuku user service...")
            try:
                Shizuku.unbindUserService(self.user_service_args, self.service_connection, True)
                self.i_user_service = None
                return True
            except Exception as e:
                self.logger.error(f"ShizukuClient: Failed to unbind service: {e}")
                return False
        return True

    def execute_command(self, command) -> tuple[bool, Union[CommandResult, str]]:
        """Execute a shell command via Shizuku service.

        Args:
            command (str): The shell command to execute.

        Returns:
            tuple[bool, Union[CommandResult, str]]: A tuple containing:
                - bool: True if execution successful, False otherwise.
                - Union[CommandResult, str]: CommandResult on success, error message on failure.
        """
        if not self.i_user_service:
            self.logger.error("ShizukuClient: Service not connected.")
            return False, "Error: Service not connected."
        try:
            self.logger.info(f"ShizukuClient: Executing command: {command}")
            res = self.i_user_service.exec(command)
            result = CommandResult(
                exitCode=int(res.exitCode),
                stdout=str(res.stdout or ''),
                stderr=str(res.stderr or ''),
            )
            self.logger.info(f"ShizukuClient: Result: {result}")
            return True, result
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.logger.error(f"ShizukuClient: Command execution failed: {e}")
            return False, f"Error: {e}"

    class _StreamCallback(PythonJavaClass):
        __javainterfaces__ = ['org/baas/boa/IStreamCallback']
        __javacontext__ = 'app'

        def __init__(self, on_stdout=None, on_stderr=None, on_done=None):
            super().__init__()
            self._on_stdout = on_stdout
            self._on_stderr = on_stderr
            self._on_done = on_done

        @java_method('(Ljava/lang/String;)V')
        def onStdout(self, line):
            if callable(self._on_stdout):
                try:
                    self._on_stdout(line)
                except Exception:
                    pass

        @java_method('(Ljava/lang/String;)V')
        def onStderr(self, line):
            if callable(self._on_stderr):
                try:
                    self._on_stderr(line)
                except Exception:
                    pass

        @java_method('(I)V')
        def onDone(self, exitCode):
            if callable(self._on_done):
                try:
                    self._on_done(int(exitCode))
                except Exception:
                    pass

    def exec_stream(self, command, on_stdout=None, on_stderr=None, on_done=None):
        """Execute a shell command with streaming output via Shizuku service.

        Args:
            command (str): The shell command to execute.
            on_stdout (callable, optional): Callback for stdout data.
            on_stderr (callable, optional): Callback for stderr data.
            on_done (callable, optional): Callback when command execution finishes.

        Returns:
            bool: True if execution started successfully, False otherwise.
        """
        if not self.i_user_service:
            self.logger.error("ShizukuClient: Service not connected.")
            return False
        try:
            cb = ShizukuClient._StreamCallback(on_stdout, on_stderr, on_done)
            _stream_callbacks.add(cb)
            self.i_user_service.execStream(command, cb)
            return True
        except Exception as e:
            self.logger.error(f"ShizukuClient: exec_stream failed")
            self.logger.error(e)
            return False

    def fs_stat(self, path: str):
        """Get file/directory statistics.

        Args:
            path (str): The file or directory path.

        Returns:
            FsStatResult or None: A FsStatResult object containing file statistics if successful, None otherwise.
        """
        if not self.i_user_service:
            return None
        try:
            st = self.i_user_service.fsStat(path)
            if not st:
                return None
            return FsStatResult(
                exists=bool(st.exists),
                isDir=bool(st.isDir),
                size=int(st.size or 0),
                mtime=int(st.mtime or 0),
                mode=st.mode,
                uid=st.uid,
                gid=st.gid,
            )
        except Exception as e:
            self.logger.error(f"fs_stat error: {e}")
            return None

    def fs_list(self, path: str) -> list[str]:
        """List files and directories in the given path.

        Args:
            path (str): The directory path to list.

        Returns:
            list[str]: A list of file/directory names in the path, empty list if error or path not accessible.
        """
        if not self.i_user_service:
            return []
        try:
            arr = self.i_user_service.fsList(path)
            if arr is not None:
                return [str(s) for s in arr]
            return []
        except Exception as e:
            self.logger.error(f"fs_list error: {e}")
            return []

    def fs_read(self, path: str, decode_b64: bool = True):
        """Read file content from the given path.

        Args:
            path (str): The file path to read.
            decode_b64 (bool): Whether to decode base64 content. Defaults to True.

        Returns:
            bytes or str or None: File content as bytes if base64 and decoded,
                as base64 string if base64 and not decoded, as text if not base64,
                or None if error.
        """
        if not self.i_user_service:
            return None
        try:
            res = self.i_user_service.fsRead(path)
            if res is None:
                return None
            is_b64 = bool(res.isBase64)
            if is_b64:
                data = bytes(res.bytes or b'')
                if decode_b64:
                    return data
                return 'b64:' + base64.b64encode(data).decode('ascii')
            return res.text
        except Exception as e:
            self.logger.error(f"fs_read error: {e}")
            return None

    def fs_write(self, path: str, data, append: bool = False) -> bool:
        """Write data to a file.

        Args:
            path (str): The file path to write to.
            data (str or bytes): The data to write.
            append (bool): Whether to append to existing file. Defaults to False.

        Returns:
            bool: True if write successful, False otherwise.
        """
        if not self.i_user_service:
            return False
        try:
            # Binder 对单次事务有大小限制，统一按二进制分块写入（base64 包裹）
            BIN_CHUNK_BYTES = 256 * 1024  # 256KB 原始二进制，base64 后约 ~342KB

            if isinstance(data, (bytes, bytearray)):
                bytes_data = bytes(data)
            else:
                # 将任意可写入的数据转为 UTF-8 字节
                bytes_data = str(data).encode('utf-8')

            total_len = len(bytes_data)
            if total_len <= BIN_CHUNK_BYTES:
                payload = 'b64:' + base64.b64encode(bytes_data).decode('ascii')
                self.i_user_service.fsWrite(path, payload, bool(append))
                return True

            # 分块写入：首块使用传入的 append，其余强制追加
            first_append = bool(append)
            offset = 0
            while offset < total_len:
                chunk = bytes_data[offset:offset + BIN_CHUNK_BYTES]
                payload = 'b64:' + base64.b64encode(chunk).decode('ascii')
                self.i_user_service.fsWrite(path, payload, first_append)
                first_append = True
                offset += len(chunk)
            return True
        except Exception as e:
            self.logger.error(f"fs_write error: {e}")
            return False

    def fs_delete(self, path: str, recursive: bool = False) -> bool:
        """Delete a file or directory.

        Args:
            path (str): The file or directory path to delete.
            recursive (bool): Whether to delete directories recursively. Defaults to False.

        Returns:
            bool: True if deletion successful, False otherwise.
        """
        if not self.i_user_service:
            return False
        try:
            self.i_user_service.fsDelete(path, bool(recursive))
            return True
        except Exception as e:
            self.logger.error(f"fs_delete error: {e}")
            return False

    def fs_mkdirs(self, path: str) -> bool:
        """Create directories recursively.

        Args:
            path (str): The directory path to create.

        Returns:
            bool: True if creation successful, False otherwise.
        """
        if not self.i_user_service:
            return False
        try:
            self.i_user_service.fsMkdirs(path)
            return True
        except Exception as e:
            self.logger.error(f"fs_mkdirs error: {e}")
            return False

    def fs_move(self, src: str, dst: str, replace: bool = False) -> bool:
        """Move or rename a file/directory.

        Args:
            src (str): The source file/directory path.
            dst (str): The destination file/directory path.
            replace (bool): Whether to replace existing destination. Defaults to False.

        Returns:
            bool: True if move successful, False otherwise.
        """
        if not self.i_user_service:
            return False
        try:
            self.i_user_service.fsMove(src, dst, bool(replace))
            return True
        except Exception as e:
            self.logger.error(f"fs_move error: {e}")
            return False

    def pm_install(self, apk_path: str) -> bool:
        """Install an APK package.

        Args:
            apk_path (str): The path to the APK file to install.

        Returns:
            bool: True if installation successful, False otherwise.
        """
        if not self.i_user_service:
            return False
        try:
            self.i_user_service.pmInstall(apk_path)
            return True
        except Exception as e:
            self.logger.error(f"pm_install error: {e}")
            return False

    def pm_uninstall(self, package_name: str) -> bool:
        """Uninstall an APK package.

        Args:
            package_name (str): The package name to uninstall.

        Returns:
            bool: True if uninstallation successful, False otherwise.
        """
        if not self.i_user_service:
            return False
        try:
            self.i_user_service.pmUninstall(package_name)
            return True
        except Exception as e:
            self.logger.error(f"pm_uninstall error: {e}")
            return False