import time

from core import picture, image, color
from core.utils import build_possible_string_dict_and_length, most_similar_string

SHOP_ITEM_ROW_X = {
    'CN': [651, 801, 954, 1109],
    'Global': [650, 800, 950, 1100],
    'JP': [650, 800, 950, 1100]
}

def get_purchase_state(self):
    img_ends = [
        "shop_purchase-available",
        "shop_purchase-unavailable",
        "shop_refresh-button-appear",
    ]
    return picture.co_detect(self, None, None, img_ends, None, False)

def to_common_shop(self, skip_first_screenshot=False):
    img_ends = "shop_menu"
    rgb_possibles = {
        "main_page": (799, 653),
        "reward_acquired": (640, 89)
    }
    img_possibles = {
        "main_page_full-notice": (887, 165),
        "main_page_insufficient-inventory-space": (910, 138),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)

def goto_shop_by_name(self, name_idx):
    possible_names = self.static_config.shop_type_list_names[self.identifier]
    char_set = set()
    for name in possible_names:
        for ch in name:
            char_set.add(ch)
    candidates = "".join(char_set)
    shop_name = possible_names[name_idx]
    self.logger.info("<<< Goto Shop [ " + shop_name + " ] >>>")
    _dict, _list = build_possible_string_dict_and_length(possible_names)
    def replace_func(st, _dict=_dict, _list=_list, origin=possible_names):
        st = st.replace(' ', '').replace('（', '(').replace('）', ')').replace('!', 'l')
        acc, idx = most_similar_string(st, _dict, _list)
        if acc >= 0.4:
            return origin[idx]
        return st
    shop_pos = image.swipe_search_target_str(
        self=self,
        name="shop_list-type-name-feature",
        search_area=(0, 102, 25, 569),
        threshold=0.8,
        possible_strs=possible_names,
        target_str_index=name_idx,
        swipe_params=(176, 502, 176, 120, 0.5, 0.5),
        ocr_language=self.ocr_language,
        ocr_region_offsets=(51, 5, 156, 55),
        ocr_str_replace_func=replace_func,
        max_swipe_times=4,
        ocr_candidates=candidates + '（）',
        ocr_filter_score=0.2,
        first_retry_dir=0,
        deduplication_pixels=(10, 10)
    )
    shop_pos = (int(shop_pos[0]), int(shop_pos[1]))
    shop_not_selected_rgb_feature_name = "temp_shop_not_selected"
    shop_selected_rgb_feature_name = "temp_shop_selected"
    not_selected_rgb_range = [245, 255, 245, 255, 245, 255]
    selected_rgb_range = [35, 55, 60, 80, 89, 109]
    rgb_p = [
        [1, shop_pos[1] + 15],
        [1, shop_pos[1] + 50],
        [206, shop_pos[1] + 15],
        [206, shop_pos[1] + 50],
    ]
    color.create_rgb_feature(self, shop_not_selected_rgb_feature_name, rgb_p, [not_selected_rgb_range] * 4)
    color.create_rgb_feature(self, shop_selected_rgb_feature_name, rgb_p, [selected_rgb_range] * 4)
    rgb_possibles = {
        shop_not_selected_rgb_feature_name: (shop_pos[0] + 100, shop_pos[1] + 30),
    }
    rgb_ends = shop_selected_rgb_feature_name
    picture.co_detect(self, rgb_ends, rgb_possibles, None, None, False)
    color.remove_rgb_feature(self, shop_not_selected_rgb_feature_name)
    color.remove_rgb_feature(self, shop_selected_rgb_feature_name)

def buy(self, buy_list, shop_type="common_shop"):
    # get item position --> click buy --> check if chosen --> swipe --> get swipe y difference --> buy
    length = len(buy_list)
    last_checked_idx = 0
    last_checked_y = 0  # item with y > last_checked_y should be considered not checked
    total_item = buy_list.sum()
    count = 0
    while last_checked_idx < length:
        count += 1
        items, item_lines_y = get_item_position(self, shop_type)
        for i in range(1, len(item_lines_y)):
            if item_lines_y[i - 1][1] < item_lines_y[i][1]:
                self.logger.warning("Item num detected might be wrong, higher y has more items.")
        temp = 0
        self.logger.info("Detect Item Row y : " + str(item_lines_y))
        self.logger.info("Last   Checked  y : " + str(last_checked_y))
        for i in range(0, len(item_lines_y)):
            if item_lines_y[i][0] - last_checked_y <= 10:
                temp += item_lines_y[i][1]
                continue
            need_buy_list = []
            for j in range(0, item_lines_y[i][1]):
                curr_idx = last_checked_idx + items[temp + j][0][0]
                if not buy_list[curr_idx]:
                    continue

                if not items[temp + j][1]:
                    self.logger.warning("Item at [ " + str(curr_idx + 1) + " ] is not purchasable.")
                else:
                    need_buy_list.append(items[temp + j])
                total_item -= 1
            ensure_choose(self, need_buy_list)
            temp += item_lines_y[i][1]
            last_checked_idx += item_lines_y[i][1]
            last_checked_y = item_lines_y[i][0]
        if total_item == 0:
            self.logger.info("All Required Items Bought.")
            break
        if last_checked_idx >= length:
            break
        last_checked_y -= swipe_get_y_diff(self, item_lines_y)

