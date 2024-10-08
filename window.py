# coding:utf-8
import datetime
import json
import os
import shutil
import sys
import threading
from functools import partial
from typing import Union

from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel
from qfluentwidgets import FluentIcon as FIF, FluentTranslator, SplashScreen, MSFluentWindow, TabBar, \
    MSFluentTitleBar, MessageBox, TransparentToolButton, FluentIconBase, TabItem, \
    RoundMenu, Action, MenuAnimationType, MessageBoxBase, LineEdit
from qfluentwidgets import (SubtitleLabel, setFont, setThemeColor)

from core import default_config
from gui.components.dialog_panel import CreateSettingMessageBox
from gui.fragments.process import ProcessFragment
from gui.fragments.readme import ReadMeWindow
from gui.util import notification
from gui.util.config_set import ConfigSet
from gui.util.config_gui import configGui
from gui.util.translator import baasTranslator as bt

# sys.stderr = open('error.log', 'w+', encoding='utf-8')
# sys.stdout = open('output.log', 'w+', encoding='utf-8')
sys.path.append('./')

# Offer the error to the error.log
ICON_DIR = 'gui/assets/logo.png'
LAST_NOTICE_TIME = 0


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
                default_event_config[i]['daily_reset'][j][0] = default_event_config[i]['daily_reset'][j][0] - 1
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
                    for k in range(0, len(data[i]['daily_reset'])):
                        if len(data[j]['daily_reset'][k]) != 3:
                            data[j]['daily_reset'][k] = [0, 0, 0]
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
        elif server == "国际服" or "国际服青少年" or "韩国ONE":
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


class RenameDialogBox(MessageBoxBase):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        RenameDialogContext = QObject()
        self.titleLabel = SubtitleLabel(self.tr('配置详情'), self)
        self.viewLayout.addWidget(self.titleLabel)

        self.name_input = None

        configItems = [
            {
                'label': RenameDialogContext.tr('原来的配置名称'),
                'key': 'name',
                'type': 'text',
                'readOnly': True,
            },
            {
                'label': RenameDialogContext.tr('修改后的配置名称'),
                'key': 'name',
                'type': 'text',
                'readOnly': False,
            }
        ]

        for ind, cfg in enumerate(configItems):
            optionPanel = QHBoxLayout(self)
            labelComponent = QLabel(bt.tr('ConfigTranslation', cfg['label']), self)
            optionPanel.addWidget(labelComponent, 0, Qt.AlignLeft)
            optionPanel.addStretch(1)
            currentKey = cfg['key']
            inputComponent = LineEdit(self)
            if ind == 1: self.name_input = inputComponent
            if cfg['readOnly']: inputComponent.setReadOnly(True)
            inputComponent.setText(config.get(currentKey))
            optionPanel.addWidget(inputComponent, 0, Qt.AlignRight)
            self.viewLayout.addLayout(optionPanel)
            labelComponent.setStyleSheet("""
                font-family: "Microsoft YaHei";
                font-size: 15px;
            """)
        self.yesButton.setText(RenameDialogContext.tr('确定'))
        self.cancelButton.setText(RenameDialogContext.tr('取消'))
        self.widget.setMinimumWidth(350)


