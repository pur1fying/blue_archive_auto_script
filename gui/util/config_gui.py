import sys

from PyQt5.QtCore import QLocale, pyqtSignal
from qfluentwidgets import (BoolValidator, ColorConfigItem, ConfigItem, ConfigSerializer,
                            OptionsConfigItem, OptionsValidator, QConfig, qconfig, setThemeColor)

from gui.util.language import Language


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
