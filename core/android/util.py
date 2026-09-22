from traceback import print_exc

from . import classes as android_classes

_main = None

def main_activity():
    """
    获取主 Activity。

    !! 注意，必须在 Python 入口侧至少调用一次这个函数 !!  
    因为 Python 侧非主线程无法获取到任何 APK 内的类

    :return: 如果获取失败，返回 None
    """
    global _main
    if _main is None:
        try:
            MainActivity = android_classes.MainActivity
            if MainActivity is None:
                return None
            _main = MainActivity.mActivity
        except Exception:
            print_exc()
    return _main


def show_toast(message: str, activity=None):
    """
    显示 Toast 消息。

    :param message: 要显示的消息
    :param activity: Activity 实例，如果为 None 则自动获取主 Activity
    """
    ctx = activity or main_activity()
    if ctx is None:
        return
    Toast = android_classes.Toast
    if Toast is None:
        return
    Toast.makeText(ctx, message, Toast.LENGTH_SHORT).show()
