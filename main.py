import json
from core.utils import Logger
from core.ocr import ocr
from gui.util.config_set import ConfigSet
from core.Baas_thread import Baas_thread


class Main:
    def __init__(self, logger_signal=None, ocr_needed=None):
        self.ocr_needed = ocr_needed
        self.ocr = None
        self.static_config = None
        self.logger = Logger(logger_signal)
        self.init_all_data()
        self.threads = {}

    def init_all_data(self):
        self.init_ocr()
        self.init_static_config()
        self.logger.info("-- All Data Initialization Complete Script ready--")

    def init_ocr(self):
        try:
            self.ocr = ocr.Baas_ocr(logger=self.logger, ocr_needed=self.ocr_needed)
            return True
        except Exception as e:
            self.logger.error("OCR initialization failed")
            self.logger.error(e)
            return False

    def get_thread(self, config, name="1", logger_signal=None, button_signal=None, update_signal=None):
        t = Baas_thread(config, logger_signal, button_signal, update_signal)
        t.static_config = self.static_config
        t.ocr = self.ocr
        self.threads.setdefault(name, t)
        return t

    def stop_script(self, name):
        if name in self.threads:
            self.threads[name].flag_run = False
            del self.threads[name]
            return True
        else:
            return False

    def init_static_config(self):
        try:
            self.static_config = self.operate_dict(json.load(open('config/static.json', 'r', encoding='utf-8')))
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
    t = Main(ocr_needed=["NUM", "CN", "Global"])
    t.init_static_config()
    config = ConfigSet(config_dir="default_config")
    tt = Baas_thread(config, None, None, None)
    tt.static_config = t.static_config
    tt.init_all_data()
    tt.ocr = t.ocr
    # tt.solve("refresh_uiautomator2")
    # tt.solve("explore_activity_challenge")
    # tt.solve("activity_sweep")
    # tt.solve("explore_activity_mission")
    # tt.solve("explore_activity_story")
    # tt.solve("common_shop")
    tt.solve("total_assault")
    # tt.solve("cafe_reward")
    # tt.solve("momo_talk")
    # tt.solve("explore_normal_task")
    # tt.solve("explore_hard_task")
    # tt.solve("normal_task")
    # tt.solve("hard_task")
    # tt.solve("arena")
    # tt.solve("lesson")
    # tt.solve("group")
    # tt.solve("mail")
    # tt.solve("collect_reward")
    # tt.solve("main_story")
    # tt.solve("group_story")
    # tt.solve("clear_special_task_power")
    # tt.solve("scrimmage")
    # tt.solve("rewarded_task")
    # tt.solve("create")
