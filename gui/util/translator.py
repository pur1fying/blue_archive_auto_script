import typing

from PyQt5.QtCore import QLocale, QTranslator
from qfluentwidgets import ConfigSerializer, OptionsConfigItem, OptionsValidator, QConfig, qconfig

from gui.util.config_translation import ConfigTranslation
from gui.util.language import Language


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name()

    def deserialize(self, value: str):
        return Language(QLocale(value))
    

class Config(QConfig):
    """ Language config """
    language = OptionsConfigItem(
        "Translator", "Language", Language.ENGLISH, OptionsValidator(Language), LanguageSerializer(), restart=True)
    
    def __init__(self):
        super().__init__()


class Translator(QTranslator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = Config()
        qconfig.load('config/language.json', self.cfg)

        self.locale = self.cfg.get(self.cfg.language).value
        self.stringLang = self.locale.name()
        self.__config_translation = None
        
    def loadCfgTranslation(self):
        self.__config_translation = ConfigTranslation()

    def isString(self, value):
        return isinstance(value, str)
    
    def isBytes(self, value):
        return isinstance(value, bytes)
    
    def toString(self, tranlation: str | bytes) -> str:
        if self.isBytes(tranlation):
            tranlation = self.decode(tranlation)
        return tranlation
    
    def encode(self, *args):
        return [arg.encode('utf-8') if self.isString(arg) else arg for arg in args]

    def decode(self, *args):
        return [arg.decode('utf-8') if self.isBytes(arg) else arg for arg in args]
    
    def __get(self, text):
        return self.__config_translation.entries.get(text)
    
    def isChinese(self):
        return self.stringLang == 'zh_CN'

    def tr(self, 
           context: str, 
           sourceText: str, 
           disambiguation: str | None = None, 
           n: int = -1) -> str:
        """
        Translate sourceText by looking in the qm file.
        Use this to access specific context tags.

        Parameters
        ----------
        context: str 
            context tag in .ts file e.g ConfigTranslation

        sourceText: str 
            text to translate
        """
        if not self.isChinese() and self.isString(sourceText) and self.isString(context):
            bytesArgs = self.encode(context, sourceText, disambiguation)
            translation = super().translate(*bytesArgs, n)
            if translation:
                return self.toString(translation)
        return sourceText
    
    def undo(self, text: str) -> str:
        """
        Undo translations by looking in ConfigTranslation.

        Parameters
        ----------
        text: str 
            text to undo translation
        """
        if not self.isChinese() and self.isString(text) and self.__get(text):
            text = self.__get(text)
        return text


baasTranslator = Translator()
