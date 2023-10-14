import json
import time
from cnocr import CnOcr

from core.utils import kmp
from gui.util.extend_config import ExtendConfig

from qfluentwidgets import qconfig


def _read_static_config():
    with open('./core/static.json', 'r', encoding='utf-8') as f:
        return json.load(f)


class Setup:
    def __init__(self):
        self.extend_config = ExtendConfig()
        qconfig.load('./gui/config/extend.json', self.extend_config)
        static_config = _read_static_config()
        basic_config = static_config['basic']
        self.base_time = time.time()
        self.pos = []
        self.click_time = 0.0

        self.schedule_pri = [4, 3, 2, 1, 5]  #** 可设置参数，日程区域优先级  1 2 3 4 5 分别表示 已经出的五个区域
        self.ocr = CnOcr(rec_model_name='densenet_lite_114-fc')
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
