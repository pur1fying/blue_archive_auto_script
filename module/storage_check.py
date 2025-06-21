import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Sequence

import cv2
import imutils
import numpy as np

from core import picture


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


def compare_images_SQDIFF(source_img: np.ndarray,
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


def compare_images_CCOEFF_NORMED(source_img: np.ndarray,
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


def compare_images_CCORR_NORMED(source_img: np.ndarray,
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


def navigate(self):
    self.to_main_page()
    rgb_reactions = {
        "main_page": (1227, 33)
    }
    img_reactions = {
        "main_page_menu": (516, 389)
    }
    img_ends = [
        "equipment_storage-page"
    ]
    picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, rgb_reactions=rgb_reactions)


def process_region(baas_thread, region, quantity_region, x, y, results, lock):
    sub_folders = ["badge", "bag", "charm", "gloves", "hairpin", "hat", "necklace", "shoes", "watch",
                   "exp", "weaponexp", "empty"]
    max_template_name, max_val, max_loc = None, float('inf'), None
    for sub_folder in sub_folders:
        equipment_template_folder = f"src/images/JP/equipment/{sub_folder}/"
        if not os.path.exists(equipment_template_folder):
            continue
        equipment_templates = os.listdir(equipment_template_folder)
        for t in equipment_templates:
            template = cv2.imread(os.path.join(equipment_template_folder, t), cv2.IMREAD_UNCHANGED)
            if template is not None:
                result, loc, score = compare_images_SQDIFF(region, template)
                if score < max_val:
                    max_val = score
                    max_template_name = t
                    max_loc = (loc[0] + x, loc[1] + y)
    quantity = -1
    # print(f"found {max_template_name} with score {max_val:.4f}")
    if (max_template_name is not None) and (max_template_name != "empty.png"):
        ocr_quantity = baas_thread.ocr.ocr_for_single_line(
            language="en-us",
            origin_image=quantity_region,
            candidates="K0123456789",
            filter_score=0.3
        )
        text = ocr_quantity.replace("K", "000")
        if text.isdigit():
            quantity = int(text)
    # print(f"Best match for {max_template_name} with score {max_val:.4f} at {max_loc}, quantity={quantity}")
    with lock:
        if max_template_name in results:
            if results[max_template_name]["quantity"] != quantity:
                # If the template is already found, but the quantity is different, it indicates ocr has mistaken the counts.
                raise ValueError(
                    f"Quantity mismatch for {max_template_name}: {results[max_template_name]['quantity']} != {quantity}")
        else:
            results[max_template_name] = {"loc": max_loc, "score": max_val, "quantity": quantity}


def implement(baas_thread):
    navigate(baas_thread)
    results = {}

    debug_count = 0
    previous_results_length = -1

    # if the length of results is not changed, we consider the process finished since no new item was added.
    while previous_results_length != len(results) and ("empty.png" not in results):
        previous_results_length = len(results)
        template_full = cv2.imread("src/images/JP/equipment/item_frame.png", cv2.IMREAD_UNCHANGED)
        baas_thread.update_screenshot_array()
        screen = imutils.resize(baas_thread.latest_img_array, width=1280, height=720)
        column_region = screen[145:250, 660:815]

        max_column_loc, max_score = (-1, -1), -1.0
        for i in range(8):
            template = template_full[i * 8:i * 8 + 8, ]
            _, loc, score = compare_images_CCOEFF_NORMED(column_region, template, 0.8)
            if score > max_score:
                max_score = score
                max_column_loc = loc
        # visual
        # vis_img = column_region.copy()
        # cv2.rectangle(vis_img, max_column_loc,
        #               (max_column_loc[0] + 109, max_column_loc[1] + 8), (0, 255, 0), 2)
        # cv2.imshow("Column Match Visual", vis_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        column_coords = [680, 786, 893, 1006, 1113]

        # multithreading to speed up the process
        lock = threading.Lock()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for y in range(139 + max_column_loc[1], screen.shape[0] - 133, 101):
                for x in column_coords:
                    debug_count += 1
                    region = screen[y:y + 108, x:x + 130]
                    # cv2.imwrite(f"temp/region{debug_count}.png", region)
                    quantity_region = region[72:, 45:115]
                    # cv2.imwrite(f"temp/quantity_region{debug_count}.png", quantity_region)

                    # submit the task to the executor
                    futures.append(executor.submit(process_region, baas_thread, region, quantity_region,
                                                   x, y, results, lock))

            # wait for all futures to complete
            for future in futures:
                future.result()
        baas_thread.swipe(917, 552, 917, 220, 0.2, 1.0)

    print(json.dumps(results, sort_keys=True))
    return True
