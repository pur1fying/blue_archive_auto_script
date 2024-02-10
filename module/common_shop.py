import time
import numpy as np
from core import color, picture


def implement(self):
    self.quick_method_to_main_page()
    to_common_shop(self, True)
    time.sleep(0.5)
    assets = {
        "creditpoints": self.get_creditpoints(),
        "pyroxenes": self.get_pyroxene(),
    }
    buy_list = np.array(self.config["CommonShopList"])
    price = self.static_config["common_shop_price_list"][self.server]
    tp = []
    for i in range(0, len(price)):
        tp.append(price[i][2])
        price[i] = price[i][1]
    price = np.array(price)
    asset_required = calculate_one_time_assets(self, buy_list, price, tp)
    refresh_time = min(self.config['CommonShopRefreshTime'], 3)
    refresh_price = [40, 60, 80]
    for i in range(0, refresh_time + 1):
        if asset_required["creditpoints"] > assets['creditpoints'] != -1 or asset_required["pyroxenes"] > assets[
            'pyroxenes'] != -1:
            self.logger.info("INADEQUATE assets for BUYING")
            return True
        buy(self, buy_list)
        self.latest_img_array = self.get_screenshot_array()

        if color.judge_rgb_range(self, 1126, 662, 235, 255, 222, 242, 64, 84):
            self.logger.info("Purchase available")
            self.click(1160, 662, wait_over=True)
            time.sleep(0.5)
            self.click(767, 488, wait_over=True)
            time.sleep(2)
            self.click(640, 80, wait_over=True)
            self.click(640, 80, wait_over=True)
            assets = calculate_left_assets(self, assets, asset_required)

            to_common_shop(self)
        elif color.judge_rgb_range(self, 1126, 665, 206, 226, 206, 226, 206, 226):
            self.logger.info("Purchase Unavailable")
            self.click(1240, 39, wait=False)
            return True
        if i != refresh_time:
            if assets['pyroxenes'] != -1 and assets['pyroxenes'] > refresh_price[i]:
                self.logger.info("Refresh assets adequate")
                if not to_refresh(self):
                    self.logger.info("refresh Times inadequate")
                    return True
                assets = calculate_left_assets(self, assets, {"creditpoints": 0, "pyroxenes": refresh_price[i]})
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
        "main_page_insufficient_inventory_space": (910, 138),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def buy(self, buy_list):
    buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                 [700, 461], [857, 461], [1000, 461], [1162, 461]]
    i = 0
    length = len(buy_list)
    while i < length:
        if buy_list[i]:
            self.click(buy_list_for_common_items[i % 8][0], buy_list_for_common_items[i % 8][1],
                       wait_over=True)
            time.sleep(0.1)
        if i % 8 == 7:
            if not buy_list[i + 1:].any():
                break
            if length - i > 0:
                if length - i > 5:
                    self.logger.info("SWIPE DOWNWARDS")
                    self.swipe(932, 550, 932, 0, duration=0.5)
                    time.sleep(0.5)
                else:
                    buy_list_for_common_items = buy_list_for_common_items[4:]
                    self.logger.info("SWIPE DOWNWARDS")
                    self.swipe(932, 275, 932, 0, duration=0.5)
                    time.sleep(0.5)
        i = i + 1


def calculate_left_assets(self, assets, asset_required):
    if assets['creditpoints'] != -1 and asset_required["creditpoints"] > 0:
        assets['creditpoints'] = assets['creditpoints'] - asset_required["creditpoints"]
        self.logger.info("left creditpoints : " + str(assets['creditpoints']))
    if assets['pyroxenes'] != -1 and asset_required["pyroxenes"] > 0:
        assets['pyroxenes'] = assets['pyroxenes'] - asset_required["pyroxenes"]
        self.logger.info("left pyroxenes : " + str(assets['pyroxenes']))
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
        "pyroxenes": 0,
    }
    for i in range(0, len(price)):
        if buy_list[i]:
            res[tp[i]] = res[tp[i]] + price[i]
    if res["creditpoints"] > 0:
        self.logger.info("one time needed creditpoints : " + str(res["creditpoints"]))
    if res["pyroxenes"] > 0:
        self.logger.info("one time needed pyroxenes : " + str(res["pyroxenes"]))
    return res
