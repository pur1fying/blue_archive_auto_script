import cv2
import numpy as np
from core import position, color


def screenshot_cut(self, area):
    # template is from 1280 * 720 screenshot, if real screenshot is 2560 * 1440, then ratio is 2.0
    # cut the same area from real screenshot
    return self.latest_img_array[int(area[1] * self.ratio):int(area[3] * self.ratio),
           int(area[0] * self.ratio):int(area[2] * self.ratio), :]


def img_cut(img, area):
    # cut image from area, don't consider ratio
    return img[area[1]:area[3], area[0]:area[2]]


def compare_image(self, name, threshold=0.8, rgb_diff=20):
    if name not in position.image_dic[self.server]:  # template image not found
        return False
    area = position.get_area(self.server, name)
    template_img = position.image_dic[self.server][name]
    ss_img = screenshot_cut(self, area)
    if not compare_image_rgb(template_img, ss_img, rgb_diff=rgb_diff):
        return False
    ss_img = cv2.resize(ss_img, (template_img.shape[1], template_img.shape[0]), interpolation=cv2.INTER_AREA)
    # ss_img and template_img have the same size, similarity is a float
    similarity = cv2.matchTemplate(ss_img, template_img, cv2.TM_CCOEFF_NORMED)[0][0]
    return similarity > threshold


def getImageByName(self, name):
    return position.image_dic[self.server][name]


def search_in_area(self, name, area=(0, 0, 1280, 720), threshold=0.8, rgb_diff=20, ret_max_val=False):
    # search image "name" in area, return upper left point of template image if found, else return False
    if name not in position.image_dic[self.server]:
        if ret_max_val:
            return False, 0
        return False
    template_img = position.image_dic[self.server][name]
    ss_img = resize_ss_image(self, area)

    similarity = cv2.matchTemplate(ss_img, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(similarity)
    if max_val < threshold:
        if ret_max_val:  # check rgb_diff when need ret max_val
            pass
        else:
            return False

    ss_img = img_cut(ss_img, (max_loc[0], max_loc[1], max_loc[0] + template_img.shape[1], max_loc[1] + template_img.shape[0]))
    if not compare_image_rgb(template_img, ss_img, rgb_diff=rgb_diff):
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
    while self.flag_run and compare_image(self, img_possible):
        self.logger.info(msg)
        self.click(x, y, wait_over=True)
        self.latest_img_array = self.get_screenshot_array()
    return True


def search_image_in_area(self, image, area=(0, 0, 1280, 720), threshold=0.8, rgb_diff=20):
    # search image from screenshot in area, return upper left point of template image if found, else return False
    # image may not from 1280x720
    template_img = image
    ss_img = screenshot_cut(self, area)

    similarity = cv2.matchTemplate(ss_img, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(similarity)
    if max_val < threshold:
        return False
    ss_img = img_cut(ss_img,(max_loc[0], max_loc[1], max_loc[0] + template_img.shape[1], max_loc[1] + template_img.shape[0]))
    if not compare_image_rgb(template_img, ss_img, rgb_diff=rgb_diff):
        return False
    upper_left = (int(max_loc[0] / self.ratio) + area[0], int(max_loc[1] / self.ratio) + area[1])
    return upper_left


def compare_image_rgb(img1, img2, rgb_diff=20):
    # check if img average rgb are similar
    img1_average_rgb = np.mean(img1, axis=(0, 1))
    img2_average_rgb = np.mean(img2, axis=(0, 1))
    if compare_rgb(img1_average_rgb, img2_average_rgb, rgb_diff):
        return True
    return False


def compare_rgb(rgb1, rgb2, rgb_diff):
    # check if two rgb are similar
    if (
            abs(rgb1[0] - rgb2[0]) > rgb_diff or
            abs(rgb1[1] - rgb2[1]) > rgb_diff or
            abs(rgb1[2] - rgb2[2]) > rgb_diff
    ):
        return False
    return True


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
    template_img = position.image_dic[self.server][image_template_name]  # template image
    ss_img = resize_ss_image(self, search_area)  # screenshot image
    similarity = cv2.matchTemplate(ss_img, template_img, cv2.TM_CCOEFF_NORMED)
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
