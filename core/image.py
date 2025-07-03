from statistics import median
from typing import Sequence

import cv2
import numpy as np

from core import position
from core.utils import merge_nearby_coordinates


def screenshot_cut(self, area):
    # template is from 1280 * 720 screenshot, if real screenshot is 2560 * 1440, then ratio is 2.0
    # cut the same area from real screenshot
    return self.latest_img_array[
           int(area[1] * self.ratio):int(area[3] * self.ratio),
           int(area[0] * self.ratio):int(area[2] * self.ratio), :]


def img_cut(img, area):
    # cut image from area, don't consider ratio
    return img[area[1]:area[3], area[0]:area[2]]


def compare_image(self, name, threshold=0.8, rgb_diff=20):
    if name not in position.image_dic[self.identifier]:  # template image not found
        return False
    area = position.get_area(self.identifier, name)
    template_img = position.image_dic[self.identifier][name]
    ss_img = screenshot_cut(self, area)
    if not compare_image_rgb(template_img, ss_img, rgb_diff=rgb_diff):
        return False
    ss_img = cv2.resize(ss_img, (template_img.shape[1], template_img.shape[0]), interpolation=cv2.INTER_AREA)
    # ss_img and template_img have the same size, similarity is a float
    similarity = cv2.matchTemplate(ss_img, template_img, cv2.TM_CCOEFF_NORMED)[0][0]
    return similarity > threshold


def getImageByName(self, name):
    return position.image_dic[self.identifier][name]