class BAASTabItem(TabItem):
    def __init__(self, *args, **kwargs):
        if 'config' in kwargs.keys():
            self.config = kwargs.pop('config')
        if 'window' in kwargs.keys():
            self.window = kwargs.pop('window')
        super().__init__(*args, **kwargs)

    def contextMenuEvent(self, a0):
        print(self.config.get('name'))
        menu = RoundMenu(parent=self)
        rename_action = Action(FIF.EDIT, self.tr('重命名'), triggered=self._showRenameDialog)
        menu.addAction(rename_action)
        rename_action.setCheckable(True)
        rename_action.setChecked(True)
        menu.exec(a0.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def _showRenameDialog(self):
        rename_dialog = RenameDialogBox(self.window, self.config)
        if not rename_dialog.exec_(): return
        new_name = rename_dialog.name_input.text()
        if new_name == self.config.get('name'): return
        self.config.set('name', new_name)
        self.setText(new_name)


class BAASTabBar(TabBar):
    def __init__(self, parent):
        super().__init__(parent)

    def addBAASTab(self, routeKey: str, config: ConfigSet, icon: Union[QIcon, str, FluentIconBase] = None, window=None):
        return self.insertBAASTab(-1, routeKey, config, icon, window=window)

    def insertBAASTab(self, index: int, routeKey: str, config: ConfigSet,
                      icon: Union[QIcon, str, FluentIconBase] = None, window=None, onClick=None):
        if routeKey in self.itemMap:
            raise ValueError(f"The route key `{routeKey}` is duplicated.")
        if index == -1:
            index = len(self.items)
        if index <= self.currentIndex() and self.currentIndex() >= 0:
            self._currentIndex += 1
        text = config.get_origin('name')
        item = BAASTabItem(text, self.view, icon, config=config, window=window)
        item.setRouteKey(routeKey)
        _w = self.tabMaximumWidth() if self.isScrollable() else self.tabMinimumWidth()
        item.setMinimumWidth(_w)
        item.setMaximumWidth(self.tabMaximumWidth())
        item.setShadowEnabled(self.isTabShadowEnabled())
        item.setCloseButtonDisplayMode(self.closeButtonDisplayMode)
        item.setSelectedBackgroundColor(
            self.lightSelectedBackgroundColor, self.darkSelectedBackgroundColor)
        item.pressed.connect(self._onItemPressed)
        item.closed.connect(lambda: self.tabCloseRequested.emit(self.items.index(item)))
        if onClick:
            item.pressed.connect(onClick)
        self.itemLayout.insertWidget(index, item, 1)
        self.items.insert(index, item)
        self.itemMap[routeKey] = item
        if len(self.items) == 1:
            self.setCurrentIndex(0)
        return item


class BAASTitleBar(MSFluentTitleBar):
    """ Title bar with icon and title """
    onHelpButtonClicked = pyqtSignal()
    onHistoryButtonClicked = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        # add buttons
        self.toolButtonLayout = QHBoxLayout()
        self.hBoxLayout.insertLayout(4, self.toolButtonLayout)

        # add tab bar
        self.tabBar = BAASTabBar(self)
        self.tabBar.setMovable(False)
        self.tabBar.setTabMaximumWidth(120)
        self.tabBar.setTabShadowEnabled(False)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabSelectedBackgroundColor(QColor(255, 255, 255, 125), QColor(255, 255, 255, 50))

        self.historyButton = TransparentToolButton(FIF.HISTORY, self)
        self.historyButton.setToolTip('更新日志')
        self.historyButton.clicked.connect(self.onHistoryButtonClicked)

        self.searchButton = TransparentToolButton(FIF.HELP, self)
        self.searchButton.setToolTip(self.tr('帮助'))
        self.searchButton.clicked.connect(self.onHelpButtonClicked)
        # self.tabBar.tabCloseRequested.connect(self.tabRemoveRequest)

        self.hBoxLayout.insertWidget(5, self.tabBar, 1)
        self.hBoxLayout.setStretch(6, 0)
        self.hBoxLayout.insertWidget(6, self.historyButton, 0, alignment=Qt.AlignRight)
        self.hBoxLayout.insertWidget(7, self.searchButton, 0, alignment=Qt.AlignRight)

        # self.hBoxLayout.insertSpacing(8, 20)

    def canDrag(self, pos: QPoint):
        if not super().canDrag(pos):
            return False
        pos.setX(pos.x() - self.tabBar.x())
        return not self.tabBar.tabRegion().contains(pos)


class Window(MSFluentWindow):
    notify_signal = pyqtSignal(str)

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
        self.__switchStatus = True
        self.config_dir_list = []

        if not os.path.exists('./config'):
            os.mkdir('./config')
        for _dir_ in os.listdir('./config'):
            if os.path.isdir(f'./config/{_dir_}'):
                files = os.listdir(f'./config/{_dir_}')
                if 'config.json' in files:
                    check_config(_dir_)
                    conf = ConfigSet(config_dir=_dir_)
                    conf.add_signal("notify_signal", self.notify_signal)
                    self.config_dir_list.append(conf)
        self.notify_signal.connect(self.notify)
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
                          [ProcessFragment(parent=self, config=x) for x in self.config_dir_list],
                          [SwitchFragment(parent=self, config=x) for x in self.config_dir_list],
                          [SettingsFragment(parent=self, config=x) for x in self.config_dir_list]]
        # _sc_list = [SwitchFragment(parent=self, config_dir=x) for x in config_dir_list]
        self.homeInterface = self._sub_list[0][0]
        self.processInterface = self._sub_list[1][0]
        self.schedulerInterface = self._sub_list[2][0]
        self.settingInterface = self._sub_list[3][0]
        # self.processInterface = ProcessFragment()
        # self.navigationInterface..connect(self.onNavigationChanged)
        self.initNavigation()
        self.dispatchWindow()
        self.splashScreen.finish()
        self.init_main_class()

    def init_main_class(self, ):
        threading.Thread(target=self.init_main_class_thread).start()

    def notify(self, raw_msg):
        json_msg = json.loads(raw_msg)
        notification.__dict__['_' + json_msg['type']](json_msg['label'], json_msg['msg'], self)

    def init_main_class_thread(self):
        from main import Main
        self.main_class = Main(self._sub_list[0][0]._main_thread_attach.logger_signal, self.ocr_needed)
        for i in range(0, len(self._sub_list[0])):
            self._sub_list[0][i]._main_thread_attach.Main = self.main_class

    def call_update(self):
        self.schedulerInterface.update_settings()

    def initNavigation(self):
        self.navi_btn_list = [
            self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页')),
            self.addSubInterface(self.processInterface, FIF.CALENDAR, self.tr('调度')),
            self.addSubInterface(self.schedulerInterface, FIF.CALENDAR, self.tr('配置')),
            self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('设置'))
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
            self.addTab(home_tab.object_name, home_tab.config, None)
        # self.stackedWidget.currentChanged.connect(self.onTabChanged)
        self.tabBar.currentChanged.connect(self.onTabChanged)
        self.tabBar.tabAddRequested.connect(self.onTabAddRequested)
        self.tabBar.tabCloseRequested.connect(self.onTabCloseRequested)
        self.titleBar.onHelpButtonClicked.connect(self.showHelpModal)
        self.titleBar.onHistoryButtonClicked.connect(self.showHistoryModel)

    def initWindow(self):
        self.resize(900, 700)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        desktop = QApplication.desktop().availableGeometry()
        _w, _h = desktop.width(), desktop.height()
        self.move(_w // 2 - self.width() // 2, _h // 2 - self.height() // 2)

    def closeEvent(self, event):
        super().closeEvent(event)

    @staticmethod
    def showHelpModal():
        helpModal = ReadMeWindow()
        helpModal.setWindowTitle(helpModal.tr('帮助'))
        helpModal.setWindowIcon(QIcon(ICON_DIR))
        helpModal.resize(800, 600)
        helpModal.setFocus()
        helpModal.show()

    @staticmethod
    def showHistoryModel():
        from gui.fragments.history import HistoryWindow
        historyModal = HistoryWindow()
        historyModal.setWindowTitle('更新日志')
        historyModal.setWindowIcon(QIcon(ICON_DIR))
        historyModal.resize(800, 600)
        historyModal.setFocus()
        historyModal.show()

    def onNavigationChanged(self, index: int):
        for ind, btn in enumerate(self.navi_btn_list):
            btn.setSelected(True if ind == index else False)
        objectName = self.tabBar.currentTab().routeKey()
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
        addDialog = CreateSettingMessageBox(self)
        addDialog.pathLineEdit.setFocus()
        if addDialog.exec_():
            text = addDialog.pathLineEdit.text()
            if text in list(map(lambda x: x.config['name'], self.config_dir_list)):
                notification.error(self.tr('设置失败'), f'{self.tr("名为")}“{text}”{self.tr("的配置已经存在！")}', self)
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
                ProcessFragment(parent=self, config=_config),
                SettingsFragment(parent=self, config=_config)
            ]
            for i in range(0, len(_sub_list_)):
                self._sub_list[i].append(_sub_list_[i])
                self.stackedWidget.addWidget(_sub_list_[i])
            self.addTab(_sub_list_[0].object_name, _config, 'resource/Smiling_with_heart.png')

    def onTabCloseRequested(self, i0):
        config_name = self._sub_list[0][i0].config["name"]
        title = self.tr('是否要删除配置：') + f' {config_name}？'
        content = self.tr("""你需要在确认后重启BAAS以完成更改。""")
        closeRequestBox = MessageBox(title, content, self)
        if closeRequestBox.exec():
            shutil.rmtree(f'./config/{self._sub_list[0][i0].config.config_dir}')

    def addTab(self, routeKey: str, config: ConfigSet, icon: Union[QIcon, str, FluentIconBase, None]):
        self.tabBar.addBAASTab(routeKey, config, icon, window=self)

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


# enable dpi scale
if configGui.get(configGui.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(configGui.get(configGui.dpiScale))


if __name__ == '__main__':
    # pa=Main()
    # pa._init_emulator()
    # pa.solve("arena")

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # internationalization
    translator = FluentTranslator(bt.locale)
    bt.load("gui/i18n/" + bt.stringLang)

    app.installTranslator(translator)
    app.installTranslator(bt)

    bt.loadCfgTranslation()

    w = Window()
    w.setMicaEffectEnabled(configGui.get(configGui.micaEnabled))
    configGui.micaEnableChanged.connect(w.setMicaEffectEnabled)
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
