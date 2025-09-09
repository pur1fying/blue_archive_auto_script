# coding:utf-8
import datetime
import json
import os
import shutil
import sys
import threading
from functools import partial
from typing import Union

from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel
from qfluentwidgets import FluentIcon as FIF, FluentTranslator, SplashScreen, MSFluentWindow, TabBar, \
    MSFluentTitleBar, MessageBox, TransparentToolButton, FluentIconBase, TabItem, \
    RoundMenu, Action, MenuAnimationType, MessageBoxBase, LineEdit
from qfluentwidgets import (SubtitleLabel, setFont)

from core.config import default_config
from gui.components.dialog_panel import CreateSettingMessageBox
from gui.fragments.process import ProcessFragment
from gui.fragments.readme import ReadMeWindow
from gui.util import notification
from gui.util.config_gui import configGui, COLOR_THEME
from core.config.config_set import ConfigSet
from gui.util.language import Language
from gui.util.translator import baasTranslator as bt

# sys.stderr = open('error.log', 'w+', encoding='utf-8')
# sys.stdout = open('output.log', 'w+', encoding='utf-8')
sys.path.append('./')

# Offer the error to the error.log
ICON_DIR = 'gui/assets/logo.png'
LAST_NOTICE_TIME = 0


def delete_deprecated_config(file_name, config_name=None):
    # delete useless config file
    pre = 'config/'
    if config_name is not None:
        pre += config_name + '/'
    if type(file_name) is str:
        path = pre + file_name
        if os.path.exists(path):
            os.remove(path)
    elif type(file_name) is list:
        for name in file_name:
            path = pre + name
            if os.path.exists(path):
                os.remove(path)


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
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
    except Exception:
        os.remove('./config/static.json')
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)


def check_switch_config(dir_path='./default_config'):
    path = './config/' + dir_path + '/switch.json'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_config.SWITCH_DEFAULT_CONFIG)


def check_and_update_user_config(dir_path='./default_config'):
    path = './config/' + dir_path + '/config.json'
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = update_config_reserve_old(data, json.loads(default_config.DEFAULT_CONFIG))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        os.remove(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)


def check_single_event(new_event, old_event):
    for key in new_event:
        if key not in old_event:
            old_event[key] = new_event[key]
    return old_event