def search_in_area(self, name, area=(0, 0, 1280, 720), threshold=0.8, rgb_diff=20, ret_max_val=False):
    # search image "name" in area, return upper left point of template image if found, else return False
    if name not in position.image_dic[self.identifier]:
        if ret_max_val:
            return False, 0
        return False
    template_img = position.image_dic[self.identifier][name]
    ss_img = resize_ss_image(self, area)

    similarity = cv2.matchTemplate(ss_img, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(similarity)
    if max_val < threshold:
        if ret_max_val:  # check rgb_diff when need ret max_val
            pass
        else:
            return False

    ss_img = img_cut(ss_img,
                     (max_loc[0], max_loc[1], max_loc[0] + template_img.shape[1], max_loc[1] + template_img.shape[0]))
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
    ss_img = img_cut(ss_img,
                     (max_loc[0], max_loc[1], max_loc[0] + template_img.shape[1], max_loc[1] + template_img.shape[0]))
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


def click_until_template_disappear(self, name, x, y, threshold=0.8, rgb_diff=20, click_first=True):
    if click_first:
        self.click(x, y, wait_over=True)
        self.update_screenshot_array()
    while self.flag_run and compare_image(self, name, threshold, rgb_diff):
        self.click(x, y, wait_over=True)
        self.update_screenshot_array()


def get_image_all_appear_position(self, image_template_name, search_area=(0, 0, 1280, 720), threshold=0.8):
    if image_template_name not in position.image_dic[self.identifier]:
        return []
    template_img = position.image_dic[self.identifier][image_template_name]  # template image
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


def swipe_search_target_str(
    self,
    name,
    search_area=(0, 0, 1280, 720),
    threshold=0.8,
    possible_strs=None,
    target_str_index=0,
    swipe_params=(0, 0, 0, 0, 0.0, 0.0),
    ocr_language='en-us',
    ocr_region_offsets=(0, 0, 0, 0),
    ocr_str_replace_func=None,
    max_swipe_times=3,
    ocr_candidates="",
    ocr_filter_score=0.2,
    first_retry_dir=0
):
    temp = len(swipe_params)
    if temp < 4:
        raise ValueError("swipe_params must have at least 4 elements.")
    if temp == 4:
        swipe_params = (
            swipe_params[0], swipe_params[1],
            swipe_params[2], swipe_params[3],
            0.5, 0.0
        )
    elif temp == 5:
        swipe_params = (
            swipe_params[0], swipe_params[1],
            swipe_params[2], swipe_params[3],
            swipe_params[4],
            0.0
        )
    reversed_swipe_params = (
        swipe_params[2], swipe_params[3],
        swipe_params[0], swipe_params[1],
        swipe_params[4],
        swipe_params[5]
    )
    retry_swipe_dir = first_retry_dir
    if possible_strs is None:
        raise ValueError("possible_strs can't be None.")
    target_str = possible_strs[target_str_index]
    self.logger.info(f"Swipe Searching for \"{target_str}\".")
    self.logger.info("Possible strings : ")
    for i in range(len(possible_strs)):
        self.logger.info(possible_strs[i])
    for time in range(max_swipe_times):
        if time != 0:  # skip first screenshot
            self.update_screenshot_array()
        all_positions = get_image_all_appear_position(self, name, search_area, threshold)
        if len(all_positions) == 0:
            self.logger.warning("Didn't find target image, try swipe.")
            if retry_swipe_dir == 0:
                self.swipe(*swipe_params)
            else:
                self.swipe(*reversed_swipe_params)
            retry_swipe_dir ^= 1
            continue
        all_positions = merge_nearby_coordinates(all_positions, 5, 5)
        max_idx = -1  # impossible value
        min_idx = len(possible_strs)
        all_strs = []
        for pos in all_positions:
            x_coords = [coord[0] for coord in pos]
            y_coords = [coord[1] for coord in pos]
            p = (median(x_coords), median(y_coords))
            ocr_region = (
                p[0] + ocr_region_offsets[0],
                p[1] + ocr_region_offsets[1],
                p[0] + ocr_region_offsets[0] + ocr_region_offsets[2],
                p[1] + ocr_region_offsets[1] + ocr_region_offsets[3]
            )
            # img = screenshot_cut(self, ocr_region)
            # cv2.imshow("img", img)
            # cv2.waitKey(0)
            ocr_str = self.ocr.get_region_res(
                baas=self,
                region=ocr_region,
                language=ocr_language,
                candidates=ocr_candidates,
                filter_score=ocr_filter_score
            )
            # check twice, before replace and after replace
            all_strs.append(ocr_str)
            if ocr_str == target_str:
                self.logger.info(f"Found \"{target_str}\" at {p}.")
                return p
            if ocr_str in possible_strs:
                idx = possible_strs.index(ocr_str)
                max_idx = max(max_idx, idx)
                min_idx = min(min_idx, idx)
                continue
            if ocr_str_replace_func is None:
                continue
            ocr_str = ocr_str_replace_func(ocr_str)
            if ocr_str == target_str:
                self.logger.info(f"Found \"{target_str}\" (replaced) at {p}.")
                return p
            if ocr_str in possible_strs:
                idx = possible_strs.index(ocr_str)
                max_idx = max(max_idx, idx)
                min_idx = min(min_idx, idx)
        self.logger.info(f"All detected strings: {all_strs}.")
        if max_idx != -1:
            if target_str_index > max_idx:
                self.logger.info(f"Target idx {target_str_index} > max idx {max_idx}.")
                self.swipe(*swipe_params)
                continue
        if min_idx != len(possible_strs):
            if target_str_index < min_idx:
                self.logger.info(f"Target idx {target_str_index} < min idx {min_idx}.")
                self.logger.info("Swipe Backward.")
                self.swipe(*reversed_swipe_params)
                continue
        self.logger.warning("Didn't find target string, try swipe.")
        if retry_swipe_dir == 0:
            self.swipe(*swipe_params)
        else:
            self.swipe(*reversed_swipe_params)
        retry_swipe_dir ^= 1


def match_template_CCORR_NORMED(source_img: np.ndarray,
                                template_img: np.ndarray,
                                threshold: float = 0.85,
                                ignore_transparent: bool = True) -> tuple[bool, Sequence[int], float]:
    """
    Uses the TM_CCORR_NORMED method for template matching and returns the best match location and best score.
    Args:
        source_img (np.ndarray): The image to search in.
        template_img (np.ndarray): The template to search for.
        threshold (float, optional): The threshold for matchTemplate, larger values are stricter. Defaults to 0.85.
        ignore_transparent (bool, optional): If True, ignores the transparent area in the template image. Defaults to True.
    Returns:
        Tuple[bool, Sequence[int], float]:
            - bool: True if a match is found(max_val > threshold), False otherwise.
            - Sequence[int]: (x, y) coordinates of the top-left corner, or (-1, -1) if source_img or template_img is None.
            - float: The matching score(max_val).
    """
    if source_img is None or template_img is None:
        # print("Source or template image is None.")
        return False, (-1, -1), -1.0

    # if the source image is smaller than the template, resize the template img
    template_img = resize_template(template_img, source_img)

    mask = np.ones(template_img.shape[:2], dtype="uint8") * 255
    # if the template image has an alpha channel, and we want to ignore transparent areas
    if template_img.shape[2] == 4 and ignore_transparent:
        # create a mask from the alpha channel
        alpha = template_img[:, :, 3]
        mask = (alpha > 0).astype("uint8") * 255

    # convert image to BGR.
    source_img = convert_to_bgr(source_img)
    template_img = convert_to_bgr(template_img)

    res = cv2.matchTemplate(source_img, template_img, cv2.TM_CCORR_NORMED, mask=mask)

    # we ignore min_val and min_loc here, as we are using TM_CCORR_NORMED, in which larger values are better.
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        return True, max_loc, max_val
    else:
        return False, max_loc, max_val


def match_template_CCOEFF_NORMED(source_img: np.ndarray,
                                 template_img: np.ndarray,
                                 threshold: float = 0.85) -> tuple[bool, Sequence[int], float]:
    """
    Uses the TM_CCOEFF_NORMED method for template matching and returns the best match location and best score.
    Args:
        source_img (np.ndarray): The image to search in.
        template_img (np.ndarray): The template to search for.
        threshold (float, optional): The threshold for matchTemplate, larger values are stricter. Defaults to 0.85.
    Returns:
        Tuple[bool, Sequence[int], float]:
            - bool: True if a match is found(max_val > threshold), False otherwise.
            - Sequence[int]: (x, y) coordinates of the top-left corner, or (-1, -1) if source_img or template_img is None.
            - float: The matching score(max_val).
    """

    if source_img is None or template_img is None:
        # print("Source or template image is None.")
        return False, (-1, -1), -1.0

    # convert image to BGR.
    source_img = convert_to_bgr(source_img)
    template_img = convert_to_bgr(template_img)

    # if the source image is smaller than the template, resize the template img
    template_img = resize_template(template_img, source_img)

    res = cv2.matchTemplate(source_img, template_img, cv2.TM_CCOEFF_NORMED)

    # we ignore min_val and min_loc here, as we are using TM_CCOEFF_NORMED, in which larger values are better.
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        return True, max_loc, max_val
    else:
        return False, max_loc, max_val


def match_template_SQDIFF(source_img: np.ndarray,
                          template_img: np.ndarray,
                          max_diff_threshold: float = 10000,
                          ignore_transparent: bool = True) -> tuple[bool, Sequence[int], float]:
    """
    Uses the TM_SQDIFF method for template matching and returns the best match location and best score.
    Args:
        source_img (np.ndarray): The image to search in.
        template_img (np.ndarray): The template to search for.
        max_diff_threshold (float, optional): Maximum acceptable sum of squared differences. Lower values are stricter. Defaults to 10000.
        ignore_transparent (bool, optional): If True, ignores the transparent area in the template image. Defaults to True.
    Returns:
        Tuple[bool, Sequence[int], float]:
            - bool: True if a match is found(normalized_score < max_diff_threshold), False otherwise.
            - Sequence[int]: (x, y) coordinates of the top-left corner, or (-1, -1) if source_img or template_img is None.
            - float: The normalized matching score.
    """
    if source_img is None or template_img is None:
        # print("Source or template image is None.")
        return False, (-1, -1), -1.0

    # if the source image is smaller than the template, resize the template img
    template_img = resize_template(template_img, source_img)

    mask = np.ones(template_img.shape[:2], dtype="uint8") * 255
    # if the template image has an alpha channel, and we want to ignore transparent areas
    if template_img.shape[2] == 4 and ignore_transparent:
        # create a mask from the alpha channel
        alpha = template_img[:, :, 3]
        mask = (alpha > 0).astype("uint8") * 255

    # convert image to BGR.
    source_img = convert_to_bgr(source_img)
    template_img = convert_to_bgr(template_img)

    res = cv2.matchTemplate(source_img, template_img, cv2.TM_SQDIFF, mask=mask)

    # we ignore max_val and max_loc here, as we are using TM_SQDIFF, in which lower values are better.
    min_val, _, min_loc, _ = cv2.minMaxLoc(res)

    num_pixels_in_mask = np.sum(mask > 0)
    if num_pixels_in_mask == 0:
        # If the valid template is empty, we cannot compute a valid score.
        # and we see it as a perfect match.
        return True, (0, 0), 0.0
    normalized_score = min_val / num_pixels_in_mask

    if normalized_score <= max_diff_threshold:
        return True, min_loc, normalized_score
    else:
        return False, min_loc, normalized_score


def resize_template(template_img: np.ndarray, source_img: np.ndarray) -> np.ndarray:
    """
    Resizes the template image to fit within the source image dimensions.
    If the source image is already larger than the template image, it returns the original template image.
    Args:
        template_img (np.ndarray): The template image to resize.
        source_img (np.ndarray): The source image to fit the template into.
    Returns:
        np.ndarray: The resized template image.
    """
    if source_img.shape[0] < template_img.shape[0] or source_img.shape[1] < template_img.shape[1]:
        scale = min(source_img.shape[0] / template_img.shape[0],
                    source_img.shape[1] / template_img.shape[1])
        new_width = int(template_img.shape[1] * scale)
        new_height = int(template_img.shape[0] * scale)
        return cv2.resize(template_img, (new_width, new_height))
    return template_img


def convert_to_bgr(image: np.ndarray) -> np.ndarray:
    """
    Converts an image to BGR format if it is not already in that format.
    Args:
        image (np.ndarray): The input image.
    Returns:
        np.ndarray: The image in BGR format.
    """
    if len(image.shape) < 3 or image.shape[2] == 1:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image.copy()
