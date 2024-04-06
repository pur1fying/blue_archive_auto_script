from enum import Enum
from PyQt5.QtCore import QLocale, QTranslator
from qfluentwidgets import ConfigSerializer, OptionsConfigItem, OptionsValidator, QConfig, qconfig


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    ENGLISH = QLocale(QLocale.English, QLocale.UnitedStates)
    # AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() #if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) #if value != "Auto" else Language.AUTO
    

class Config(QConfig):
    """ Config of application """
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.ENGLISH, OptionsValidator(Language), LanguageSerializer(), restart=True)
    
    def __init__(self):
        super().__init__()


class Translator(QTranslator):
    def __init__(self, parent=None):
        super().__init__(parent)

    def encode(self, *args):
        return [arg.encode('utf-8') if arg else arg for arg in args]

    def decode(self, *args):
            return [arg.decode('utf-8') if arg else arg for arg in args]
    
    def toString(self, tranlation: str | bytes) -> str:
        if isinstance(tranlation, bytes):
            tranlation = self.decode(tranlation)
        return tranlation
    
    def tr(self, context: str | None, sourceText: str | None, disambiguation: str | None = None, n: int = -1) -> str:
        """
        Convert sourceText by looking in the qm file.
        Use this to access specific context tags outside source file.

        Parameters
        ----------
        context: str 
            context tag in .ts file e.g ConfigTranslation

        sourceText: str 
            the text to translate
        """
        bytesArgs = self.encode(context, sourceText, disambiguation)
        translation = super().translate(*bytesArgs, n)
        if translation:
            return self.toString(translation)
        return sourceText
    

cfg = Config()
qconfig.load('config/language.json', cfg)
baasTranslator = Translator()
