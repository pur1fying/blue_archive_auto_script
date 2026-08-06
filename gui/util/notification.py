import json

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition

from core.config.config_set import ConfigSet


def success(label: str, msg: str, config: ConfigSet, duration: int = 800) -> None:
    config.get_signal('notify_signal').emit(json.dumps({
        'type': 'success',
        'label': label,
        'msg': msg,
        'duration': duration
    }))


def error(label: str, msg: str, config: ConfigSet, duration: int = 800) -> None:
    config.get_signal('notify_signal').emit(json.dumps({
        'type': 'error',
        'label': label,
        'msg': msg,
        'duration': duration
    }))


def warning(label: str, msg: str, config: ConfigSet, duration: int = 800) -> None:
    config.get_signal('notify_signal').emit(json.dumps({
        'type': 'warning',
        'label': label,
        'msg': msg,
        'duration': duration
    }))


def saved(config: ConfigSet, label: str = None, msg: str = '', duration: int = 1200) -> None:
    """Lightweight top-right toast used after dialog OK commits a draft.

    Call _saved directly: notify_signal receivers only handle success/error/warning,
    so a custom type 'saved' would be ignored and the toast would never appear.
    """
    if label is None:
        # caller may pass already-translated text; fallback Chinese default
        label = '已保存'
    window = config.get_window() if hasattr(config, 'get_window') else None
    if window is None:
        return
    _saved(label, msg, window, duration)


def _success(label: str, msg: str, info_widget: QWidget, duration: int = 800, customized=False) -> None:
    InfoBar(
        icon=InfoBarIcon.SUCCESS,
        title=f'{label}{"设置成功" if not customized else ""}',
        content=f'{msg}',
        orient=Qt.Vertical,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()


def _error(label: str, msg: str, info_widget: QWidget, duration: int = 800, customized=False) -> None:
    InfoBar(
        icon=InfoBarIcon.ERROR,
        title=f'{label}{"设置失败" if not customized else ""}',
        content=f'{msg}',
        orient=Qt.Vertical,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()


def _warning(label: str, settled: str, info_widget: QWidget, duration: int = 800) -> None:
    InfoBar(
        icon=InfoBarIcon.WARNING,
        title='警告',
        content=f'{label}设置可能会出现问题，当前值为：{settled}',
        orient=Qt.Vertical,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()


def _saved(label: str, msg: str, info_widget: QWidget, duration: int = 1200) -> None:
    InfoBar(
        icon=InfoBarIcon.SUCCESS,
        title=label,
        content=msg or '',
        orient=Qt.Vertical,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()
