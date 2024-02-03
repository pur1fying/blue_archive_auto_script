import json
import threading
from core.utils import Logger
from core.ocr import ocr
from gui.util.config_set import ConfigSet


class Main:
    def __init__(self, logger_signal=None, button_signal=None, update_signal=None):
        self.static_config = None
        self.ocr = ocr.Baas_ocr(logger=Logger(logger_signal), ocr_needed=['NUM', 'CN', 'Global', 'JP'])
        self.logger = Logger(logger_signal)
        self.threads = {}

    def start_thread(self,  config, index="1", logger_signal=None, button_signal=None, update_signal=None):
        t = Baas_thread(logger_signal, button_signal, update_signal, config)
        t.static_config = self.static_config
        t.init_all_data()
        t.ocr = self.ocr
        self.threads.setdefault(index, t)
        threading.Thread(target=t.thread_starter, args=index).start()
        return True

    def init_static_config(self):
        try:
            self.logger.info("-- Start Reading Static Config --")
            self.static_config = self.operate_dict(json.load(open('config/static.json', 'r', encoding='utf-8')))
            self.logger.info("SUCCESS")
            return True
        except Exception as e:
            self.logger.error("Static Config initialization failed")
            self.logger.error(e)
            return False

    def operate_dict(self, dic):
        for key in dic:
            if type(dic[key]) is dict:
                dic[key] = self.operate_dict(dic[key])
            else:
                dic[key] = self.operate_item(dic[key])
        return dic

    def is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def operate_item(self, item):
        if type(item) is int or type(item) is bool or type(item) is float or item is None:
            return item
        if type(item) is str:
            if item.isdigit():
                return int(item)
            elif self.is_float(item):
                return float(item)
            else:
                if item.count(",") == 2:
                    temp = item.split(",")
                    for j in range(0, len(temp)):
                        if temp[j].isdigit():
                            temp[j] = int(temp[j])
                    item = temp
                return item
        else:
            temp = []
            for i in range(0, len(item)):
                if type(item[i]) is dict:
                    temp.append(self.operate_dict(item[i]))
                else:
                    temp.append(self.operate_item(item[i]))
            return temp


if __name__ == '__main__':
    from core.Baas_thread import Baas_thread
    # # print(time.time())
    t = Main()
    # t.thread_starter()
    t.init_static_config()
    # t.start_thread("1")
    # print(1)
    # t.start_thread("2", None, None, None, "config/config2")
    # print(2)
    # t.start_thread("3", None, None, None, "config/config3")
    # print(3)
    # t.start_thread("4", None, None, None, "config/config4")
    # print(4)
    config = ConfigSet(config_dir="config1")
    tt = Baas_thread(config,None,None,None)
    tt.static_config = t.static_config
    tt.init_all_data()
    tt.ocr = t.ocr
    # tt.solve("mini_story")
    tt.solve("total_assault")
