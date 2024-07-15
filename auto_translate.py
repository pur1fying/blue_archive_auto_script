import os
import codecs
import translatehtml

from lxml import etree
from argostranslate import package, translate

from gui.util.language import Language


class Handler:
    def set_next(self, request):
        request.handlers.pop(0)
        if request.handlers:
            request.handlers[0].handle(request)

    def handle(self, request):
        pass


class Request:
    from_code = "zh"
    def __init__(self, handlers: list[Handler], language: Language, argos_model: str):
        """
        Parameters
        ----------
        handlers: list[Handler]
            a list of handlers that represent the the files to translate. 

        language: Language
            the memeber of the enum Language to translate

        argos_model: str 
            The argos model to load for translation
        """
        self.language = language
        self.strLang = language.value.name()
        self.handlers = handlers
        self.to_code = argos_model
        self.model = None

    def translate(self, text):
        translation = self.model.translate(text)
        print(translation)
        return translation
    
    def process(self):
        self.handlers[0].handle(self)


class ModelHandler(Handler):
    """Load argos model. It must always be the first element in the list of handlers"""
    def handle(self, request):
        # Load Argos Translate model
        to_code = request.to_code

        available_packages = package.get_available_packages()
        available_package = list(
            filter(
                lambda x: x.from_code == request.from_code and x.to_code == to_code, available_packages
            )
        )[0]
        download_path = available_package.download()
        package.install_from_path(download_path)

        # Translate
        installed_languages = translate.get_installed_languages()
        from_lang = list(filter(lambda x: x.code == request.from_code, installed_languages))[0]
        to_lang = list(filter(lambda x: x.code == to_code, installed_languages))[0]

        request.model = from_lang.get_translation(to_lang)
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
                    translation.text = request.translate(source.text)
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
        output_path = os.path.join(output_dir, request.translate('各区域所需队伍属性') + '.html')

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
        input_dir = 'src/descriptions/'
        output_dir = f'src/descriptions_{request.strLang}'
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
                with codecs.open(os.path.join(input_dir, filename), 'r', 'utf-8') as f_in:

                    # Translate all text in the HTML file
                    soup = translatehtml.translate_html(request.model, f_in)

                    # Write the translated HTML to the output directory
                    name, extension = os.path.splitext(filename)
                    output_name = f'{request.translate(name)}.html'
                    with codecs.open(os.path.join(output_dir, output_name), 'w', 'utf-8') as f_out:
                        f_out.write(str(soup.prettify()))
        

if __name__ == "__main__":
    model = ModelHandler()
    ts = XmlHandler()
    descriptions = HtmlHandler()

    request_en = Request([model, ts], Language.ENGLISH, 'en')
    request_en.process()

