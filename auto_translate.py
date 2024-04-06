import os
import sys
from lxml import etree
from argostranslate import package, translate
import translatehtml
import codecs

# Load Argos Translate model
from_code = "zh"
to_code = "en"

available_packages = package.get_available_packages()
available_package = list(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    )
)[0]
download_path = available_package.download()
package.install_from_path(download_path)

# Translate
installed_languages = translate.get_installed_languages()
from_lang = list(filter(lambda x: x.code == from_code, installed_languages))[0]
to_lang = list(filter(lambda x: x.code == to_code, installed_languages))[0]

MODEL = from_lang.get_translation(to_lang)

def translate_to_english(text):
    result = MODEL.translate(text)
    print(result)
    return result

def translate_xml(input_file, output_file):
    # Load the XML from a file
    tree = etree.parse(input_file)
    root = tree.getroot()

    # Find all 'source' tags and translate their text
    for source in root.iter('source'):
        source_text = source.text
        translated_text = translate_to_english(source_text)

        # Find the 'translation' tag within the parent 'message' tag
        translation = source.getparent().find('translation')

        # Check the 'type' attribute of the 'translation' tag
        if 'type' in translation.attrib:
            if translation.attrib['type'] == 'obsolete':
                # Delete the parent 'message' tag if 'type' is 'obsolete'
                source.getparent().getparent().remove(source.getparent())
            else:
                # Update the 'translation' tag if 'type' is not 'obsolete'
                translation.text = translated_text
        else:
            # Don't update the 'translation' tag if 'type' attribute doesn't exist
            continue

    # Write the updated XML back to the file
    tree.write(output_file, encoding='utf8')


def translate_mission_types(input_dir, output_dir):
    input_path = os.path.join(input_dir, '各区域所需队伍属性.html')
    output_path = os.path.join(output_dir, translate_to_english('各区域所需队伍属性') + '.html')

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


def translate_html_files(input_dir, output_dir):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Iterate over all files in the input directory
    for filename in os.listdir(input_dir):
        if filename == '各区域所需队伍属性.html':
            translate_mission_types(input_dir, output_dir)
            continue

        if filename.endswith('.html'):
            # Parse the HTML file with BeautifulSoup
            with codecs.open(os.path.join(input_dir, filename), 'r', 'utf-8') as f_in:

                # Translate all text in the HTML file
                soup = translatehtml.translate_html(MODEL, f_in)

                # Write the translated HTML to the output directory
                name, extension = os.path.splitext(filename)
                output_name = f'{translate_to_english(name)}.html'
                with codecs.open(os.path.join(output_dir, output_name), 'w', 'utf-8') as f_out:
                    f_out.write(str(soup.prettify()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python auto_translate.py [gui|descriptions]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == 'gui':
        translate_xml("gui/i18n/en_US.ts", 'gui/i18n/en_US.ts')
    elif mode == 'descriptions':
        translate_html_files("src/descriptions", "src/descriptions_en_US")
    else:
        print("Invalid mode. Use 'gui' or 'descriptions'.")
        sys.exit(1)
