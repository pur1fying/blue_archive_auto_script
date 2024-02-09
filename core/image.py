import random
import time
import cv2
import numpy as np
from core import position, color


def screenshot_cut(self, area, image=None):
    if len(area) == 0:
        return self.get_screenshot_array()
    else:
        if image is None:
            self.latest_img_array = self.get_screenshot_array()
            return self.latest_img_array[area[1]:area[3], area[0]:area[2], :]
        else:
            return image[area[1]:area[3], area[0]:area[2], :]


def compare_image(self, name, threshold=10, need_loading=False, image=None, need_log=True):
    if need_loading:
        color.wait_loading(self)
    if name not in position.image_dic[self.server]:
        return False
    area = get_area(self.server, name)
    res_img = position.image_dic[self.server][name]
    ss_img = screenshot_cut(self, area=area, image=image)
    diff = cv2.absdiff(ss_img, res_img)
    mean_diff = np.mean(diff)
    compare = mean_diff <= threshold
    if need_log:
        self.logger.info(f"compare_image {name} Mean Difference: {mean_diff} Result:{compare}")
    return compare


def detect(self, end=None, possibles=None, pre_func=None, pre_argv=None, skip_first_screenshot=False):
    # self.logger.info("Start detecting image possibles :{0}, end:{1}".format(possibles, end))
    while True:
        if not self.flag_run:
            return False
        if skip_first_screenshot:
            skip_first_screenshot = False
        else:
            color.wait_loading(self)
        if pre_func is not None:
            res = pre_func(*pre_argv)
            if not res:
                pass
            elif res[0] == 'end':
                return res[1]
            elif res[0] == 'click':
                continue
        if end is not None:
            if type(end) is str:
                if compare_image(self, end, 10, image=self.latest_img_array, need_log=False):
                    self.logger.info('end : ' + end)
                    return end
            elif type(end) is list:
                for asset in end:
                    if type(asset) is str:
                        asset = (asset, 3)
                    threshold = asset[1]
                    if compare_image(self, asset[0], threshold, image=self.latest_img_array, need_log=False):
                        self.logger.info('end : ' + asset[0])
                        return asset[0]
        if possibles is not None:
            for asset, obj in possibles.items():
                threshold = 3
                if len(obj) >= 3:
                    threshold = obj[2]
                if compare_image(self, asset, threshold, image=self.latest_img_array, need_log=False):
                    if type(obj[0]) is int:
                        self.logger.info("find : " + asset)
                        self.click(obj[0], obj[1], False)
                        self.latest_screenshot_time = time.time()
                    else:
                        if obj[0](*obj[1]):
                            return asset
                    break


def get_area(server, name):
    module, name = name.rsplit("_", 1)
    if position.image_x_y_range[server][module][name] is None:
        return False
    return position.image_x_y_range[server][module][name]


def process_image(self, img, name, threshold=10, step=5):
    area = get_area(name)
    width, height = area.shape[1], area.shape[0]
    ss_img = screenshot_cut(self, area=area, image=img)
    total_cnt = 0
    correct_cnt = 0
    for x in range(0, width, step):
        for y in range(0, height, step):
            total_cnt += 1
            random_x = random.randint(x, min(x + step - 1, width - 1))
            random_y = random.randint(y, min(y + step - 1, height - 1))
            r_max = img
