from enum import Enum
from PyQt5.QtCore import QLocale


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    ENGLISH = QLocale(QLocale.English, QLocale.UnitedStates)
    JAPANESE = QLocale(QLocale.Japanese, QLocale.Japan)
    KOREAN = QLocale(QLocale.Korean, QLocale.SouthKorea)

    @staticmethod
    def get_raw(lang_name: str):
        switcher = {
            '简体中文': 'zh_CN',
            'English': 'en_US',
            '日本語': 'ja_JP',
            '괴뢰어': 'ko_KR'
        }
        return switcher[lang_name]

    @staticmethod
    def combobox():
        return ['简体中文', 'English', '日本語', '괴뢰어']


if __name__ == "__main__":
    for language in Language:
        print(language.value.name())
