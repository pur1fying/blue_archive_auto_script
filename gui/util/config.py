# coding:utf-8
from enum import Enum

from qfluentwidgets import (qconfig, QConfig, ConfigItem)


class SongQuality(Enum):
    """ Online song quality enumeration class """

    STANDARD = "Standard quality"
    HIGH = "High quality"
    SUPER = "Super quality"
    LOSSLESS = "Lossless quality"


class MvQuality(Enum):
    """ MV quality enumeration class """

    FULL_HD = "Full HD"
    HD = "HD"
    SD = "SD"
    LD = "LD"


class Config(QConfig):
    """ Config of application """

    dailyCollect = ConfigItem("Daily", "Collect", True)
    dailyConsume = ConfigItem("Daily", "Consume", True)
    emailCheck = ConfigItem("Daily", "Email", True)
    hardModeCombat = ConfigItem("Combat", "HardMode", True)
    collaborateCombat = ConfigItem("Combat", "Collaborate", True)
    cafe = ConfigItem("Daily", "Cafe", True)
    atelier = ConfigItem("Daily", "Atelier", True)
    team = ConfigItem("Daily", "Team", True)
    shopList = ConfigItem("Daily", "ShopList", [0] * 16)
    mainStop = ConfigItem("Daily", "mainStop", '4-4')

    server = ConfigItem("Settings", "server", '官服')
    port = ConfigItem("Settings", "port", 7555)

    emulatorPath = ConfigItem("Emulator", "Path", "")


conf = Config()
qconfig.load('gui/config/config.json', conf)
