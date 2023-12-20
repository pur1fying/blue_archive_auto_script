# coding:utf-8
from PyQt5.QtCore import pyqtSignal
from qfluentwidgets import TextEdit


class LoggerBox:

    def __init__(self, container, parent=None):
        logger_box_sigal = pyqtSignal(str)
        super().__init__()
        self.lineEdit = TextEdit(parent)
        # self.lineEdit.resize(200, 220)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName("loggerBox")
        container.addWidget(self.lineEdit)
