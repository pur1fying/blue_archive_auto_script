# coding:utf-8
import datetime
import json
import os
import shutil
import sys
import threading
from functools import partial

from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF, SplashScreen, MSFluentWindow, TabBar, \
    MSFluentTitleBar, MessageBox, InfoBar, InfoBarIcon, InfoBarPosition, TransparentToolButton
from qfluentwidgets import (SubtitleLabel, setFont, setThemeColor)

from core import default_config
from gui.components.dialog_panel import SaveSettingMessageBox
from gui.fragments.readme import ReadMeWindow
from gui.util.config_set import ConfigSet

# sys.stderr = open('error.log', 'w+', encoding='utf-8')
# sys.stdout = open('output.log', 'w+', encoding='utf-8')
sys.path.append('./')

# Offer the error to the error.log
ICON_DIR = 'gui/assets/logo.png'


def update_config_reserve_old(config_old, config_new):  # 保留旧配置原有的键，添加新配置中没有的，删除新配置中没有的键
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


def check_display_config(dir_path='./default_config'):
    path = './config/' + dir_path + '/display.json'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_config.DISPLAY_DEFAULT_CONFIG)


def check_switch_config(dir_path='./default_config'):
    path = './config/' + dir_path + '/switch.json'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_config.SWITCH_DEFAULT_CONFIG)