def get_item_position(self, shop_type="common_shop"):
    """
        shop_type : "common_shop" or "tactical_challenge_shop"

        Returns:
            state : [((line_idx, line_y), purchasable, currency_type)]
            recorded_y : [(line_y, num_of_items_in_this_line)]
    """
    x = SHOP_ITEM_ROW_X[self.server]
    y_end = 560
    recorded_y = []  # (y, num) means line y has num items
    state = []  # every item : ((idx of this line, y), purchasable, currency_type)

    if shop_type == "common_shop":
        currency_list = ["creditpoints", "pyroxene"]
    elif shop_type == "tactical_challenge_shop":
        currency_list = ["tactical-coin"]

    def match_currency(area, purchasable):
        suffix = "bright" if purchasable else "grey"
        for currency_type in currency_list:
            template_name = f"shop_coin-type-{currency_type}-{suffix}"
            if image.search_in_area(self, template_name, area=area, threshold=0.8):
                return currency_type
        return None

    def record_line_y(curr_y):
        y = curr_y
        for i in range(0, len(recorded_y)):
            # close to existing y, consider as same line
            if abs(curr_y - recorded_y[i][0]) <= 5:
                y = recorded_y[i][0]
                recorded_y[i] = (recorded_y[i][0], recorded_y[i][1] + 1)
                break
        else:
            recorded_y.append((curr_y, 1))
        return y

    for k in range(0, len(x)):
        possibles_x = x[k]
        curr_y = 127
        while curr_y <= y_end:
            purchasable = None

            # purchase available
            if color.rgb_in_range(self, possibles_x, curr_y, 99, 139, 211, 231, 245, 255):
                purchasable = True
            # purchase unavailable
            elif color.rgb_in_range(self, possibles_x, curr_y, 68, 88, 140, 160, 164, 184):
                purchasable = False

            if purchasable is not None:
                area = (possibles_x - 14, curr_y - 15, possibles_x + 50, curr_y + 50)
                currency_type = match_currency(area, purchasable)

                if currency_type is not None:
                    y = record_line_y(curr_y)
                    curr_y += 70
                    state.append(((k, y), purchasable, currency_type))
                else:
                    curr_y += 1
            else:
                curr_y += 1

    state = sorted(state, key=lambda t: t[0][1])
    recorded_y = sorted(recorded_y, key=lambda t: t[0])
    return state, recorded_y

def ensure_choose(self, items):
    for item in items:
        if item[0][1] <= 252:
            items.remove(item)
    x = SHOP_ITEM_ROW_X[self.server]
    areas = []
    click_centers = []
    unchecked = list(range(len(items)))

    for item in items:
        areas.append((x[item[0][0]] - 30, item[0][1] - 140, x[item[0][0]] + 20, item[0][1] - 71))
        click_centers.append((x[item[0][0]] + 38, item[0][1] - 60))

    last_click_t = 0
    last_screenshot_t = time.time()
    while len(unchecked) > 0:
        clicked = False

        for i in unchecked:
            area = areas[i]
            click_center = click_centers[i]
            if not image.search_in_area(self, "shop_item-chosen", area=area, threshold=0.8):
                # slow down click
                if last_screenshot_t - last_click_t > 0.5:
                    self.click(click_center[0], click_center[1], wait_over=True)
                    clicked = True
            else:
                unchecked.remove(i)
        if clicked:
            last_click_t = time.time()
        self.update_screenshot_array()
        last_screenshot_t = time.time()



def swipe_get_y_diff(self, item_lines_y):
    max_y = item_lines_y[len(item_lines_y) - 1][0]

    if max_y > 604 - 126:
        template_y_min = max_y
        template_y_max = max_y + 23
    else:
        template_y_min = max_y + 81
        template_y_max = max_y + 126
    search_area_y_min = template_y_min - 330
    search_area_y_max = template_y_max + 30
    crop_template_x = [629, 762]
    area = (crop_template_x[0], template_y_min, crop_template_x[1], template_y_max)
    tar_img = image.screenshot_cut(self, area)
    self.swipe(616, 594, 616, 447, duration=0.05 if self.is_android_device else 0.5, post_sleep_time=1)
    self.update_screenshot_array()
    search_area = (crop_template_x[0] - 10, search_area_y_min, crop_template_x[1] + 10, search_area_y_max)
    position = image.search_image_in_area(self,
                                          tar_img,
                                          area=search_area,
                                          threshold=0.8
                                          )
    if position is False:
        self.logger.warning("Swipe Failed.")
        raise
    return area[1] - position[1]
