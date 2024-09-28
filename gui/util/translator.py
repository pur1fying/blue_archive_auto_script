from typing import Union
from PyQt5.QtCore import QTranslator
from gui.util.config_gui import configGui
from gui.util.config_translation import ConfigTranslation


class Translator(QTranslator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.locale = configGui.get(configGui.language).value
        self.stringLang = self.locale.name()
        self.__config_translation = None
        # separate dictionary for students to not caouse conflicts with existing translations
        self.__students = dict()

    def loadCfgTranslation(self):
        self.__config_translation = ConfigTranslation()

    def isString(self, value):
        return isinstance(value, str)

    def isBytes(self, value):
        return isinstance(value, bytes)

    def toString(self, translation: Union[str, bytes]) -> str:
        if self.isBytes(translation):
            translation = self.decode(translation)
        return translation

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
           disambiguation: Union[str, None] = None,
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

    def addStudent(self, chineseName, translatedName):
        """
        Add student's translated name to be displayed in
        hard_task_combobox in mainlinePriority
        """
        self.__students[chineseName] = translatedName

    def getStudent(self, chineseName):
        if self.__students.get(chineseName):
            return self.__students[chineseName]
        return chineseName


baasTranslator = Translator()
