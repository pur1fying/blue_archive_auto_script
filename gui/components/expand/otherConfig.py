from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import SwitchButton, PushButton

from .expandTemplate import TemplateLayout


def fhx():
    # To do: 反和谐功能添加
    pass


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '一键反和谐',
                'type': 'button',
                'selection': fhx,
                'key': None
            },
            {
                'label': '显示首页头图（下次启动时生效）',
                'type': 'switch',
                'key': 'bannerVisibility'
            }
        ]

        super().__init__(parent=parent, configItems=configItems)