def check_event_config(dir_path='./default_config', user_config=None):
    path = './config/' + dir_path + '/event.json'
    default_event_config = json.loads(default_config.EVENT_DEFAULT_CONFIG)
    server = user_config.server_mode
    enable_state = user_config.config.new_event_enable_state
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
                temp = default_event_config[i]
                if enable_state == "on":
                    temp['enabled'] = True
                elif enable_state == "off":
                    temp['enabled'] = False
                data.insert(i, temp)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        with open("error.log", 'w+', encoding='utf-8') as f:
            f.write(str(e) + '\n' + dir_path + '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(default_event_config, ensure_ascii=False, indent=2))
        return


def check_config(dir_path):
    delete_deprecated_config("display.json", dir_path)
    if not os.path.exists('./config'):
        os.mkdir('./config')
    check_static_config()
    if type(dir_path) is not list:
        dir_path = [dir_path]
    for path in dir_path:
        if not os.path.exists('./config/' + path):
            os.mkdir('./config/' + path)
        check_and_update_user_config(path)
        config = ConfigSet(config_dir=path)
        config.update_create_quantity_entry()
        check_event_config(path, config)
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
        text = config.config.name
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


class BAASLangAltButton(TransparentToolButton):
    def __init__(self, parent):
        super().__init__(parent)
        configGui.language.valueChanged.connect(self._onLangChanged)

        self.setToolTip(self.tr('语言设置'))
        self.actions = []
        self.clicked.connect(self.showLangAltDropdown)

    def showLangAltDropdown(self):
        self._init_actions()
        pos = self.mapToGlobal(QPoint(0, 0))
        self.menu.exec(pos, aniType=MenuAnimationType.DROP_DOWN)

    def _init_actions(self):
        self.menu = RoundMenu(parent=self)
        for ind, lang in enumerate(Language.combobox()):
            status = ' ✔' if Language.get_raw(lang) == configGui.get(configGui.language).value.name() else ''
            action = Action(FIF.PLAY, self.tr(lang) + status, triggered=partial(self._onLangChanged, lang, ind))
            self.actions.append(action)
            self.menu.addAction(action)

    def _onLangChanged(self, lang, ind=0):
        for action in self.actions:
            action.setText(action.text().replace(' ✔', ''))
        if lang == configGui.language.value: return
        configGui.set(configGui.language, configGui.language.options[ind])
        self.menu.close()
        self.menu.deleteLater()


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

        self.langButton = BAASLangAltButton(self)

        self.historyButton = TransparentToolButton(self)
        self.historyButton.setToolTip(self.tr('更新日志'))
        self.historyButton.clicked.connect(self.onHistoryButtonClicked)

        self.helpButton = TransparentToolButton(self)
        self.helpButton.setToolTip(self.tr('帮助'))
        self.helpButton.clicked.connect(self.onHelpButtonClicked)
        # self.tabBar.tabCloseRequested.connect(self.tabRemoveRequest)

        self._set_icon()

        self.hBoxLayout.insertWidget(5, self.tabBar, 1)
        self.hBoxLayout.setStretch(6, 0)
        self.hBoxLayout.insertWidget(6, self.langButton, 0, alignment=Qt.AlignRight)
        self.hBoxLayout.insertWidget(6, self.historyButton, 0, alignment=Qt.AlignRight)
        self.hBoxLayout.insertWidget(7, self.helpButton, 0, alignment=Qt.AlignRight)

        configGui.themeChanged.connect(self._set_icon)

    def _set_icon(self):
        self.historyButton.setIcon(FIF.HISTORY.icon(
            color=COLOR_THEME[configGui.theme.value]['text']))
        self.helpButton.setIcon(FIF.HELP.icon(
            color=COLOR_THEME[configGui.theme.value]['text']))
        self.langButton.setIcon(FIF.LANGUAGE.icon(
            color=COLOR_THEME[configGui.theme.value]['text']))

    def canDrag(self, pos: QPoint):
        if not super().canDrag(pos):
            return False
        pos.setX(pos.x() - self.tabBar.x())
        return not self.tabBar.tabRegion().contains(pos)


class Window(MSFluentWindow):
    notify_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_class = None
        self.initWindow()
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
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
        self.ocr_needed = ['en-us']
        for config in self.config_dir_list:
            if config.server_mode == "CN":
                self.ocr_needed.append('zh-cn')
            elif config.server_mode == "JP":
                self.ocr_needed.append('ja-jp')
            config.set_window(self)
        # create sub interface
        from gui.fragments.home import HomeFragment
        from gui.fragments.switch import SwitchFragment
        from gui.fragments.settings import SettingsFragment
        from gui.fragments.glob import GlobalFragment
        QApplication.processEvents()
        self._sub_list = [[HomeFragment(parent=self, config=x) for x in self.config_dir_list],
                          [ProcessFragment(parent=self, config=x) for x in self.config_dir_list],
                          [SwitchFragment(parent=self, config=x) for x in self.config_dir_list],
                          [SettingsFragment(parent=self, config=x) for x in self.config_dir_list]]
        # _sc_list = [SwitchFragment(parent=self, config_dir=x) for x in config_dir_list]
        self.homeInterface = self._sub_list[0][0]
        self.processInterface = self._sub_list[1][0]
        self.schedulerInterface = self._sub_list[2][0]
        self.settingInterface = self._sub_list[3][0]
        self.globalInterface = GlobalFragment(parent=self, config=self.config_dir_list[0])
        # self.processInterface = ProcessFragment()
        # self.navigationInterface..connect(self.onNavigationChanged)
        self.initNavigation()
        self.splashScreen.finish()

        # SingleShot is used to speed up the initialization process
        # self.init_main_class()
        QTimer.singleShot(100, self.init_main_class)

    def init_main_class(self, ):
        threading.Thread(target=self.init_main_class_thread).start()

    def notify(self, raw_msg):
        json_msg = json.loads(raw_msg)
        notification.__dict__['_' + json_msg['type']](json_msg['label'], json_msg['msg'], self)

    def init_main_class_thread(self):
        QApplication.processEvents()
        try:
            from main import Main
            self.main_class = Main(self._sub_list[0][0].main_thread_attach.logger_signal, self.ocr_needed)
            for i in range(0, len(self._sub_list[0])):
                self._sub_list[0][i].main_thread_attach.Main = self.main_class
        except Exception as e:
            from core.utils import Logger
            Logger(self._sub_list[0][0].main_thread_attach.logger_signal).error(e.__str__())

    def call_update(self):
        self.schedulerInterface.update_settings()

    def initNavigation(self):
        self.navi_btn_list = [
            self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页')),
            self.addSubInterface(self.processInterface, FIF.CALENDAR, self.tr('调度')),
            self.addSubInterface(self.schedulerInterface, FIF.CALENDAR, self.tr('配置')),
            self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('设置')),
            self.addSubInterface(self.globalInterface, FIF.UPDATE, self.tr('更新设置'))
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
        self.setTitleBar(BAASTitleBar(self))
        self.setWindowIcon(QIcon(ICON_DIR))
        self.setWindowTitle('BlueArchiveAutoScript')

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
        if index == 4:
            self.globalInterface.lazy_init()
            self.stackedWidget.setCurrentWidget(self.globalInterface, popOut=False)
            return
        objectName = self.tabBar.currentTab().routeKey()
        col = [x.object_name for x in self._sub_list[0]].index(objectName)
        self.dispatchSubView(index, col)

    def onTabChanged(self, _: int):
        obj_name = self.stackedWidget.currentWidget().objectName()
        if obj_name.endswith("GlobalFragment"):
            return
        self.__switchStatus = False
        objectName = self.tabBar.currentTab().routeKey()
        row = [x.isSelected for x in self.navi_btn_list].index(True)
        _ref = [x.object_name for x in self._sub_list[0]]
        if objectName not in _ref:
            col = 0
        else:
            col = [x.object_name for x in self._sub_list[0]].index(objectName)
        self.dispatchSubView(row, col)

    def dispatchSubView(self, i0: int, i1: int):
        self.stackedWidget.setCurrentWidget(self._sub_list[i0][i1], popOut=False)

    def onTabAddRequested(self):
        addDialog = CreateSettingMessageBox(self)
        addDialog.pathLineEdit.setFocus()
        if addDialog.exec_():
            text = addDialog.pathLineEdit.text()
            if text in list(map(lambda x: x.config.name, self.config_dir_list)):
                notification.error(label=self.tr('设置失败'),
                                   msg=f'{self.tr("名为")}“{text}”{self.tr("的配置已经存在！")}',
                                   config=self.config_dir_list[0])
                return
            serial_name = str(int(datetime.datetime.now().timestamp()))
            config_dir = f'./config/{serial_name}'
            os.mkdir(config_dir)
            data = json.loads(default_config.DEFAULT_CONFIG)
            data['name'] = text
            user_config_path = f'{config_dir}/config.json'
            with open(user_config_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=2))
            _config = ConfigSet(config_dir=serial_name)

            check_event_config(serial_name, _config)
            check_switch_config(serial_name)

            from gui.fragments.home import HomeFragment
            from gui.fragments.switch import SwitchFragment
            from gui.fragments.settings import SettingsFragment
            _config.add_signal("notify_signal", self.notify_signal)
            _config.set_window(self)
            _sub_list_ = [
                HomeFragment(parent=self, config=_config),
                ProcessFragment(parent=self, config=_config),
                SwitchFragment(parent=self, config=_config),
                SettingsFragment(parent=self, config=_config)
            ]
            for i in range(0, len(_sub_list_)):
                self._sub_list[i].append(_sub_list_[i])
                self.stackedWidget.addWidget(_sub_list_[i])
            self.addTab(_sub_list_[0].object_name, _config, 'resource/Smiling_with_heart.png')
            self.config_dir_list.append(_config)

    def onTabCloseRequested(self, i0):
        config_name = self._sub_list[0][i0].config.config.name
        title = self.tr('是否要删除配置：') + f' {config_name}？'
        content = self.tr("""你需要在确认后重启BAAS以完成更改。""")
        closeRequestBox = MessageBox(title, content, self)
        if closeRequestBox.exec():
            shutil.rmtree(self._sub_list[0][i0].config.config_dir)
            _changed_table = []
            for sub in self._sub_list:
                _changed_row = []
                for tab in sub:
                    if config_name != tab.config.config.name:
                        _changed_row.append(tab)
                _changed_table.append(_changed_row)
            self._sub_list = _changed_table
            # Remove the config from the list
            for _config in self.config_dir_list:
                if _config.config.name == config_name:
                    self.config_dir_list.remove(_config)
                    break
            self.tabBar.removeTab(i0)

    def addTab(self, routeKey: str, config: ConfigSet, icon: Union[QIcon, str, FluentIconBase, None]):
        self.tabBar.addBAASTab(routeKey, config, icon, window=self)


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
    deprecated_configs = [
        "display.json",
        "event.json",
        "switch.json",
        "config.json",
        "language.json"
    ]
    delete_deprecated_config(deprecated_configs)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # internationalization
    translator = FluentTranslator(bt.locale)

    app.installTranslator(translator)
    app.installTranslator(bt)

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
