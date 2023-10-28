# coding:utf-8
import sys

sys.path.append('./')
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF, SplashScreen
from qfluentwidgets import (NavigationItemPosition, FluentWindow,
                            SubtitleLabel, setFont, setThemeColor)

ICON_DIR = 'gui/assets/logo.png'


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        self.show()

        setThemeColor('#0078d4')

        # create sub interface
        from gui.fragments.home import HomeFragment
        from gui.fragments.process import ProcessFragment
        from gui.fragments.switch import SwitchFragment
        from gui.fragments.settings import SettingsFragment

        self.homeInterface = HomeFragment(parent=self)
        self.schedulerInterface = SwitchFragment()
        self.processInterface = ProcessFragment()
        self.settingInterface = SettingsFragment()

        self.initNavigation()
        self.splashScreen.finish()

    def call_update(self):
        self.schedulerInterface.update_settings()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页')

        self.navigationInterface.addSeparator()
        self.addSubInterface(self.schedulerInterface, FIF.CALENDAR, '调度器')
        self.addSubInterface(self.processInterface, FIF.CALORIES, '调度状态')

        # add custom widget to bottom
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.setFixedSize(900, 700)
        self.setWindowIcon(QIcon(ICON_DIR))
        self.setWindowTitle('BlueArchiveAutoScript')

        desktop = QApplication.desktop().availableGeometry()
        _w, _h = desktop.width(), desktop.height()
        self.move(_w // 2 - self.width() // 2, _h // 2 - self.height() // 2)

    def closeEvent(self, event):
        super().closeEvent(event)


def start():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()


if __name__ == '__main__':
    # pa=Main()
    # pa._init_emulator()
    # pa.solve("arena")

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()

# if __name__ == '__main__':
# print(datetime.now())
# s = Scheduler()
# p = s.log('test')
# print(p)
# p = sorted(p, key=lambda x: x['next_tick'])
# print(p)
