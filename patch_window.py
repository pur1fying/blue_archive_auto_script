# coding:utf-8

import os
import sys
import runpy
import functools
from typing import Any, Callable, Type

import qtpy
import qtpy.QtCore
import qtpy.QtGui
import qtpy.QtWidgets


def monkey_patch(cls: Type, attr_name: str) -> Callable[[Callable], Callable]:
    """
    一个用于简化猴子补丁类方法的装饰器。

    用法:
    @monkey_patch(MyClass, 'my_method')
    def my_patched_method(original_method, self, *args, **kwargs):
        # 执行一些操作
        result = original_method(self, *args, **kwargs)
        # 执行另一些操作
        return result
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


# --- Run original window.py entry ---
if __name__ == '__main__':
    # 保持与原始相对导入一致
    sys.path.append('./')
    runpy.run_path(os.path.join(os.path.dirname(__file__), 'window.py'), run_name='__main__')
