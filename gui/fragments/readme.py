import random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout
from qfluentwidgets import FluentIcon as FIF, FluentWindow, TextEdit
import os

from gui.util.translator import baasTranslator as bt


class ReadMeInterface(QFrame):
    def __init__(self, content: str):
        super().__init__()
        self.setObjectName('ReadMeInterface' + random.randint(0, 100000).__str__())
        self.setStyleSheet('QFrame#ReadMeInterface{background: white}')
        self.content = content
        self.textEdit = TextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setHtml(content)
        vBox = QVBoxLayout(self)
        vBox.addWidget(self.textEdit)
        self.setLayout(vBox)


class ReadMeWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        docs = []

        path = self.getPath()
        for file in os.listdir(path):
            filepath = os.path.join(path, file)
            filename = file.split('.')[0]
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                docs.append({'title': filename, 'content': content})

        for doc in docs:
            self.addSubInterface(interface=ReadMeInterface(doc['content']), icon=FIF.TAG, text=doc['title'])
        self.show()

    def getPath(self):
        directory = f'./src/descriptions/{bt.stringLang}'
        if os.path.isdir(directory):
            return directory

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QFrame

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    window = ReadMeWindow()
    sys.exit(app.exec_())
