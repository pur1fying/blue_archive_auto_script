import json
import os
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
    configLoadType = OptionsConfigItem(
        "MainWindow", "configLoadType", "Card", OptionsValidator(["Card", "List"]), restart=True)


configGui = ConfigGui()
if not os.path.exists('config/gui.json'):
    DEFAULT_GUI_CONFIG = {
        "MainWindow": {
            "configLoadType": "Card",
            "DpiScale": 1,
            "Language": "zh_CN",
            "MicaEnabled": True
        },
        "QFluentWidgets": {
            "ThemeColor": "#ff0078d4",
            "ThemeMode": "Light"
        }
    }
    with open('config/gui.json', 'w') as f:
        f.write(json.dumps(DEFAULT_GUI_CONFIG, indent=4))

qconfig.load('config/gui.json', configGui)
setThemeColor(configGui.themeColor.value)
