import os
import subprocess
import translators as ts

from bs4 import BeautifulSoup
from lxml import etree
from gui.util.language import Language


class Handler:
    def set_next(self, request):
        request.handlers.pop(0)
        if request.handlers:
            request.handlers[0].handle(request)

    def handle(self, request):
        pass


class Request:
    def __init__(self, handlers: list[Handler], 
                 qt_language: Language, 
                 translator: str = 'bing', 
                 from_lang: str = 'auto', 
                 to_lang: str = 'en'):
        """
        Parameters
        ----------
        handlers: list[Handler]
            a list of handlers that represent the files to translate. 

        qt_language: Language
            the memeber of the enum Language to translate

        translator: str
            see https://github.com/uliontse/translators

        from_lang: str
            see https://github.com/uliontse/translators

        to_lang: str
            see https://github.com/uliontse/translators
        """
        self.qt_language = qt_language
        self.strLang = qt_language.value.name()
        self.handlers = handlers
        self.translator = translator 
        self.from_lang = from_lang
        self.to_lang = to_lang

    def translate_text(self, text):
        text = ts.translate_text(text, self.translator, self.from_lang, self.to_lang)
        print(text)
        return text
    
    def translate_html(self, html_text):
        return ts.translate_html(html_text, self.translator, self.from_lang, self.to_lang)
    
    def process(self):
        self.handlers[0].handle(self)


class Pylupdate5Handler(Handler):
    def handle(self, request):
        result = subprocess.run(['pylupdate5', 'i18n.pro'], capture_output=True, text=True)
        print(result.stdout)
        self.set_next(request)
        

class XmlHandler(Handler):
    """Translate ts files"""
    def handle(self, request):
        # Load the XML from a file
        input_file = os.path.join('gui/i18n/', f'{request.strLang}.ts')
        output_file = os.path.join('gui/i18n/', f'{request.strLang}.ts')

        tree = etree.parse(input_file)
        root = tree.getroot()

        # Find all 'source' tags and translate their text
        for source in root.iter('source'):

            # Find the 'translation' tag within the parent 'message' tag
            translation = source.getparent().find('translation')

            # Check the 'type' attribute of the 'translation' tag
            if 'type' in translation.attrib:
                if translation.attrib['type'] == 'obsolete':
                    # Delete the parent 'message' tag if 'type' is 'obsolete'
                    source.getparent().getparent().remove(source.getparent())
                elif translation.attrib['type'] == 'unfinished' and not translation.text:
                    # Update the 'translation' tag if 'type' is not 'obsolete'
                    translation.text = request.translate_text(source.text)
            else:
                # Don't update the 'translation' tag if 'type' attribute doesn't exist
                continue

        # Write the updated XML back to the file
        tree.write(output_file, encoding='utf8')
        self.set_next(request)


class HtmlHandler(Handler):
    """Generate descriptions"""
    def translate_mission_types(self, request, input_dir, output_dir):
        input_path = os.path.join(input_dir, '各区域所需队伍属性.html')
        output_path = os.path.join(output_dir, request.translate_text('各区域所需队伍属性') + '.html')

        translations = {
            '爆发': 'Explosive',
            '贯穿': 'Piercing',
            '神秘': 'Mystic',
            '振动': 'Sonic'
        }

        with open(input_path, 'r') as f:
            text = f.read()

        for original, translated in translations.items():
            text = text.replace(original, translated)

        with open(output_path, 'w') as f:
            f.write(text)

    def handle(self, request):
        input_dir = 'src/descriptions/zh_CN/'
        output_dir = f'src/descriptions/{request.strLang}'
        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Iterate over all files in the input directory
        for filename in os.listdir(input_dir):
            if request.strLang == 'en_us' and filename == '各区域所需队伍属性.html':
                self.translate_mission_types(request, input_dir, output_dir)
                continue

            if filename.endswith('.html'):
                # Parse the HTML file with BeautifulSoup
                with open(os.path.join(input_dir, filename), 'r') as f:
                    html = f.read()
                translated_html = request.translate_html(html)
                soup = BeautifulSoup(translated_html, 'lxml')
                prettyHTML = soup.prettify()
                    
                # Write the translated HTML to the output directory
                name, extension = os.path.splitext(filename)
                output_name = f'{request.translate_text(name)}.html'
                with open(os.path.join(output_dir, output_name), 'w') as f:
                    f.write(prettyHTML)


class LreleaseHandler(Handler):
    def handle(self, request):
        directory = os.path.join(os.getcwd(), 'gui', 'i18n')
        result = subprocess.run(['lrelease', f'{request.strLang}.ts'], cwd=directory, capture_output=True, text=True)
        print(result.stdout)
        self.set_next(request)


if __name__ == "__main__":
    pylupdate = Pylupdate5Handler()
    gui = XmlHandler()
    descriptions = HtmlHandler()
    lrelease = LreleaseHandler()

    request_ko = Request([pylupdate, gui, descriptions, lrelease], Language.KOREAN, 'google', 'zh-Hans', 'ko')
    request_ko.process()

