# coding:utf-8
import json
import os
import sys

from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF, SplashScreen, MSFluentWindow, TabBar, \
    MSFluentTitleBar
from qfluentwidgets import (SubtitleLabel, setFont, setThemeColor)

from core import default_config

# sys.stderr = open('error.log', 'w+', encoding='utf-8')
# sys.stdout = open('output.log', 'w+', encoding='utf-8')
sys.path.append('./')

# Offer the error to the error.log
ICON_DIR = 'gui/assets/logo.png'


def update_config_reserve_old(config_old, config_new):  # 保留旧配置原有的键，添加新配置中没有的，删除新配置中没有的键
    for key in config_new:
        if key == 'TacticalChallengeShopList':
            if len(config_old[key]) == 13:
                config_old[key] = config_new[key]
            continue
        if key not in config_old:
            config_old[key] = config_new[key]
    dels = []
    for key in config_old:
        if key not in config_new:
            dels.append(key)
    for key in dels:
        del config_old[key]
    return config_old


def update_config_overwrite(config_old, config_new):  # 用新配置覆盖旧配置
    for key in config_new:
        config_old[key] = config_new[key]
    return config_old


def check_static_config():
    if not os.path.exists('./config/static.json'):
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
            return
    try:
        with open('./config/static.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = update_config_overwrite(data, json.loads(default_config.STATIC_DEFAULT_CONFIG))
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return
    except Exception as e:
        print(e)
        os.remove('./config/static.json')
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
        return


def check_user_config():
    if not os.path.exists('./config/config.json'):
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
            return
    try:
        with open('./config/config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = update_config_reserve_old(data, json.loads(default_config.DEFAULT_CONFIG))
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return
    except Exception as e:
        print(e)
        os.remove('./config/config.json')
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
        return


def check_event_config():
    if not os.path.exists('./config/event.json'):  # 如果不存在event.json则创建
        with open('./config/event.json', 'w', encoding='utf-8') as f:
            f.write(default_config.EVENT_DEFAULT_CONFIG)  # 写入默认配置
            return
    try:
        with open('./config/event.json', 'r', encoding='utf-8') as f:  # 如果存在则检查是否有新的配置项
            data = json.load(f)
        default_config.EVENT_DEFAULT_CONFIG = json.loads(default_config.EVENT_DEFAULT_CONFIG)
        for i in range(0, len(default_config.EVENT_DEFAULT_CONFIG)):
            exist = False
            for j in range(0, len(data)):
                if data[j]['func_name'] == default_config.EVENT_DEFAULT_CONFIG[i]['func_name']:
                    exist = True
                    break
            if not exist:
                data.insert(i, default_config.EVENT_DEFAULT_CONFIG[i])
        with open('./config/event.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(e)
        os.remove('./config/event.json')
        with open('./config/event.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(json.loads(default_config.EVENT_DEFAULT_CONFIG), ensure_ascii=False, indent=2))
        return


def check_config():
    if not os.path.exists('./config'):
        os.mkdir('./config')
    check_static_config()
    check_user_config()
    check_event_config()

    # 每次都要重新生成
    with open('./config/display.json', 'w', encoding='utf-8') as f:
        f.write(default_config.DISPLAY_DEFAULT_CONFIG)
    with open('./config/switch.json', 'w', encoding='utf-8') as f:
        f.write(default_config.SWITCH_DEFAULT_CONFIG)


class Widget(MSFluentWindow):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class CustomTitleBar(MSFluentTitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)

        # add buttons
        self.toolButtonLayout = QHBoxLayout()
        self.hBoxLayout.insertLayout(4, self.toolButtonLayout)

        # add tab bar
        self.tabBar = TabBar(self)

        self.tabBar.setMovable(True)
        self.tabBar.setTabMaximumWidth(120)
        self.tabBar.setTabShadowEnabled(False)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabSelectedBackgroundColor(QColor(255, 255, 255, 125), QColor(255, 255, 255, 50))

        self.tabBar.tabCloseRequested.connect(self.tabBar.removeTab)

        self.hBoxLayout.insertWidget(5, self.tabBar, 1)
        self.hBoxLayout.setStretch(6, 0)

        # self.hBoxLayout.insertSpacing(8, 20)

    def canDrag(self, pos: QPoint):
        if not super().canDrag(pos):
            return False
        pos.setX(pos.x() - self.tabBar.x())
        return not self.tabBar.tabRegion().contains(pos)


class Window(MSFluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        self.setTitleBar(CustomTitleBar(self))
        self.tabBar = self.titleBar.tabBar
        self.show()

        setThemeColor('#0078d4')

        # create sub interface
        from gui.fragments.home import HomeFragment
        from gui.fragments.switch import SwitchFragment
        from gui.fragments.settings import SettingsFragment

        self.homeInterface = HomeFragment(parent=self)
        self.schedulerInterface = SwitchFragment(parent=self)
        # self.processInterface = ProcessFragment()
        self.settingInterface = SettingsFragment(parent=self)

        self.initNavigation()
        self.dispatchWindow()
        self.splashScreen.finish()

    def call_update(self):
        self.schedulerInterface.update_settings()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页')
        # self.navigationInterface.addSeparator()
        self.addSubInterface(self.schedulerInterface, FIF.CALENDAR, '调度器')
        # add custom widget to bottom
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置')
        # Add some tabs in the group
        self.addTab(self.homeInterface.object_name, 'home', None)
        self.addTab(self.schedulerInterface.object_name, 'scheduler', None)
        self.stackedWidget.currentChanged.connect(self.onTabChanged)
        self.tabBar.currentChanged.connect(self.onTabChanged)
        self.tabBar.tabAddRequested.connect(self.onTabAddRequested)

    def initWindow(self):
        self.resize(900, 700)
        desktop = QApplication.desktop().availableGeometry()
        _w, _h = desktop.width(), desktop.height()
        self.move(_w // 2 - self.width() // 2, _h // 2 - self.height() // 2)

    def closeEvent(self, event):
        super().closeEvent(event)

    def onTabChanged(self, _: int):
        objectName = self.tabBar.currentTab().routeKey()
        print(objectName)
        # self.stackedWidget.setCurrentWidget(self.schedulerInterface)
        # self.homeInterface.setCurrentWidget(self.findChild(self.homeInterface, objectName))
        # self.stackedWidget.setCurrentWidget(self.homeInterface)

    def onTabAddRequested(self):
        text = f'硝子酱一级棒卡哇伊×{self.tabBar.count()}'
        self.addTab(text, text, 'resource/Smiling_with_heart.png')

    def addTab(self, routeKey, text, icon):
        self.tabBar.addTab(routeKey, text, icon)
        # self.homeInterface.addWidget(TabInterface(text, icon, routeKey, self))

    def dispatchWindow(self):
        self.setWindowIcon(QIcon(ICON_DIR))
        self.setWindowTitle('BlueArchiveAutoScript')


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
    check_config()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    # 聚焦窗口
    w.setFocus(True)
    w.show()
    app.exec_()

# if __name__ == '__main__':
# print(datetime.now())
# s = Scheduler()
# p = s.log('test')
# print(p)
# p = sorted(p, key=lambda x: x['next_tick'])
# print(p)
