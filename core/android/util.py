from traceback import print_exc

from jnius import autoclass

Toast = autoclass('android.widget.Toast')


def main_activity():
    """
    获取主 Activity（org.kivy.android.PythonActivity，主窗口）。

    :return: 如果获取失败，返回 None
    """
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        return PythonActivity.mActivity
    except Exception:
        print_exc()
        return None


def show_toast(message: str, activity=None):
    """
    显示 Toast 消息。

    :param message: 要显示的消息
    :param activity: Activity 实例，如果为 None 则自动获取主 Activity
    """
    ctx = activity or main_activity()
    if ctx is None:
        return
    Toast.makeText(ctx, message, Toast.LENGTH_SHORT).show()
