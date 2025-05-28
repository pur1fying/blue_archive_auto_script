import cv2
import numpy as np

from core import color, picture
from core import image
from module.tactical_challenge_shop import get_purchase_state


def implement(self):
    buy_list = np.array(self.config.CommonShopList)
    if not buy_list.any():
        self.logger.info("Nothing to buy in common shop.")
        return True
    self.to_main_page()
    to_common_shop(self, True)
    assets = {
        "creditpoints": self.get_creditpoints(),
        "pyroxene": self.get_pyroxene(),
    }
    price = self.static_config.common_shop_price_list[self.server]
    temp_price = []
    tp = []
    for i in range(0, len(price)):
        temp_price.append(price[i][1])
        tp.append(price[i][2])
    temp_price = np.array(temp_price)
    asset_required = calculate_one_time_assets(self, buy_list, temp_price, tp)
    refresh_time = min(self.config.CommonShopRefreshTime, 3)
    refresh_price = [40, 60, 80]
    for i in range(0, refresh_time + 1):
        if (asset_required["creditpoints"] > assets['creditpoints'] != -1 or
                asset_required["pyroxene"] > assets['pyroxene'] != -1):
            self.logger.info("INADEQUATE assets for BUYING")
            return True
        buy(self, buy_list)

        state = get_purchase_state(self)
        if state == "shop_purchase-available":
            self.logger.info("-- Purchase available --")
            img_possibles = {
                "shop_menu": (1163, 659),
            }
            img_ends = [
                "shop_purchase-notice1",
                "shop_purchase-notice2",
            ]
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            purchase_location = {
                'CN': (777, 491),
                'Global': (754, 581),
                'JP': (754, 581)
            }
            img_possibles = {
                "shop_purchase-notice1": purchase_location[self.server],
                "shop_purchase-notice2": (767, 524),
            }
            rgb_ends = "reward_acquired"
            img_ends = "main_page_full-notice"
            picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, True)
            assets = calculate_left_assets(self, assets, asset_required)
            to_common_shop(self)
        elif state == "shop_purchase-unavailable":
            self.logger.info("Purchase Unavailable")
            return True
        elif state == "shop_refresh-button-appear":
            self.logger.warning("Refresh Button Detected, assume item purchased previously.")
        if i != refresh_time:
            if assets['pyroxene'] != -1 and assets['pyroxene'] > refresh_price[i]:
                self.logger.info("Refresh assets adequate")
                if not to_refresh(self):
                    self.logger.info("refresh Times inadequate")
                    return True
                assets = calculate_left_assets(self, assets, {"creditpoints": 0, "pyroxene": refresh_price[i]})
                self.click(767, 468, wait_over=True, duration=0.5)
                to_common_shop(self)

    return True


