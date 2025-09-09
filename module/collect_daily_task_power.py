import time

from core import color, picture


def implement(self):
    self.to_main_page()
    to_tasks(self, True)
    time.sleep(0.5)
    self.latest_img_array = self.get_screenshot_array()
    while 1:
        if color.rgb_in_range(self, 1148, 691, 239, 255, 228, 248, 64, 84) and \
            color.rgb_in_range(self, 1142, 649, 239, 255, 228, 248, 64, 84):
            self.logger.info("claim reward")
            self.click(1145, 670,  duration=2, wait_over=True)
            self.click(254, 72,  wait_over=True)
            self.click(254, 72,  wait_over=True)
            to_tasks(self)
        elif color.rgb_in_range(self, 1148, 691, 185, 227, 184, 227, 188, 228) and \
            color.rgb_in_range(self, 1142, 649, 185, 227, 184, 227, 188, 228):
            self.logger.info("claim all grey")
            break
        else:
            self.logger.info("Can't detect button")
            return True
    if color.rgb_in_range(self, 971, 689, 239, 255, 228, 248, 40, 84) and \
        color.rgb_in_range(self, 964, 649, 239, 255, 228, 248, 40, 84):
        self.click(976, 670,  duration=0.3, wait_over=True)
        self.click(254, 72,  wait_over=True)
        self.click(254, 72,  wait_over=True)
        to_tasks(self)
    elif color.rgb_in_range(self, 959, 694, 210, 230, 210, 230, 210, 230) and \
        color.rgb_in_range(self, 957, 650, 210, 230, 210, 230, 210, 230):
        self.logger.info("claim daily pyroxenes grey")
    elif color.rgb_in_range(self, 959, 694, 112, 152, 116, 156, 119, 159) and \
        color.rgb_in_range(self, 957, 650, 112, 152, 116, 156, 119, 159):
        self.logger.info("claim daily pyroxenes complete")
    else:
        self.logger.info("Can't detect button")
        return True
    return True


def to_tasks(self, skip_first_screenshot=False):
    rgb_ends = "tasks"
    rgb_possibles = {
        "main_page": (70, 232),
        "reward_acquired": (254, 72),
    }
    img_ends = "work_task_menu"
    img_possibles = {
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (910, 138),
        "main_page_home-feature": (70, 232),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)

