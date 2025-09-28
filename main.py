import json
import os

from core.ocr import ocr
from core.utils import Logger
from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet
from core.ocr.baas_ocr_client.server_installer import check_git

class Main:
    def __init__(self, logger_signal=None, ocr_needed=None):
        self.ocr_needed = ocr_needed
        self.ocr = None
        self.logger = Logger(logger_signal)
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        self.logger.info(self.project_dir)
        self.init_all_data()
        self.threads = {}

    def init_all_data(self):
        if not self.init_ocr():
            self.logger.error("Ocr Init Incomplete Please restart .")
            return
        self.init_static_config()
        self.logger.info("-- All Data Initialization Complete Script ready--")

    def init_ocr(self):
        try:
            check_git(self.logger)
        except Exception as e:
            self.logger.error("OCR Update Failed.")
            import traceback
            self.logger.error(traceback.format_exc())
            self.logger.info("Try to Start OCR Server Without Update.")

        try:
            self.ocr = ocr.Baas_ocr(logger=self.logger, ocr_needed=self.ocr_needed)
            self.ocr.client.start_server()
            return True
        except Exception as e:
            self.logger.error(e.__str__())
            return False

    def get_thread(
            self,
            config,
            name="1",
            logger_signal=None,
            button_signal=None,
            update_signal=None,
            exit_signal=None
    ):
        t = Baas_thread(config, logger_signal, button_signal, update_signal, exit_signal)
        t.set_ocr(self.ocr)
        self.threads.setdefault(name, t)
        return t

    def stop_script(self, name):
        if name in self.threads:
            self.threads[name].flag_run = False
            del self.threads[name]
            return True
        else:
            return False

    def init_static_config(self):
        try:
            self.static_config = self.operate_dict(
                json.load(open(self.project_dir + "/config/static.json", 'r', encoding='utf-8')))
            return True
        except Exception as e:
            self.logger.error("Static Config initialization failed")
            self.logger.error(e.__str__())
            return False

    def operate_dict(self, dic):
        for key in dic:
            if type(dic[key]) is dict:
                dic[key] = self.operate_dict(dic[key])
            else:
                dic[key] = self.operate_item(dic[key])
        return dic

    def is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def operate_item(self, item):
        if type(item) is int or type(item) is bool or type(item) is float or item is None:
            return item
        if type(item) is str:
            if item.isdigit():
                return int(item)
            elif self.is_float(item):
                return float(item)
            else:
                if item.count(",") == 2:
                    temp = item.split(",")
                    for j in range(0, len(temp)):
                        if temp[j].isdigit():
                            temp[j] = int(temp[j])
                    item = temp
                return item
        else:
            temp = []
            for i in range(0, len(item)):
                if type(item[i]) is dict:
                    temp.append(self.operate_dict(item[i]))
                else:
                    temp.append(self.operate_item(item[i]))
            return temp


if __name__ == '__main__':
    ocr_needed = ["en-us"]
    INSTANCE = Main(ocr_needed=ocr_needed)
    config = ConfigSet(config_dir="1708232489")
    bThread = Baas_thread(config, None, None, None)
    bThread.set_ocr(INSTANCE.ocr)
    bThread.init_all_data()
    # tt.update_screenshot_array()
    # for i in range(0, 10):
    #     tt.ocr.get_region_res(tt, (1005, 94, 1240, 129), "ko-kr", "lesson region name")
    # exit(0)
    # from module import create
    # create.create_phase(bThread, 3)

    # create.select_node(bThread, 1)

    # print(json.dumps(res, indent=4))
    # print(len(res))
    # exit(0)
    # bThread.thread_starter()
    # bThread.solve("refresh_uiautomator2")
    # bThread.solve("explore_activity_challenge")
    # bThread.solve("activity_sweep")
    # bThread.solve("tactical_challenge_shop")
    # bThread.solve("explore_activity_mission")
    # bThread.solve("explore_activity_story")
    bThread.solve("common_shop")
    # bThread.solve("total_assault")
    # bThread.solve("cafe_reward")
    # bThread.solve("momo_talk")
    # bThread.solve("explore_normal_task")
    # bThread.solve("explore_hard_task")
    # bThread.solve("normal_task")
    # bThread.solve("hard_task")
    # bThread.solve("arena")
    # bThread.solve("lesson")
    # bThread.solve("group")
    # bThread.solve("mail")
    # bThread.solve("collect_reward")
    # bThread.solve("main_story")
    # bThread.solve("group_story")
    # bThread.solve("mini_story")
    # bThread.solve("clear_special_task_power")
    # bThread.solve("scrimmage")
    # bThread.solve("rewarded_task")
    # bThread.solve("create")
    # bThread.solve("dailyGameActivity")
    # bThread.solve("friend")
    bThread.solve("joint_firing_drill")

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

if __name__ == '__main__':
    # 保持与原始相对导入一致
    sys.path.append('./')
    pwd = os.path.dirname(__file__)
    if os.path.exists(os.path.join(pwd, 'window.py')):
        path = os.path.join(pwd, 'window.py')
    elif os.path.exists(os.path.join(pwd, 'window.pyc')):
        path = os.path.join(pwd, 'window.pyc')
    else:
        raise FileNotFoundError('window.py or window.pyc not found')
    runpy.run_path(path, run_name='__main__')