def to_common_shop(self, skip_first_screenshot=False):
    rgb_ends = "common_shop"
    rgb_possibles = {
        "main_page": (799, 653),
        "reward_acquired": (640, 89),
        "tactical_challenge_shop": (157, 135)
    }
    img_possibles = {
        "main_page_full-notice": (887, 165),
        "main_page_insufficient-inventory-space": (910, 138),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


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
    area = (629, template_y_min, 1228, template_y_max)
    tar_img = image.screenshot_cut(self, area)
    self.swipe(1246, 594, 1246, 447, duration=0.05, post_sleep_time=1)
    self.update_screenshot_array()
    position = image.search_image_in_area(self, tar_img, area=(629 - 10, search_area_y_min, 1228 + 10, search_area_y_max), threshold=0.8)
    if position is False:
        self.logger.warning("Swipe Failed.")
        raise
    return area[1] - position[1]


def buy(self, buy_list):
    # get item position --> click buy --> check if chosen --> swipe --> get swipe y difference --> buy
    length = len(buy_list)
    last_checked_idx = 0
    last_checked_y = 0  # item with y > last_checked_y should be considered not checked
    total_item = buy_list.sum()
    count = 0
    while last_checked_idx < length:
        count += 1
        items, item_lines_y = get_item_position(self)
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
            for j in range(0, item_lines_y[i][1]):
                curr_idx = last_checked_idx + items[temp + j][0][0]
                if not buy_list[curr_idx]:
                    continue

                if not items[temp + j][1]:
                    self.logger.warning("Item at [ " + str(curr_idx + 1) + " ] is not purchasable.")
                else:
                    ensure_choose(self, items[temp + j])
                total_item -= 1
            last_checked_idx += 4
            last_checked_y = item_lines_y[i][0]
        if total_item == 0:
            self.logger.info("All Required Items Bought.")
            break
        if last_checked_idx >= length:
            break
        last_checked_y -= swipe_get_y_diff(self, item_lines_y)


def ensure_choose(self, item):
    if item[0][1] <= 252:
        return
    x = [653, 805, 959, 1114]
    area = (x[item[0][0]] - 30, item[0][1] - 140, x[item[0][0]] + 20, item[0][1] - 71)
    click_center = (x[item[0][0]] + 38, item[0][1] - 60)
    while not image.search_in_area(self, "shop_item-chosen", area=area, threshold=0.8):
        self.click(click_center[0], click_center[1], wait_over=True, duration=0.2)
        self.update_screenshot_array()


def get_item_position(self):
    x = [653, 805, 959, 1114]
    y_end = 560
    recorded_y = []  # (y, num) means line y has num items
    state = []  # every item : ((idx of this line, y), purchasable, currency_type)
    for k in range(0, len(x)):
        possibles_x = x[k]
        curr_y = 127
        while curr_y <= y_end:
            # purchase available
            if color.rgb_in_range(self, possibles_x, curr_y, 99, 139, 211, 231, 245, 255):
                area = (possibles_x - 14, curr_y - 10, possibles_x + 40, curr_y + 40)
                currency_type = None
                if image.search_in_area(self, "shop_coin-type-creditpoints-bright", area=area, threshold=0.8):
                    currency_type = "creditpoints"
                elif image.search_in_area(self, "shop_coin-type-pyroxene-bright", area=area, threshold=0.8):
                    currency_type = "pyroxene"
                if currency_type is not None:
                    y = curr_y
                    for i in range(0, len(recorded_y)):
                        if abs(curr_y - recorded_y[i][0]) <= 5:
                            y = recorded_y[i][0]
                            recorded_y[i] = (recorded_y[i][0], recorded_y[i][1] + 1)
                            break
                    else:
                        recorded_y.append((curr_y, 1))
                    curr_y += 70
                    state.append(((k, y), True, currency_type))
                else:
                    curr_y += 1
            # purchase unavailable
            elif color.rgb_in_range(self, possibles_x, curr_y, 68, 88, 140, 160, 164, 184):
                area = (possibles_x - 14, curr_y - 10, possibles_x + 40, curr_y + 40)
                currency_type = None
                if image.search_in_area(self, "shop_coin-type-creditpoints-grey", area=area, threshold=0.8):
                    currency_type = "creditpoints"
                elif image.search_in_area(self, "shop_coin-type-pyroxene-grey", area=area, threshold=0.8):
                    currency_type = "pyroxene"
                if currency_type is not None:
                    y = curr_y
                    for i in range(0, len(recorded_y)):
                        if abs(curr_y - recorded_y[i][0]) <= 5:
                            y = recorded_y[i][0]
                            recorded_y[i] = (recorded_y[i][0], recorded_y[i][1] + 1)
                            break
                    else:
                        recorded_y.append((curr_y, 1))
                    curr_y += 70
                    state.append(((k, y), False, currency_type))
                else:
                    curr_y += 1
            else:
                curr_y += 1
            # purchase unavailable
    state = sorted(state, key=lambda t: t[0][1])
    recorded_y = sorted(recorded_y, key=lambda t: t[0])
    return state, recorded_y


def calculate_left_assets(self, assets, asset_required):
    if assets['creditpoints'] != -1 and asset_required["creditpoints"] > 0:
        assets['creditpoints'] = assets['creditpoints'] - asset_required["creditpoints"]
        self.logger.info("left creditpoints : " + str(assets['creditpoints']))
    if assets['pyroxene'] != -1 and asset_required["pyroxene"] > 0:
        assets['pyroxene'] = assets['pyroxene'] - asset_required["pyroxene"]
        self.logger.info("left pyroxene : " + str(assets['pyroxene']))
    return assets


def to_refresh(self):
    img_ends = [
        "shop_refresh-notice",
        "shop_refresh-unavailable-notice",
    ]
    rgb_possibles = {"common_shop": [1160, 664]}
    if picture.co_detect(self, None, rgb_possibles, img_ends, None, True) == "shop_refresh_guide":
        return False
    return True


def calculate_one_time_assets(self, buy_list, price, tp):
    res = {
        "creditpoints": 0,
        "pyroxene": 0,
    }
    for i in range(0, len(price)):
        if buy_list[i]:
            res[tp[i]] = res[tp[i]] + price[i]
    if res["creditpoints"] > 0:
        self.logger.info("one time needed creditpoints : " + str(res["creditpoints"]))
    if res["pyroxene"] > 0:
        self.logger.info("one time needed pyroxene : " + str(res["pyroxene"]))
    return res
