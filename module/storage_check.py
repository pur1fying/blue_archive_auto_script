import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import cv2
import imutils

from core import picture
from core.image import match_template_CCOEFF_NORMED, match_template_SQDIFF


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
                result, loc, score = match_template_SQDIFF(region, template)
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
            _, loc, score = match_template_CCOEFF_NORMED(column_region, template, 0.8)
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
