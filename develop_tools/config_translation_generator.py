""""
This is a program to generate ConfigTranslation from default_config. 
DO NOT REPLACE ConfigTranslation with the file generated because
Combobox options will be lost and the code will be less readable.
Use it instead to get a portion of default_config and paste it in ConfigTranslation.

Instructions:
go to root directory of project and enter in terminal:
python -m develop_tools.config_translation_generator
"""


import re
import json

from core.default_config import (DISPLAY_DEFAULT_CONFIG, 
                                    DEFAULT_CONFIG, 
                                    EVENT_DEFAULT_CONFIG, 
                                    STATIC_DEFAULT_CONFIG, 
                                    SWITCH_DEFAULT_CONFIG, 
                                    )


def deserialize(l):
    return [json.loads(dict) for dict in l]

def contains_chinese(s):
    return re.search("[\u4e00-\u9FFF]", s)

def find_chinese_strings(data, chinese_strings=[]):
    if isinstance(data, dict):
        for key, value in data.items():
            find_chinese_strings(value, chinese_strings)
    elif isinstance(data, list):
        for item in data:
            find_chinese_strings(item, chinese_strings)
    elif isinstance(data, str) and contains_chinese(data):
        chinese_strings.append(data)
    return chinese_strings

def remove_duplicates(chinese_strings):
    """remove duplicates while preserving order"""
    seen = set()
    seen_add = seen.add
    return [x for x in chinese_strings if not (x in seen or seen_add(x))]

def create_translation_file(chinese_strings, filename):
    with open(filename, "w") as f:
        f.write("from PyQt5.QtCore import QObject\n\n")


        f.write("class ConfigTranslation(QObject):\n")
        f.write("    def __init__(self, parent=None):\n")
        f.write("        super().__init__(parent=parent)\n")
        f.write("        self.entries = {\n")
        for s in chinese_strings:
            f.write(f"            self.tr('{s}'): '{s}',\n")
        f.write("        }\n\n")


if __name__ == "__main__":
    # data = deserialize([
    #         DISPLAY_DEFAULT_CONFIG, 
    #         DEFAULT_CONFIG, 
    #         EVENT_DEFAULT_CONFIG, 
    #         STATIC_DEFAULT_CONFIG, 
    #         SWITCH_DEFAULT_CONFIG, 
    # ])

    # chinese_strings = find_chinese_strings(data)
    # create_translation_file(chinese_strings, 'test.py')

    data = json.loads(STATIC_DEFAULT_CONFIG)
    data = data['tactical_challenge_shop_price_list']['Global']
    chinese_strings = find_chinese_strings(data)
    chinese_strings = remove_duplicates(chinese_strings)
    create_translation_file(chinese_strings, 'test.py')