def check_user_config(dir_path='./default_config'):
    path = './config/' + dir_path + '/config.json'
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
            return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = update_config_reserve_old(data, json.loads(default_config.DEFAULT_CONFIG))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return data['server']
    except Exception as e:
        print(e)
        os.remove(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
        return 'CN'


def check_single_event(new_event, old_event):
    for key in new_event:
        if key not in old_event:
            old_event[key] = new_event[key]
    return old_event


def check_event_config(dir_path='./default_config', server="CN"):
    path = './config/' + dir_path + '/event.json'
    default_event_config = json.loads(default_config.EVENT_DEFAULT_CONFIG)
    if server != "CN":
        for i in range(0, len(default_event_config)):
            for j in range(0, len(default_event_config[i]['daily_reset'])):
                default_event_config[i]['daily_reset'][j] = default_event_config[i]['daily_reset'][j] - 1
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            with open("error.log", 'w+', encoding='utf-8') as errorfile:
                errorfile.write("path not exist" + '\n' + dir_path + '\n' + datetime.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S') + '\n')
            f.write(json.dumps(default_event_config, ensure_ascii=False, indent=2))
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:  # 检查是否有新的配置项
            data = json.load(f)
        for i in range(0, len(default_event_config)):
            exist = False
            for j in range(0, len(data)):
                if data[j]['func_name'] == default_event_config[i]['func_name']:
                    data[j] = check_single_event(default_event_config[i], data[j])
                    exist = True
                    break
            if not exist:
                data.insert(i, default_event_config[i])
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        with open("error.log", 'w+', encoding='utf-8') as f:
            f.write(str(e) + '\n' + dir_path + '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(default_event_config, ensure_ascii=False, indent=2))
        return


def check_config(dir_path):
    if not os.path.exists('./config'):
        os.mkdir('./config')
    check_static_config()
    if type(dir_path) is not list:
        dir_path = [dir_path]
    for path in dir_path:
        if not os.path.exists('./config/' + path):
            os.mkdir('./config/' + path)
        server = check_user_config(path)
        if server == "官服" or server == "B服":
            server = "CN"
        elif server == "国际服":
            server = "Global"
        elif server == "日服":
            server = "JP"
        check_event_config(path, server)
        check_display_config(path)
        check_switch_config(path)


class Widget(MSFluentWindow):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class BAASTitleBar(MSFluentTitleBar):
    """ Title bar with icon and title """
    onHelpButtonClicked = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        # add buttons
        self.toolButtonLayout = QHBoxLayout()
        self.hBoxLayout.insertLayout(4, self.toolButtonLayout)

        # add tab bar
        self.tabBar = TabBar(self)
        self.tabBar.setMovable(False)
        self.tabBar.setTabMaximumWidth(120)
        self.tabBar.setTabShadowEnabled(False)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabSelectedBackgroundColor(QColor(255, 255, 255, 125), QColor(255, 255, 255, 50))

        self.searchButton = TransparentToolButton(FIF.HELP.icon(), self)
        self.searchButton.setToolTip('帮助')
        self.searchButton.clicked.connect(self.onHelpButtonClicked)
        # self.tabBar.tabCloseRequested.connect(self.tabRemoveRequest)

        self.hBoxLayout.insertWidget(5, self.tabBar, 1)
        self.hBoxLayout.setStretch(6, 0)
        self.hBoxLayout.insertWidget(7, self.searchButton, 0, alignment=Qt.AlignRight)

        # self.hBoxLayout.insertSpacing(8, 20)

    def canDrag(self, pos: QPoint):
        if not super().canDrag(pos):
            return False
        pos.setX(pos.x() - self.tabBar.x())
        return not self.tabBar.tabRegion().contains(pos)


class Window(MSFluentWindow):

    def __init__(self):
        super().__init__()
        self.main_class = None
        self.initWindow()
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        self.setTitleBar(BAASTitleBar(self))
        self.tabBar = self.titleBar.tabBar
        self.navi_btn_list = []
        self.show()
        setThemeColor('#0078d4')
        self.__switchStatus = True
        self.config_dir_list = []

        if not os.path.exists('./config'):
            os.mkdir('./config')
        for _dir_ in os.listdir('./config'):
            if os.path.isdir(f'./config/{_dir_}'):
                files = os.listdir(f'./config/{_dir_}')
                if 'config.json' in files:
                    check_config(_dir_)
                    self.config_dir_list.append(ConfigSet(config_dir=_dir_))

        if len(self.config_dir_list) == 0:
            check_config('default_config')
            self.config_dir_list.append(ConfigSet('default_config'))
        self.ocr_needed = ['NUM', 'Global']
        for config in self.config_dir_list:
            if config.server_mode not in self.ocr_needed:
                self.ocr_needed.append(config.server_mode)
        # create sub interface
        from gui.fragments.home import HomeFragment
        from gui.fragments.switch import SwitchFragment
        from gui.fragments.settings import SettingsFragment
        self._sub_list = [[HomeFragment(parent=self, config=x) for x in self.config_dir_list],
                          [SwitchFragment(parent=self, config=x) for x in self.config_dir_list],
                          [SettingsFragment(parent=self, config=x) for x in self.config_dir_list]]
        # _sc_list = [SwitchFragment(parent=self, config_dir=x) for x in config_dir_list]
        self.homeInterface = self._sub_list[0][0]
        self.schedulerInterface = self._sub_list[1][0]
        self.settingInterface = self._sub_list[2][0]
        # self.processInterface = ProcessFragment()
        # self.navigationInterface..connect(self.onNavigationChanged)
        self.initNavigation()
        self.dispatchWindow()
        self.splashScreen.finish()
        self.init_main_class()

    def init_main_class(self, ):
        threading.Thread(target=self.init_main_class_thread).start()

    def init_main_class_thread(self):
        from main import Main
        self.main_class = Main(self._sub_list[0][0]._main_thread_attach.logger_signal, self.ocr_needed)
        for i in range(0, len(self._sub_list[0])):
            self._sub_list[0][i]._main_thread_attach.Main = self.main_class

    def call_update(self):
        self.schedulerInterface.update_settings()

    def initNavigation(self):
        self.navi_btn_list = [
            self.addSubInterface(self.homeInterface, FIF.HOME, '主页'),
            self.addSubInterface(self.schedulerInterface, FIF.CALENDAR, '配置'),
            self.addSubInterface(self.settingInterface, FIF.SETTING, '设置')
        ]

        for ind, btn in enumerate(self.navi_btn_list):
            btn.disconnect()
            btn.clicked.connect(partial(self.onNavigationChanged, ind))

        for sub in self._sub_list:
            for tab in sub[1:]:
                self.stackedWidget.addWidget(tab)
        # add custom widget to bottom

        # Add some tabs in the group
        for home_tab in self._sub_list[0]:
            self.addTab(home_tab.object_name, home_tab.config['name'], None)
        # self.stackedWidget.currentChanged.connect(self.onTabChanged)
        self.tabBar.currentChanged.connect(self.onTabChanged)
        self.tabBar.tabAddRequested.connect(self.onTabAddRequested)
        self.tabBar.tabCloseRequested.connect(self.onTabCloseRequested)
        self.titleBar.onHelpButtonClicked.connect(self.showHelpModal)

    def initWindow(self):
        self.resize(900, 700)
        desktop = QApplication.desktop().availableGeometry()
        _w, _h = desktop.width(), desktop.height()
        self.move(_w // 2 - self.width() // 2, _h // 2 - self.height() // 2)

    def closeEvent(self, event):
        super().closeEvent(event)

    @staticmethod
    def showHelpModal():
        helpModal = ReadMeWindow()
        helpModal.setWindowTitle('帮助')
        helpModal.setWindowIcon(QIcon(ICON_DIR))
        helpModal.resize(800, 600)
        helpModal.setFocus()
        helpModal.show()

    def onNavigationChanged(self, index: int):
        for ind, btn in enumerate(self.navi_btn_list):
            btn.setSelected(True if ind == index else False)
        objectName = self.tabBar.currentTab().routeKey()
        # new_interface = list(filter(lambda x: x.object_name == objectName, self._home_list))[0]
        col = [x.object_name for x in self._sub_list[0]].index(objectName)
        self.dispatchSubView(index, col)

    def onTabChanged(self, _: int):
        self.__switchStatus = False
        objectName = self.tabBar.currentTab().routeKey()
        currentName = self.stackedWidget.currentWidget().objectName()
        row = -1
        for i0, sub in enumerate(self._sub_list):
            for i1, tab in enumerate(sub):
                if tab.object_name == currentName:
                    row = i0
        assert row != -1
        col = [x.object_name for x in self._sub_list[0]].index(objectName)
        self.dispatchSubView(row, col)

    def dispatchSubView(self, i0: int, i1: int):
        self.stackedWidget.setCurrentWidget(self._sub_list[i0][i1], popOut=False)

    def onTabAddRequested(self):
        addDialog = SaveSettingMessageBox(self)
        addDialog.pathLineEdit.setFocus()
        if addDialog.exec_():
            text = addDialog.pathLineEdit.text()
            if text in list(map(lambda x: x.config['name'], self.config_dir_list)):
                ib = InfoBar(
                    icon=InfoBarIcon.ERROR,
                    title='设置成功',
                    content=f'名为“{text}”的配置已经存在！',
                    orient=Qt.Vertical,  # vertical layout
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
                ib.show()
                return
            serial_name = str(int(datetime.datetime.now().timestamp()))
            os.mkdir(f'./config/{serial_name}')
            check_event_config(serial_name)
            check_display_config(serial_name)
            check_switch_config(serial_name)
            data = json.loads(default_config.DEFAULT_CONFIG)
            data['name'] = text
            with open(f'./config/{serial_name}/config.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=2))
            from gui.fragments.home import HomeFragment
            from gui.fragments.switch import SwitchFragment
            from gui.fragments.settings import SettingsFragment
            _config = ConfigSet(config_dir=serial_name)
            _sub_list_ = [
                HomeFragment(parent=self, config=_config),
                SwitchFragment(parent=self, config=_config),
                SettingsFragment(parent=self, config=_config)
            ]
            for i in range(0, len(_sub_list_)):
                self._sub_list[i].append(_sub_list_[i])
                self.stackedWidget.addWidget(_sub_list_[i])
            self.addTab(_sub_list_[0].object_name, text, 'resource/Smiling_with_heart.png')

    def onTabCloseRequested(self, i0):
        config_name = self._sub_list[0][i0].config["name"]
        title = f'是否要删除配置：{config_name}？'
        content = """你需要在确认后重启BAAS以完成更改。"""
        closeRequestBox = MessageBox(title, content, self)
        if closeRequestBox.exec():
            shutil.rmtree(f'./config/{self._sub_list[0][i0].config.config_dir}')

    def addTab(self, routeKey, text, icon):
        self.tabBar.addTab(routeKey, text, icon)

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
