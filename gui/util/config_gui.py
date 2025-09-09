import sys

from PyQt5.QtCore import QLocale, pyqtSignal
from qfluentwidgets import (BoolValidator, ColorConfigItem, ConfigItem, ConfigSerializer,
                            OptionsConfigItem, OptionsValidator, QConfig, qconfig, setThemeColor)

from gui.util.language import Language


COLOR_THEME = {
    'Light': {
        # 基础
        'background': '#eeffffff',
        'background_hover': '#e0f7fa',
        'text': '#333333',
        'outline': '#ffffff',
        'border': '#eecccccc',

        # 语义化背景
        'background__success': '#d4edda',  # 浅绿色背景
        'background__warning': '#fff3cd',  # 浅黄色背景
        'background__error':   '#f8d7da',  # 浅红色背景
        'background__info':    '#d1ecf1',  # 浅蓝色背景

        # 语义化文字
        'text__success': '#155724',  # 深绿色
        'text__warning': '#856404',  # 深黄色/棕色
        'text__error':   '#721c24',  # 深红色
        'text__info':    '#0c5460',  # 深蓝色
        'text__gray':   '#666666',  # 中灰色

        # 语义化边框
        'border__success': '#c3e6cb',
        'border__warning': '#ffeeba',
        'border__error':   '#f5c6cb',
        'border__info':    '#bee5eb',
    },

    'Dark': {
        # 基础
        'background': '#44333333',
        'background_hover': '#555555',
        'text': '#ffffff',
        'outline': '#333333',
        'border': '#ee555555',

        # 语义化背景（深色模式用更暗的色调）
        'background__success': '#1e3d2f',
        'background__warning': '#3d3620',
        'background__error':   '#402626',
        'background__info':    '#1f3a40',

        # 语义化文字（亮色以便在深背景上可读）
        'text__success': '#a6e3b0',
        'text__warning': '#ffd97a',
        'text__error':   '#f28b82',
        'text__info':    '#80d4ea',
        'text__gray':   '#bbbbbb',

        # 语义化边框
        'border__success': '#3a5f4b',
        'border__warning': '#5f5635',
        'border__error':   '#6a3a3a',
        'border__info':    '#34656a',
    }
}



class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name()

    def deserialize(self, value: str):
        return Language(QLocale(value))


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class ConfigGui(QConfig):
    """ Language config """
    themeColor = ColorConfigItem("QFluentWidgets", "ThemeColor", '#0078d4')
    micaEnableChanged = pyqtSignal(bool)
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.ENGLISH, OptionsValidator(Language), LanguageSerializer(), restart=True)
    configDisplayType = OptionsConfigItem(
        "MainWindow", "configLoadType", "Card", OptionsValidator(["Card", "List"]), restart=True)
    cardDisplayType = OptionsConfigItem(
        "MainWindow", "cardDisplayType", "withImage", OptionsValidator(["withImage", "plainText"]), restart=True)


configGui = ConfigGui()

qconfig.load('config/gui.json', configGui)
setThemeColor(configGui.themeColor.value)
