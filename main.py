import json
import os
import time

from core.utils import Logger
from core.ocr import ocr
from core.config.config_set import ConfigSet
from core.Baas_thread import Baas_thread
from core import picture, color


class Main:
    def __init__(self, logger_signal=None, ocr_needed=None):
        self.ocr_needed = ocr_needed
        self.ocr = None
        self.logger = Logger(logger_signal)
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        self.logger.info(self.project_dir)
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
            self.logger.error(e.__str__())
            return False

    def get_thread(self, config, name="1", logger_signal=None, button_signal=None, update_signal=None,
                   exit_signal=None):
        t = Baas_thread(config, logger_signal, button_signal, update_signal, exit_signal)
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
            self.static_config = self.operate_dict(
                json.load(open(self.project_dir + "/config/static.json", 'r', encoding='utf-8')))
            return True
        except Exception as e:
            self.logger.error("Static Config initialization failed")
            self.logger.error(e.__str__())
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
    ocr_needed = ["Global", "CN", "JP", "NUM"]
    INSTANCE = Main(ocr_needed=ocr_needed)
    config = ConfigSet(config_dir="default_config")
    bThread = Baas_thread(config, None, None, None)
    bThread.init_all_data()
    bThread.ocr = INSTANCE.ocr

    # from module import create
    # create.create_phase(bThread, 3)

    # create.select_node(bThread, 1)

    # print(json.dumps(res, indent=4))
    # print(len(res))
    # exit(0)
    # bThread.thread_starter()
    # bThread.solve("refresh_uiautomator2")
    # bThread.solve("explore_activity_challenge")
    # bThread.solve("activity_sweep")
    # bThread.solve("tactical_challenge_shop")
    # bThread.solve("explore_activity_mission")
    # bThread.solve("explore_activity_story")
    # bThread.solve("common_shop")
    # bThread.solve("total_assault")
    # bThread.solve("cafe_reward")
    # bThread.solve("momo_talk")
    # bThread.solve("explore_normal_task")
    # bThread.solve("explore_hard_task")
    # bThread.solve("normal_task")
    # bThread.solve("hard_task")
    # bThread.solve("arena")
    # bThread.solve("lesson")
    # bThread.solve("group")
    # bThread.solve("mail")
    # bThread.solve("collect_reward")
    # bThread.solve("main_story")
    # bThread.solve("group_story")
    # bThread.solve("mini_story")
    # bThread.solve("clear_special_task_power")
    # bThread.solve("scrimmage")
    # bThread.solve("rewarded_task")
    # bThread.solve("create")
    # bThread.solve("dailyGameActivity")
    # bThread.solve("friend")
    bThread.solve("joint_firing_drill")
