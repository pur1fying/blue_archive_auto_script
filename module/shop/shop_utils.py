from core import picture, image, color
from core.utils import build_possible_string_dict_and_length, most_similar_string


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

