import random
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame, QVBoxLayout
from qfluentwidgets import FluentIcon as FIF, FluentWindow, TextEdit

# TODO: 在下方docs中编写文档
# content里写说明，注意，需要使用HTML的形式给到样式，不给样式就是纯文字
# 使用Markdown请先转换成HTML
docs = [
    {
        'title': '主线任务配置说明',
        'content': '主线任务配置说明'
    },
    {
        'title': '困难任务配置说明',
        'content': '困难任务配置说明'
    }
]


class ReadMeInterface(QFrame):
    def __init__(self, content: str):
        super().__init__()
        self.setObjectName('ReadMeInterface' + random.randint(0, 100000).__str__())
        self.setStyleSheet('QFrame#ReadMeInterface{background: white}')
        self.content = content
        self.textField = TextEdit()
        self.textField.setReadOnly(True)
        self.textField.setPlainText(content)
        vBox = QVBoxLayout(self)
        vBox.addWidget(self.textField)
        self.setLayout(vBox)


class ReadMeWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.titles = ['主线任务配置说明', '困难任务配置说明']
        for doc in docs:
            self.addSubInterface(interface=ReadMeInterface(doc['content']), icon=FIF.TAG, text=doc['title'])
        self.show()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QFrame

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    window = ReadMeWindow()
    sys.exit(app.exec_())
