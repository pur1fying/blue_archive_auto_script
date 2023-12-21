import time

from core import color
from module import explore_normal_task
import importlib


def implement(self):
    if self.server == "CN":
        explore_normal_task.implement(self)
    elif self.server == "Global":
        self.logger.info("Global server not support")


def choose_mod(self):
    while not color.judge_rgb_range(self.latest_img_array, 961, 148, 188, 208, 56, 76, 55, 75):
        self.click(1185, 147)
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()


def get_stage_data(region):
    module_path = 'src.explore_task_data.hard_task_' + str(region)
    stage_module = importlib.import_module(module_path)
    stage_data = getattr(stage_module, 'stage_data', None)
    return stage_data
