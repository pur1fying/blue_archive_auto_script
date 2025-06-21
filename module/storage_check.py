import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Sequence

import cv2
import imutils
import numpy as np

from core import picture


def compare_images_SQDIFF(source_img: np.ndarray,
                          template_img: np.ndarray,
                          max_diff_threshold: float = 600000) -> tuple[bool, Sequence[int], float]:
    """
    使用 TM_SQDIFF 方法进行模板匹配，能有效忽略模板透明区域对应的源图像素。
    非常适合模板周围有其他元素干扰的情况。

    Args:
        source_img: The image to search in (BGR).
        template_img: The template to search for (BGRA).
        max_diff_threshold: 最大可接受的差值平方和。值越低，要求越严格。

    Returns:
        A tuple containing:
        - bool: True if a match is found, False otherwise.
        - tuple: (x, y) coordinates of the top-left corner, or (-1, -1).
    """
    if source_img is None or template_img is None:
        print("Source or template image is None.")
        return False, (-1, -1), -1.0

    # Ensure the source image is larger than the template image
    if source_img.shape[0] < template_img.shape[0] or source_img.shape[1] < template_img.shape[1]:
        print("Source image is smaller than the template image.")
        cv2.imwrite("source_image.png", source_img)
        cv2.imwrite("template_image.png", template_img)
        raise ValueError()
        return False, (-1, -1), -1.0

    # 确保模板是4通道 (BGRA)
    if template_img.shape[2] != 4:
        raise ValueError("Template image must be a BGRA image with an alpha channel.")

    # 从Alpha通道创建mask
    alpha_channel = template_img[:, :, 3]
    mask = cv2.threshold(alpha_channel, 10, 255, cv2.THRESH_BINARY)[1]  # 忽略几乎透明的像素

    # 确保源图是3通道，以便匹配
    if len(source_img.shape) < 3 or source_img.shape[2] == 1:
        source_img = cv2.cvtColor(source_img, cv2.COLOR_GRAY2BGR)
    elif source_img.shape[2] == 4:
        source_img = cv2.cvtColor(source_img, cv2.COLOR_BGRA2BGR)

    template_bgr = template_img[:, :, :3]

    # --- 核心改动 ---
    # 使用 TM_SQDIFF，它在有 mask 时，只计算非遮罩区域的像素差值平方和。
    # 这能完美忽略源图中对应模板透明区域的“污染物”（如文字、图标）。
    method = cv2.TM_SQDIFF

    res = cv2.matchTemplate(source_img, template_bgr, method, mask=mask)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # 对于 TM_SQDIFF, 我们关心的是最小值 (min_val)
    best_score = min_val
    best_loc = min_loc

    # 计算模板中实际参与比较的像素数量，用于归一化阈值（可选，但推荐）
    num_pixels_in_mask = np.sum(mask > 0)
    if num_pixels_in_mask == 0:
        print("No valid pixels in mask, cannot normalize score.")
        return False, (-1, -1), -1.0  # 避免除以零
    normalized_score = best_score / num_pixels_in_mask

    # 阈值判断：值越小越好
    if normalized_score <= max_diff_threshold:
        return True, best_loc, normalized_score
    else:
        print(f"Match not found: score {normalized_score:.2f} exceeds threshold {max_diff_threshold}.")
        return False, (-1, -1), -1.0


def compare_images_CCOEFF_NORMED(source_img: np.ndarray,
                                 template_img: np.ndarray,
                                 threshold: float = 0.85) -> tuple[bool, Sequence[int], float]:
    """
    通过在灰度图上使用归一化相关系数进行匹配，对颜色和亮度变化更具鲁棒性。

    Args:
        source_img: The image to search in.
        template_img: The template to search for.
        threshold: 匹配阈值 (0.0 to 1.0). 越高越严格.

    Returns:
        Tuple[bool, Tuple[int, int], float]: 匹配结果和位置及最佳分数。
    """
    if source_img is None or template_img is None:
        return False, (-1, -1), -1.0

    # convert img to BGR channel if img is BGRA
    if len(source_img.shape) == 3 and source_img.shape[2] == 4:
        source_img = cv2.cvtColor(source_img, cv2.COLOR_BGRA2BGR)
    if len(template_img.shape) == 3 and template_img.shape[2] == 4:
        template_img = cv2.cvtColor(template_img, cv2.COLOR_BGRA2BGR)

    # if the source image is smaller than the template, resize the template img
    if source_img.shape[0] < template_img.shape[0] or source_img.shape[1] < template_img.shape[1]:
        scale = min(source_img.shape[0] / template_img.shape[0],
                    source_img.shape[1] / template_img.shape[1])
        new_width = int(template_img.shape[1] * scale)
        new_height = int(template_img.shape[0] * scale)
        template_img = cv2.resize(template_img, (new_width, new_height))

    try:
        res = cv2.matchTemplate(source_img, template_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            return True, max_loc, max_val
        else:
            return False, max_loc, max_val

    except cv2.error as e:
        print(f"OpenCV error during matchTemplate: {e}")
        return False, (-1, -1), -1.0


def compare_images_CCORR_NORMED(source: np.ndarray,
                                template: np.ndarray,
                                threshold: float = 0.85) -> tuple[bool, Sequence[int], float]:
    """
    使用模板匹配的黄金标准（彩色图 + TM_CCORR_NORMED + mask）来查找图像。
    此方法对颜色、亮度和背景杂物具有很高的鲁棒性。

    Args:
        source: The image to search in (BGR).
        template: The template to search for (BGRA).
        threshold: 匹配阈值 (0.0 to 1.0). 越高越严格。对于此方法，推荐0.9以上。

    Returns:
        Tuple[bool, Tuple[int, int], float]:
        - bool: 如果匹配分数高于或等于阈值，则为 True。
        - Tuple[int, int]: 最佳匹配的左上角坐标 (x, y)。
        - float: 实际的最佳匹配分数，范围通常在 -1.0 到 1.0 之间。
    """
    if source is None or template is None:
        return False, (-1, -1), -1.0
    h, w = template.shape[:2]
    if source.shape[0] < h or source.shape[1] < w:
        # Source image is too small for the given offset and template size.
        return False, (-1, -1), -1.0

    if template.shape[2] == 4:
        # 提取 alpha 通道作为 mask
        alpha = template[:, :, 3]
        mask = (alpha > 0).astype("uint8") * 255
        template_rgb = template[:, :, :3]
        # 使用 CCORR_NORMED 和 mask 匹配（OpenCV 只支持这一个模式配合 mask）
        res = cv2.matchTemplate(source, template_rgb, cv2.TM_CCORR_NORMED, mask=mask)
    else:
        if source.shape[2] != template.shape[2]:
            print("Region and template have different dimensions.")
            return False, (-1, -1), -1.0
        res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED)

    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    print(similarity)
    if max_val >= threshold:
        return True, max_loc, max_val
    else:
        return False, (-1, -1), -1.0


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


