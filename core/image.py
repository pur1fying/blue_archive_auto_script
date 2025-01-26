import cv2
import numpy as np
from core import position, color


def screenshot_cut(self, area):
    return self.latest_img_array[int(area[1] * self.ratio):int(area[3] * self.ratio), int(area[0] * self.ratio):int(area[2] * self.ratio), :]


def img_cut(img, area):
    return img[area[1]:area[3], area[0]:area[2]]


def compare_image(self, name, need_log=True, threshold=0.8, rgb_diff=20):
    if name not in position.image_dic[self.server]:
        return False
    area = position.get_area(self.server, name)
    res_img = position.image_dic[self.server][name]
    ss_img = screenshot_cut(self, area)
    res_img_average_rgb = np.mean(res_img, axis=(0, 1))
    ss_img_average_rgb = np.mean(ss_img, axis=(0, 1))
    if abs(res_img_average_rgb[0] - ss_img_average_rgb[0]) > rgb_diff or abs(
            res_img_average_rgb[1] - ss_img_average_rgb[1]) > rgb_diff or abs(
        res_img_average_rgb[2] - ss_img_average_rgb[2]) > rgb_diff:
        return False
    ss_img = cv2.resize(ss_img, (res_img.shape[1], res_img.shape[0]), interpolation=cv2.INTER_AREA)
    similarity = cv2.matchTemplate(ss_img, res_img, cv2.TM_CCOEFF_NORMED)[0][0]
    # self.logger.info(name + " : " + str(similarity))
    if need_log:
        self.logger.info(name + " : " + str(similarity))
    return similarity > threshold


def getImageByName(self, name):
    return position.image_dic[self.server][name]


def search_in_area(self, name, area=(0, 0, 1280, 720), threshold=0.8, rgb_diff=20, ret_max_val=False):
    # search image "name" in area, return upper left point of template image if found, else return False
    if name not in position.image_dic[self.server]:
        if ret_max_val:
            return False, 0
        return False
    res_img = position.image_dic[self.server][name]
    ss_img = resize_ss_image(self, area)

    similarity = cv2.matchTemplate(ss_img, res_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(similarity)
    if max_val < threshold:
        if ret_max_val:  # check rgb_diff when need ret max_val
            pass
        else:
            return False

    res_average_rgb = np.mean(res_img, axis=(0, 1))
    ss_img = img_cut(ss_img, (max_loc[0], max_loc[1], max_loc[0] + res_img.shape[1], max_loc[1] + res_img.shape[0]))
    ss_average_rgb = np.mean(ss_img, axis=(0, 1))
    if abs(res_average_rgb[0] - ss_average_rgb[0]) > rgb_diff or abs(
            res_average_rgb[1] - ss_average_rgb[1]) > rgb_diff or abs(
        res_average_rgb[2] - ss_average_rgb[2]) > rgb_diff:
        if ret_max_val:
            return False, 0  # rgb diff not match, assume not found
        return False

    if max_val < threshold and ret_max_val:
        return False, max_val

    upper_left = (max_loc[0] + area[0], max_loc[1] + area[1])
    if ret_max_val:
        return upper_left, max_val
    return upper_left


def click_to_disappear(self, img_possible, x, y):
    msg = 'find : ' + img_possible
    while self.flag_run and compare_image(self, img_possible, need_log=False):
        self.logger.info(msg)
        self.click(x, y, wait_over=True)
        self.latest_img_array = self.get_screenshot_array()
    return True


def search_image_in_area(self, image, area=(0, 0, 1280, 720), threshold=0.8, rgb_diff=20):
    # search image from screenshot in area, return upper left point of template image if found, else return False
    # image may not from 1280x720
    res_img = image
    ss_img = screenshot_cut(self, area)

    similarity = cv2.matchTemplate(ss_img, res_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(similarity)
    if max_val < threshold:
        return False

    res_average_rgb = np.mean(res_img, axis=(0, 1))
    ss_img = img_cut(ss_img, (max_loc[0], max_loc[1], max_loc[0] + res_img.shape[1], max_loc[1] + res_img.shape[0]))
    ss_average_rgb = np.mean(ss_img, axis=(0, 1))
    if abs(res_average_rgb[0] - ss_average_rgb[0]) > rgb_diff or abs(
            res_average_rgb[1] - ss_average_rgb[1]) > rgb_diff or abs(
        res_average_rgb[2] - ss_average_rgb[2]) > rgb_diff:
        return False

    upper_left = (int(max_loc[0] / self.ratio) + area[0], int(max_loc[1] / self.ratio) + area[1])
    return upper_left


def click_until_image_disappear(self, x, y, region, threshold=0.8, rgb_diff=20, click_first=True):
    image = screenshot_cut(self, region)
    if click_first:
        self.click(x, y, wait_over=True)
        self.update_screenshot_array()
    while self.flag_run and search_image_in_area(self, image, region, threshold, rgb_diff):
        self.click(x, y, wait_over=True)
        self.update_screenshot_array()


def get_image_all_appear_position(self, image_template_name, search_area=(0, 0, 1280, 720), threshold=0.8):
    if image_template_name not in position.image_dic[self.server]:
        return []
    res_img = position.image_dic[self.server][image_template_name]  # template image
    ss_img = resize_ss_image(self, search_area)  # screenshot image
    similarity = cv2.matchTemplate(ss_img, res_img, cv2.TM_CCOEFF_NORMED)
    loc = np.where(similarity >= threshold)
    res = list(zip(*loc[::-1]))
    ret = []
    for pt in res:
        ret.append((pt[0] + search_area[0], pt[1] + search_area[1]))
    return ret


def resize_ss_image(self, area, interpolation=cv2.INTER_AREA):
    # resize screenshot to template image size(720 * 1280) according to ratio
    ss_img = screenshot_cut(self, area)
    tar_size = (int(ss_img.shape[1] / self.ratio), int(ss_img.shape[0] / self.ratio))
    return cv2.resize(ss_img, tar_size, interpolation=interpolation)
