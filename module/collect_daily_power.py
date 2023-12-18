import time
from core import stage, color, image


x = {
    'menu': (107, 9, 162, 36)
}


def implement(self, activity="collect_daily_power"):
    to_tasks(self)
    time.sleep(0.5)
    if self.server == 'CN':
        return cn_implement(self)
    elif self.server == "Global":
        return global_implement(self)


def cn_implement(self):
    while 1:
        if color.judge_rgb_range(self.latest_img_array, 1148, 691, 239, 255, 228, 248, 64, 84) and \
                color.judge_rgb_range(self.latest_img_array, 1142, 649, 239, 255, 228, 248, 64, 84):
            self.logger.info("claim reward")
            self.click(1145, 670, wait=False,duration=2)
            self.click(254, 72, wait=False)
            self.click(254, 72, wait=False)
            to_tasks(self)
        elif color.judge_rgb_range(self.latest_img_array, 1148, 691, 206, 226, 207, 227, 208, 228) and \
                color.judge_rgb_range(self.latest_img_array, 1142, 649, 206, 226, 207, 227, 208, 228):
            self.logger.info("claim all grey")
            break
        else:
            self.logger.info("Can't detect button")
            return False
    return True


def to_tasks(self):
    if self.server == 'Global':
        click_pos = [
            [70, 232],
            [910, 138],
            [254, 72],
            [889, 162],
        ]
        los = [
            "main_page",
            "insufficient_inventory_space",
            "reward_acquired",
            "full_ap_notice",
        ]
        ends = [
            "tasks",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)
    elif self.server == "CN":
        possibles = {
            "main_page_home-feature": (70, 232, 3)
        }
        image.detect(self, "work_task_menu", possibles)


def global_implement(self):
    while 1:
        if color.judge_rgb_range(self.latest_img_array, 1148, 691, 239, 255, 228, 248, 64, 84) and \
                color.judge_rgb_range(self.latest_img_array, 1142, 649, 239, 255, 228, 248, 64, 84):
            self.logger.info("claim reward")
            self.click(1145, 670, wait=False,duration=2)
            self.click(254, 72, wait=False)
            self.click(254, 72, wait=False)
            to_tasks(self)
        elif color.judge_rgb_range(self.latest_img_array, 1148, 691, 185, 205, 184, 204, 188, 208) and \
                color.judge_rgb_range(self.latest_img_array, 1142, 649, 185, 205, 184, 204, 188, 208):
            self.logger.info("claim all grey")
            break
        else:
            self.logger.info("Can't detect button")
            return False

    if color.judge_rgb_range(self.latest_img_array, 971, 689, 239, 255, 228, 248, 40, 84) and \
            color.judge_rgb_range(self.latest_img_array, 964, 649, 239, 255, 228, 248, 40, 84):
        self.click(976, 670, wait=False,duration=2)
        self.click(254, 72, wait=False)
        self.click(254, 72, wait=False)
        to_tasks(self)
    elif color.judge_rgb_range(self.latest_img_array, 959, 694, 210, 230, 210, 230, 210, 230) and \
            color.judge_rgb_range(self.latest_img_array, 957, 650, 210, 230, 210, 230, 210, 230):
        self.logger.info("claim daily pyroxenes grey")
    elif color.judge_rgb_range(self.latest_img_array, 959, 694, 112, 152, 116, 156, 119, 159) and \
            color.judge_rgb_range(self.latest_img_array, 957, 650, 112, 152, 116, 156, 119, 159):
        self.logger.info("claim daily pyroxenes complete")
    else:
        self.logger.info("Can't detect button")
        return False
    return True

