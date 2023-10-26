from PyQt5.QtWidgets import QWidget

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(120)

