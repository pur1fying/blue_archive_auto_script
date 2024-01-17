import time

from core import color, picture


def implement(self, activity="collect_daily_power"):
    self.quick_method_to_main_page()
    to_tasks(self, True)
    time.sleep(0.5)
    while 1:
        if color.judge_rgb_range(self.latest_img_array, 1148, 691, 239, 255, 228, 248, 64, 84) and \
            color.judge_rgb_range(self.latest_img_array, 1142, 649, 239, 255, 228, 248, 64, 84):
            self.logger.info("claim reward")
            self.click(1145, 670, wait=False, duration=2, wait_over=True)
            self.click(254, 72, wait=False, wait_over=True)
            self.click(254, 72, wait=False, wait_over=True)
            to_tasks(self)
        elif color.judge_rgb_range(self.latest_img_array, 1148, 691, 185, 227, 184, 227, 188, 228) and \
            color.judge_rgb_range(self.latest_img_array, 1142, 649, 185, 227, 184, 227, 188, 228):
            self.logger.info("claim all grey")
            break
        else:
            self.logger.info("Can't detect button")
            return True
    if self.server == "Global" or self.server == 'JP':
        if color.judge_rgb_range(self.latest_img_array, 971, 689, 239, 255, 228, 248, 40, 84) and \
            color.judge_rgb_range(self.latest_img_array, 964, 649, 239, 255, 228, 248, 40, 84):
            self.click(976, 670, wait=False, duration=2, wait_over=True)
            self.click(254, 72, wait=False, wait_over=True)
            self.click(254, 72, wait=False, wait_over=True)
            to_tasks(self)
        elif color.judge_rgb_range(self.latest_img_array, 959, 694, 210, 230, 210, 230, 210, 230) and \
            color.judge_rgb_range(self.latest_img_array, 957, 650, 210, 230, 210, 230, 210, 230):
            self.logger.info("claim daily pyroxenes grey")
        elif color.judge_rgb_range(self.latest_img_array, 959, 694, 112, 152, 116, 156, 119, 159) and \
            color.judge_rgb_range(self.latest_img_array, 957, 650, 112, 152, 116, 156, 119, 159):
            self.logger.info("claim daily pyroxenes complete")
        else:
            self.logger.info("Can't detect button")
            return True
    return True


def to_tasks(self, skip_first_screenshot=False):
    rgb_ends = "tasks"
    rgb_possibles = {
        "main_page": (70, 232),
        "insufficient_inventory_space": (910, 138),
        "reward_acquired": (254, 72),
        "full_ap_notice": (889, 162),
    }
    img_ends = "work_task_menu"
    img_possibles = {
        "main_page_home-feature": (70, 232),
        'main_page_full-notice': (887, 165),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)

