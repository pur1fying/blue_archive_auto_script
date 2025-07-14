import time
from hashlib import md5
from random import random

from PyQt5.QtWidgets import QFrame

from window import Window


class GlobalFragment(QFrame):

    def __init__(self, parent: Window = None):
        super(GlobalFragment, self).__init__(parent=parent)
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f"{self.object_name}.GlobalFragment")
        self.__initialized__ = False

    def lazy_init(self):
        if self.__initialized__: return
        self.__initialized__ = True
        # TODO: Put your actual initialization code here
