import debugpy
debugpy.listen(5678, in_process_debug_adapter=True)
print("Waiting for debugger attach...")
# debugpy.wait_for_client()

# Setup Shizuku and ADB
import core.android.classes # Load classes early
from core.android.util import main_activity
Main = main_activity()

from core.android.shizuku import request_permission
from core.android import patch_adb, ShizukuClient
from core.utils import Logger
logger = Logger(None)
shizuku = ShizukuClient(logger)
request_permission()
shizuku.connect()
patch_adb(shizuku, logger)


import sys
import types

# --- psutil mock for Android ---
class Process:
    def __init__(self, pid=None):
        if pid is not None and not isinstance(pid, int):
            raise TypeError("pid must be an integer")
        self.pid = pid

    def is_running(self):
        return False

    def children(self, recursive=False):
        return []

    def cmdline(self):
        return []

    def name(self):
        return ""

    def exe(self):
        return ""

    def info(self):
        return {'pid': self.pid, 'name': '', 'exe': '', 'cmdline': ''}


def process_iter(attrs=None, ad_value=None):
    return iter([])


def pid_exists(pid):
    return False


class Error(Exception):
    pass


class NoSuchProcess(Error):
    pass


class AccessDenied(Error):
    pass


class TimeoutExpired(Error):
    pass

psutil_mock = types.ModuleType('psutil')
psutil_mock.Process = Process
psutil_mock.process_iter = process_iter
psutil_mock.pid_exists = pid_exists
psutil_mock.Error = Error
psutil_mock.NoSuchProcess = NoSuchProcess
psutil_mock.AccessDenied = AccessDenied
psutil_mock.TimeoutExpired = TimeoutExpired

sys.modules['psutil'] = psutil_mock
sys.modules['psutil._psutil_linux'] = types.ModuleType('psutil._psutil_linux')


###########################################

import os
import sys
import runpy
import functools
from typing import Any, Callable, Type

import qtpy
import qtpy.QtCore
import qtpy.QtGui
import qtpy.QtWidgets
from qtpy.QtWidgets import QTableWidget

QTableWidget.update

def monkey_patch(cls: Type, attr_name: str) -> Callable[[Callable], Callable]:
    """
    一个用于简化猴子补丁类方法的装饰器。

    用法:
    ```python
    @monkey_patch(MyClass, 'my_method')
    def my_patched_method(original_method, self, *args, **kwargs):
        # 执行一些操作
        result = original_method(self, *args, **kwargs)
        # 执行另一些操作
        return result
    ```
    """
    def decorator(patch_func: Callable) -> Callable:
        original_func = getattr(cls, attr_name)

        @functools.wraps(patch_func)
        def wrapper(*args, **kwargs) -> Any:
            return patch_func(original_func, *args, **kwargs)

        setattr(cls, attr_name, wrapper)
        return wrapper
    return decorator

# --- Monkey patch 1: QApplication shim and PyQt5 aliasing ---

OriginalQApplication = qtpy.QtWidgets.QApplication
_app = qtpy.QtWidgets.QApplication(sys.argv)
if _app is None:
    _app = OriginalQApplication(sys.argv)

class PatchedQApplication(OriginalQApplication):
    def __new__(cls, *args, **kwargs):
        return _app

    @staticmethod
    def exec(*args, **kwargs):
        return OriginalQApplication.exec()

qtpy.QtCore.pyqtSignal = qtpy.QtCore.Signal
qtpy.QtCore.QRegExp = qtpy.QtCore.QRegularExpression
qtpy.QtCore.pyqtProperty = qtpy.QtCore.Property
qtpy.QtCore.pyqtSlot = qtpy.QtCore.Slot
qtpy.QtGui.QRegExpValidator = qtpy.QtGui.QRegularExpressionValidator
qtpy.QtWidgets.qApp = _app
qtpy.QtWidgets.QApplication = PatchedQApplication
qtpy.QtWidgets.QApplication.desktop = lambda: qtpy.QtGui.QGuiApplication.primaryScreen()
sys.modules['PyQt5'] = qtpy
sys.modules['PyQt5.QtCore'] = qtpy.QtCore
sys.modules['PyQt5.QtGui'] = qtpy.QtGui
sys.modules['PyQt5.QtWidgets'] = qtpy.QtWidgets


# --- Monkey patch 2: MSFluentWindow.addSubInterface button disconnect compatibility ---
from qfluentwidgets import MSFluentWindow

