from enum import Enum
from PyQt5.QtCore import QLocale


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    ENGLISH = QLocale(QLocale.English, QLocale.UnitedStates)
    JAPANESE = QLocale(QLocale.Japanese, QLocale.Japan)
    KOREAN = QLocale(QLocale.Korean, QLocale.SouthKorea)

    def combobox():
        return ['简体中文', 'English', '日本語', '괴뢰어']

if __name__ == "__main__":
    for language in Language:
        print(language.value.name())
