import random
import time
import cv2
import numpy as np
from core import position, color


def screenshot_cut(self, area):
    return self.latest_img_array[int(area[1]*self.ratio):int(area[3]*self.ratio), int(area[0]*self.ratio):int(area[2]*self.ratio), :]


def compare_image(self, name, need_log=True, threshold=0.8, rgb_diff=20):
    if name not in position.image_dic[self.server]:
        return False
    area = get_area(self.server, name)
    res_img = position.image_dic[self.server][name]
    ss_img = screenshot_cut(self, area)
    res_img_average_rgb = np.mean(res_img, axis=(0, 1))
    ss_img_average_rgb = np.mean(ss_img, axis=(0, 1))
    if abs(res_img_average_rgb[0] - ss_img_average_rgb[0]) > rgb_diff or abs(res_img_average_rgb[1] - ss_img_average_rgb[1]) > rgb_diff or abs(res_img_average_rgb[2] - ss_img_average_rgb[2]) > rgb_diff:
        return False
    ss_img = cv2.resize(ss_img, (res_img.shape[1], res_img.shape[0]), interpolation=cv2.INTER_AREA)
    similarity = cv2.matchTemplate(ss_img, res_img, cv2.TM_CCOEFF_NORMED)[0][0]
    # self.logger.info(name + " : " + str(similarity))
    if need_log:
        self.logger.info(name + " : " + str(similarity))
    return similarity > threshold


def detect(self, end=None, possibles=None, pre_func=None, pre_argv=None, skip_first_screenshot=False):
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
                if compare_image(self, end, need_log=False):
                    self.logger.info('end : ' + end)
                    return end
            elif type(end) is list:
                for asset in end:
                    if compare_image(self, asset[0],  need_log=False):
                        self.logger.info('end : ' + asset[0])
                        return asset[0]
        if possibles is not None:
            for asset, obj in possibles.items():
                if compare_image(self, asset,  need_log=False):
                    if type(obj[0]) is int:
                        self.logger.info("find : " + asset)
                        self.click(obj[0], obj[1])
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