@monkey_patch(MSFluentWindow, 'addSubInterface')
def patch_addSubInterface(addSubInterface, self, *args, **kwargs):
    btn = addSubInterface(self, *args, **kwargs)
    try:
        _orig_btn_disconnect = getattr(btn, 'disconnect', None)
    except Exception:
        _orig_btn_disconnect = None

    def _btn_disconnect_compat(*a, **kw):
        if callable(_orig_btn_disconnect):
            try:
                return _orig_btn_disconnect(*a, **kw)
            except TypeError:
                pass
        for _sig_name in ("clicked", "pressed", "released", "toggled"):
            try:
                _sig = getattr(btn, _sig_name, None)
                if _sig is not None:
                    try:
                        _sig.disconnect()
                    except Exception:
                        pass
            except Exception:
                pass
        return None

    try:
        setattr(btn, 'disconnect', _btn_disconnect_compat)
    except Exception:
        pass
    return btn


# --- Monkey patch 3: QWidget.setFocus accept PyQt5-style bool ---
@monkey_patch(qtpy.QtWidgets.QWidget, 'setFocus')
def patch_setFocus(setFocus, self, *args, **kwargs):
    if len(args) == 1 and isinstance(args[0], bool):
        return setFocus(self)
    return setFocus(self, *args, **kwargs)


# --- Monkey patch 4: onNavigationChanged ---
@monkey_patch(MSFluentWindow, '__init__')
def patch_init(__init__, self, *args, **kwargs):
    __init__(self, *args, **kwargs)
    if hasattr(self, 'onNavigationChanged'):
        original_onNavigationChanged = self.onNavigationChanged

        @functools.wraps(original_onNavigationChanged)
        def patched_onNavigationChanged(*p_args, **p_kwargs):
            return original_onNavigationChanged(p_args[0])

        self.onNavigationChanged = patched_onNavigationChanged

@monkey_patch(QTableWidget, 'update')
def patch_QTableWidget_update(update, self, *args, **kwargs):
    # 如果没有传入参数，说明调用者想要的是 QWidget.update() (重绘整个控件)
    if not args and not kwargs:
        # 显式调用基类 QWidget 的 update 方法，避开 PySide6 的重载歧义
        return qtpy.QtWidgets.QWidget.update(self)
    
    # 如果有参数 (例如 QModelIndex)，则调用原始方法 (即 QAbstractItemView.update(index))
    return update(self, *args, **kwargs)

# import sys
# import debugpy
# debugpy.listen(5678, in_process_debug_adapter=True)
# # print("Waiting for debugger attach...")
# # debugpy.wait_for_client()

# from core.android.shizuku import add_request_permission_result_listener, request_permission, check_permission
# from core.android import patch_adb, ShizukuClient
# from core.utils import Logger
# logger = Logger(None)
# shizuku = ShizukuClient(logger)
# request_permission()
# shizuku.connect()
# patch_adb(shizuku, logger)

# import time
# time.sleep(3)

# import uiautomator2 as u2
# from core.device.uiautomator2_client import BAAS_U2_Initer
# d = u2.connect('baas')
# # d._force_reset_uiautomator_v2()
# # init = BAAS_U2_Initer(d._adb_device, logger)
# # init.install()

# print('Swipe')
# d.screenshot()
# d.swipe(0.5, 0, 0.5, 0.7, 3)
# print('Swipe End')

# time.sleep(5)
# 1. 获取必要的 Java 类
# from jnius import autoclass

# JString = autoclass('java.lang.String')
# JRuntimeException = autoclass('java.lang.RuntimeException')
# JThread = autoclass('java.lang.Thread')

# # 2. 创建一个 Java 异常对象
# j_exception = JRuntimeException(JString('456'))

# # 3. 获取当前线程
# current_thread = JThread.currentThread()

# # 4. 获取我们在 ExtendedPythonActivity 中注册的 Handler
# handler = current_thread.getUncaughtExceptionHandler()

# # 5. 直接把异常“塞”给 Handler，触发跳转页面
# handler.uncaughtException(current_thread, j_exception)

if __name__ == '__main__':
    sys.path.append('./')
    pwd = os.path.dirname(__file__)
    if os.path.exists(os.path.join(pwd, 'window.py')):
        path = os.path.join(pwd, 'window.py')
    elif os.path.exists(os.path.join(pwd, 'window.pyc')):
        path = os.path.join(pwd, 'window.pyc')
    else:
        raise FileNotFoundError('window.py or window.pyc not found')
    runpy.run_path(path, run_name='__main__')