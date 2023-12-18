import time

import cv2
import numpy as np

from core import stage, position


def screenshot_cut(self, area, image=None):
    if len(area) == 0:
        return self.get_screenshot_array()
    else:
        if image is None:
            self.latest_img_array = self.get_screenshot_array()
            return self.latest_img_array[area[1]:area[3], area[0]:area[2], :]
        else:
            return image[area[1]:area[3], area[0]:area[2], :]


def compare_image(self, name, threshold=3, need_loading=False, image=None, need_log=True):
    if need_loading:
        stage.wait_loading(self)
    area = get_area(name)
    ss_img = screenshot_cut(self, area=area, image=image)
    res_img = position.iad[name]
    diff = cv2.absdiff(ss_img, res_img)
    mse = np.mean(diff ** 2)
    compare = mse <= threshold
    if need_log:
        self.logger.info("compare_image %s mse: %s Result:%s", name, mse, compare)
    return compare


def detect(self, end=None, possibles=None, pre_func=None, pre_argv=None):
    self.logger.info("Start detecting image possibles :{0}, end:{1}".format(possibles, end))
    while True:
        self.wait_loading()
        self.latest_img_array = self.get_screenshot_array()  # 每次公用一张截图
        if pre_func is not None:
            res = pre_func(*pre_argv)
            if not res:
                pass
            elif res[0] == 'end':
                return res[1]
            elif res[0] == 'click':
                time.sleep(self.screenshot_interval)
                continue
        if end is not None:
            if type(end) is str:
                if compare_image(self, end, 3, image=self.latest_img_array, need_log=False):
                    return end
            elif type(end) is list:
                for asset in end:
                    if type(asset) is str:
                        asset = (asset, 3)
                    threshold = asset[1]
                    if compare_image(self, asset[0], threshold, image=self.latest_img_array,need_log=False):
                        return asset[0]

        if possibles is not None:
            for asset, obj in possibles.items():
                threshold = 3
                if len(obj) >= 3:
                    threshold = obj[2]
                if compare_image(self, asset, threshold, image=self.latest_img_array, need_log=False):
                    if type(obj[0]) is int:
                        self.click(obj[0], obj[1], False)
                        time.sleep(self.screenshot_interval)
                    else:
                        if obj[0](*obj[1]):
                            return asset
                    break
        time.sleep(self.screenshot_interval)


def get_area(name):
    module, name = name.rsplit("_", 1)
    return position.ibd[module][name]
