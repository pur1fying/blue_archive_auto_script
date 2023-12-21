import json
import time
from core import STATIC_CONFIG_PATH
from core.utils import kmp
from gui.util.config_set import ConfigSet


class Setup:
    def __init__(self):
        self.base_time = time.time()
        self.pos = []
        self.ocr = None
        self.config = ConfigSet()

        self.click_time = 0.0

        self.schedule_pri = self.config.get('schedulePriority')  # ** 可设置参数，日程区域优先级  1 2 3 4 5 分别表示 已经出的五个区域
        self.latest_img_array = None

        # Load static config

    def img_ocr(self, img):  # 用于文字识别
        time.time()
        out = self.ocr.ocr(img)
        res = ""
        for i in range(0, len(out)):
            if out[i]["score"] > 0.4:
                res = res + out[i]["text"]
        return res

    def set_click_time(self):  # 用于计算点击时间，如果截图时间后于点击时间，则该图片会被判断为无效
        self.click_time = time.time() - self.base_time

    def pd(self, list1, list2):  # 用于判断关键字出现的次数是否满足要求
        for i in range(0, len(list1)):
            if self.keyword_apper_time_dictionary[list1[i]] < list2[i]:
                return False
        return True
