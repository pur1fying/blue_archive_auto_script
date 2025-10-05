from typing import TYPE_CHECKING

from jnius import autoclass, PythonJavaClass, java_method, cast
# from android import activity, mActivity

from .util import main_activity, show_toast
if TYPE_CHECKING:
    from core import Baas_thread

_listeners = set()
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

def is_available() -> bool:
    """判断 Shizuku 类是否可用。"""
    return Shizuku is not None


def is_pre_v11() -> bool:
    """是否为 Shizuku v11 之前版本（不支持动态申请权限）。"""
    try:
        return bool(Shizuku.isPreV11())
    except Exception:
        # 若方法不存在，默认视为支持动态申请
        return False


def check_permission() -> bool:
    """
    判断是否拥有 Shizuku 的 adb shell 权限。
    """
    try:
        return Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
    except Exception:
        return False


def request_permission(activity=None, request_code: int = PERMISSION_CODE_DEFAULT):
    """
    动态申请 Shizuku 权限。
    - 若已授权，提示“已拥有权限”。
    - 若 Shizuku 版本过低（pre v11），提示不支持动态申请。
    - 否则发起权限请求。
    """
    if check_permission():
        show_toast('已拥有权限', activity)
        return

    if is_pre_v11():
        show_toast('当前shizuku版本不支持动态申请', activity)
        return

    Shizuku.requestPermission(int(request_code))


class _PermissionResultListener(PythonJavaClass):
    """
    Shizuku 权限结果监听代理。
    对应 Java 接口：Shizuku.OnRequestPermissionResultListener
    """

    __javainterfaces__ = [_LISTENER_IFACE_JNI]
    __javacontext__ = 'app'

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    # 签名: void onRequestPermissionResult(int requestCode, int grantResult)
    @java_method('(II)V')
    def onRequestPermissionResult(self, requestCode, grantResult):
        try:
            if callable(self._callback):
                self._callback(int(requestCode), int(grantResult))
        except Exception:
            # 回调异常不应影响主流程
            pass


def add_request_permission_result_listener(callback):
    """
    添加权限申请结果监听。
    返回监听实例，供后续移除使用。
    """
    listener = _PermissionResultListener(callback)
    Shizuku.addRequestPermissionResultListener(listener)
    _listeners.add(listener)
    return listener


def remove_request_permission_result_listener(listener) -> None:
    """移除指定的权限申请结果监听器。"""
    try:
        Shizuku.removeRequestPermissionResultListener(listener)
    finally:
        if listener in _listeners:
            _listeners.remove(listener)


class ShizukuClient:
    def __init__(self, logger: 'Baas_thread.Logger'):
        activity = main_activity()
        if not activity:
            logger.error("ShuzikuClient: cannot load main activity.")
            return
        self.context = activity.getApplicationContext()
        self.i_user_service = None
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
        if not Shizuku:
            self.logger.error("ShizukuClient: Shizuku classes not found.")
            return False

        # 检查 Shizuku 权限
        if Shizuku.checkSelfPermission() != 0: # 0 is PERMISSION_GRANTED
            self.logger.warning("ShizukuClient: Shizuku permission not granted. Requesting...")
            Shizuku.requestPermission(0) # 0 is a request code
            self.show_toast("Please grant Shizuku permission.")
            return False

        self.logger.info("ShizukuClient: Binding Shizuku user service...")
        try:
            Shizuku.bindUserService(self.user_service_args, self.service_connection)
            return True
        except Exception as e:
            self.logger.error(f"ShizukuClient: Failed to bind service: {e}")
            return False

    def disconnect(self):
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

    def execute_command(self, command):
        if not self.i_user_service:
            self.logger.error("ShizukuClient: Service not connected.")
            self.show_toast("Service not connected.")
            return False, "Error: Service not connected."
        try:
            self.logger.info(f"ShizukuClient: Executing command: {command}")
            result = self.i_user_service.exec(command)
            self.logger.info(f"ShizukuClient: Result: {result}")
            return True, result
        except Exception as e:
            self.logger.error(f"ShizukuClient: Command execution failed: {e}")
            return False, f"Error: {e}"
            
    def show_toast(self, text):
        show_toast(text, self.context)