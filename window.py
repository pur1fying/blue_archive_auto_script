# coding:utf-8
import os
import sys
import json
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF, SplashScreen
from qfluentwidgets import (FluentWindow, SubtitleLabel, setFont, setThemeColor)

from core import default_config

# sys.stderr = open('error.log', 'w+', encoding='utf-8')
# sys.stdout = open('output.log', 'w+', encoding='utf-8')
sys.path.append('./')

# Offer the error to the error.log
ICON_DIR = 'gui/assets/logo.png'


def update_config_reserve_old(config_old, config_new):  # 保留旧配置原有的键，添加新配置中没有的，删除新配置中没有的键
    if type(config_old) is not dict:
        return config_new
    for key in config_new:
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
    if type(config_old) is not dict:
        return config_new
    for key in config_new:
        config_old[key] = config_new[key]
    return config_old


def check_static_config():
    if not os.path.exists('./config/static.json'):
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
            return
    with open('./config/static.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = update_config_overwrite(data, json.loads(default_config.STATIC_DEFAULT_CONFIG))
    with open('./config/static.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return


def check_user_config():
    if not os.path.exists('./config/config.json'):
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
            return
    with open('./config/config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = update_config_reserve_old(data, json.loads(default_config.DEFAULT_CONFIG))
    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return


def check_event_config():
    if not os.path.exists('./config/event.json'):   # 如果不存在event.json则创建
        with open('./config/event.json', 'w', encoding='utf-8') as f:
            f.write(default_config.EVENT_DEFAULT_CONFIG)  # 写入默认配置
            return
    with open('./config/event.json', 'r', encoding='utf-8') as f:  # 如果存在则检查是否有新的配置项
        data = json.load(f)
    if type(data) is not list:  # event应该是list，不是则其重置为默认配置
        data = default_config.EVENT_DEFAULT_CONFIG
    else:
        default_config.EVENT_DEFAULT_CONFIG = json.loads(default_config.EVENT_DEFAULT_CONFIG)
        for i in range(0, len(default_config.EVENT_DEFAULT_CONFIG)):
            exist = False
            for j in range(0, len(data)):
                if data[j]['func_name'] == default_config.EVENT_DEFAULT_CONFIG[i]['func_name']:
                    exist = True
                    break
            if not exist:
                data.append(default_config.EVENT_DEFAULT_CONFIG[i])

    with open('./config/event.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
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
        from gui.fragments.switch import SwitchFragment
        from gui.fragments.settings import SettingsFragment

        self.homeInterface = HomeFragment(parent=self)
        self.schedulerInterface = SwitchFragment(parent=self)
        # self.processInterface = ProcessFragment()
        self.settingInterface = SettingsFragment(parent=self)

        self.initNavigation()
        self.splashScreen.finish()

    def call_update(self):
        self.schedulerInterface.update_settings()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页')

        self.navigationInterface.addSeparator()
        self.addSubInterface(self.schedulerInterface, FIF.CALENDAR, '调度器')

        # add custom widget to bottom
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置')

    def initWindow(self):
        self.resize(900, 700)
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
