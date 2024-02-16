from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition


def success(label: str, msg: str, info_widget: QWidget, duration: int = 800) -> None:
    InfoBar(
        icon=InfoBarIcon.SUCCESS,
        title=f'{label}设置成功',
        content=f'{msg}',
        orient=Qt.Vertical,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()


def error(label: str, msg: str, info_widget: QWidget, duration: int = 800) -> None:
    InfoBar(
        icon=InfoBarIcon.ERROR,
        title=f'{label}设置失败',
        content=f'{msg}',
        orient=Qt.Vertical,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()


def warning(label: str, settled: str, info_widget: QWidget, duration: int = 800) -> None:
    InfoBar(
        icon=InfoBarIcon.WARNING,
        title='警告',
        content=f'{label}设置可能会出现问题，当前值为：{settled}',
        orient=Qt.Vertical,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
        parent=info_widget
    ).show()