def process_region(self, region, quantity_region, sub_folders, x, y, results, flags, lock):
    max_template_name, max_val, max_loc = None, float('inf'), None
    for sub_folder in sub_folders:
        equipment_template_folder = f"src/images/JP/equipment/{sub_folder}/"
        if not os.path.exists(equipment_template_folder):
            continue
        equipmen_templates = os.listdir(equipment_template_folder)
        for t in equipmen_templates:
            template = cv2.imread(os.path.join(equipment_template_folder, t), cv2.IMREAD_UNCHANGED)
            if template is not None:
                result, loc, score = compare_images_SQDIFF(region, template)
                if score < max_val:
                    max_val = score
                    max_template_name = t
                    max_loc = (loc[0] + x, loc[1] + y)
    quantity = -1
    if (max_template_name is not None) and (max_template_name != "empty.png"):
        ocr_quantity = self.ocr.ocr_for_single_line(
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
        if flags.get(max_template_name, False):
            if results[max_template_name]["quantity"] != quantity:
                raise ValueError(
                    f"Quantity mismatch for {max_template_name}: {results[max_template_name]['quantity']} != {quantity}")
        else:
            results[max_template_name] = {"loc": max_loc, "score": max_val, "quantity": quantity}
        flags[max_template_name] = True


def main(self, results: dict, flags: dict, count):
    template_full = cv2.imread("src/images/JP/equipment/item_frame.png", cv2.IMREAD_UNCHANGED)
    self.update_screenshot_array()
    screen = imutils.resize(self.latest_img_array, width=1280, height=720)
    column_region = screen[145:250, 660:815]

    max_column_loc, max_score = (-1, -1), -1.0
    for i in range(8):
        template = template_full[i * 8:i * 8 + 8, ]
        _, loc, score = compare_images_CCOEFF_NORMED(column_region, template, 0.8)
        if score > max_score:
            max_score = score
            max_column_loc = loc
    # visual
    vis_img = column_region.copy()
    cv2.rectangle(vis_img, max_column_loc,
                  (max_column_loc[0] + 109, max_column_loc[1] + 8), (0, 255, 0), 2)
    cv2.imshow("Column Match Visual", vis_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    sub_folders = ["badge", "bag", "charm", "gloves", "hairpin", "hat", "necklace", "shoes", "watch",
                   "exp", "weaponexp", "empty"]
    # column_coords = [1020, 1180, 1340, 1510, 1670]
    column_coords = [680, 786, 893, 1006, 1113]

    # 使用线程池执行 process_region
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for y in range(139 + max_column_loc[1], screen.shape[0] - 133, 101):
            for x in column_coords:
                count += 1
                region = screen[y:y + 108, x:x + 130]
                # cv2.imwrite(f"temp/region{count}.png", region)
                quantity_region = region[72:, 45:115]
                # cv2.imwrite(f"temp/quantity_region{count}.png", quantity_region)

                lock = threading.Lock()
                # 提交任务到线程池
                futures.append(
                    executor.submit(process_region, self, region, quantity_region, sub_folders, x, y, results,
                                    flags, lock))

        # 等待所有任务完成
        for future in futures:
            future.result()

    return count


def implement(self):
    navigate(self)
    flags = {}
    results = {}

    count = 0
    count = main(self, results, flags, count)
    while not flags.get("empty.png", False):
        self.swipe(917, 552, 917, 220, 0.2, 1.0)
        count = main(self, results, flags, count)

    print(json.dumps(results, sort_keys=True))
    return True
