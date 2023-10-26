import os
import os
import time

from qfluentwidgets import qconfig

from core import STATIC_CONFIG_PATH, EXTEND_CONFIG_PATH, SWITCH_CONFIG_PATH, DEFAULT_CONFIG_PATH, EVENT_CONFIG_PATH, \
    DISPLAY_CONFIG_PATH
from core import default_config
from core.inject_config import Config
from core.utils import kmp
from gui.util.extend_config import ExtendConfig


def check_config():
    if not os.path.exists('./config'):
        os.mkdir('./config')
    if not os.path.exists('./config/extend.json'):
        with open('./config/extend.json', 'w', encoding='utf-8') as f:
            f.write(default_config.EXTEND_DEFAULT_CONFIG)
    if not os.path.exists('./config/static.json'):
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
    if not os.path.exists('./config/switch.json'):
        with open('./config/switch.json', 'w', encoding='utf-8') as f:
            f.write(default_config.SWITCH_DEFAULT_CONFIG)
    if not os.path.exists('./config/config.json'):
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
    if not os.path.exists('./config/event.json'):
        with open('./config/event.json', 'w', encoding='utf-8') as f:
            f.write(default_config.EVENT_DEFAULT_CONFIG)
    if not os.path.exists('./config/display.json'):
        with open('./config/display.json', 'w', encoding='utf-8') as f:
            f.write(default_config.DISPLAY_DEFAULT_CONFIG)


class Setup:
    def __init__(self):
        check_config()
        self.event_config = Config(EVENT_CONFIG_PATH)
        self.display_config = Config(DISPLAY_CONFIG_PATH)
        self.static_config = Config(STATIC_CONFIG_PATH)
        self.extend_config = Config(EXTEND_CONFIG_PATH)
        self.switch_config = Config(SWITCH_CONFIG_PATH)
        self.default_config = Config(DEFAULT_CONFIG_PATH)

        self.extend_config = ExtendConfig()
        basic_config = self.static_config.get('basic')
        self.base_time = time.time()
        self.pos = []
        self.click_time = 0.0

        self.schedule_pri = [4, 3, 2, 1, 5]  # ** 可设置参数，日程区域优先级  1 2 3 4 5 分别表示 已经出的五个区域
        self.latest_img_array = None

        # Load static config
        self.pri = basic_config['create_list']
        self.main_activity = basic_config['activity_list']
        self.main_activity_label = basic_config['activity_label_list']
        self.keyword = basic_config['keyword']
        self.schedule_lo_y = basic_config['schedule_point_list']
        self.to_page = basic_config['to_page']
        self.location_recognition_list = basic_config['location_recognition_list']

        self.keyword_apper_time_dictionary = {i: 0 for i in self.keyword}


    def return_location(self):
        for item_location in self.location_recognition_list:
            for index_recognition in range(0, len(item_location['name_list'])):
                if self.pd(item_location['name_list'][index_recognition],
                           item_location['count_list'][index_recognition]):
                    return item_location['result']
        return "UNKNOWN UI PAGE"

    def get_keyword_appear_time(self, string):
        for i in range(0, len(self.keyword)):
            self.keyword_apper_time_dictionary[self.keyword[i]] = kmp(self.keyword[i], string)

    def get_conf(self, name: str) -> any:
        return qconfig.get(self.extend_config.__dict__[name])

    def img_ocr(self, img):
        time.time()
        out = self.ocr.ocr(img)
        res = ""
        for i in range(0, len(out)):
            if out[i]["score"] > 0.6:
                res = res + out[i]["text"]
        print(res)
        return res

    def set_click_time(self):
        self.click_time = time.time() - self.base_time

    def pd(self, list1, list2):
        for i in range(0, len(list1)):
            if self.keyword_apper_time_dictionary[list1[i]] < list2[i]:
                return False
        return True
