import time
import numpy as np
from core import color, picture


def implement(self):
    self.quick_method_to_main_page()
    to_tactical_challenge_shop(self, skip_first_screenshot=True)
    time.sleep(0.5)
    tactical_challenge_assets = get_tactical_challenge_assets(self)
    self.logger.info("tactical assets : " + str(tactical_challenge_assets))
    buy_list = np.array(self.config["TacticalChallengeShopList"])
    price = self.static_config["tactical_challenge_shop_price_list"][self.server]
    temp = []
    for i in range(0, len(price)):
        temp.append(price[i][1])
    temp = np.array(temp)
    asset_required = (buy_list * temp).sum()
    refresh_time = min(self.config['TacticalChallengeShopRefreshTime'], 3)
    refresh_price = [10, 10, 10]
    for i in range(0, refresh_time + 1):
        self.logger.info("asset_required : " + str(asset_required))
        if asset_required > tactical_challenge_assets:
            self.logger.info("INADEQUATE assets for BUYING")
            return True
        buy(self, buy_list)
        self.latest_img_array = self.get_screenshot_array()
        if color.judge_rgb_range(self, 1126, 662, 235, 255, 222, 242, 64, 84):
            self.logger.info("Purchase available")
            self.click(1160, 662, wait_over=True, duration=0.5)
            self.click(767, 488, wait_over=True, duration=2)
            self.click(640, 80, wait_over=True)
            self.click(640, 80, wait_over=True)

            tactical_challenge_assets = tactical_challenge_assets - asset_required
            self.logger.info("left assets : " + str(tactical_challenge_assets))
            to_tactical_challenge_shop(self)

        elif color.judge_rgb_range(self, 1126, 662, 206, 226, 206, 226, 206, 226):
            self.logger.info("Purchase Unavailable")
            self.click(1240, 39, wait_over=True)
            return True
        self.latest_img_array = self.get_screenshot_array()
        if i != refresh_time:
            if tactical_challenge_assets > refresh_price[i]:
                self.logger.info("Refresh assets adequate")
                if not to_refresh(self):
                    self.logger.info("refresh Times inadequate")
                    return True
                tactical_challenge_assets = tactical_challenge_assets - refresh_price[i]
                self.logger.info("left tactical challenge assets : " + str(tactical_challenge_assets))
                self.click(767, 468, duration=0.5, wait_over=True)
                to_tactical_challenge_shop(self)
    return True


def to_tactical_challenge_shop(self, skip_first_screenshot=False):
    rgb_ends = "tactical_challenge_shop",
    tactical_challenge_x = {
        'CN': 823,
        'Global': 823,
        'JP': 778,
    }
    tactical_challenge_y = {
        'CN': 455,
        'Global': 531,
        'JP': 531,
    }
    rgb_possibles = {
        "main_page": (tactical_challenge_x[self.server], 653),
        "reward_acquired": (640, 89),
        "common_shop": (160, tactical_challenge_y[self.server]),
    }
    img_possibles = {
        'main_page_full-notice': (887, 165),
        "main_page_insufficient_inventory_space": (910, 138),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def to_refresh(self):
    img_ends = [
        "shop_refresh-notice",
        "shop_refresh-unavailable-notice"
    ]
    rgb_possibles = {"tactical_challenge_shop": (1160, 664)}
    res = picture.co_detect(self, None, rgb_possibles, img_ends, None, True)
    if res == "shop_refresh_guide" or res == "shop_refresh-notice":
        return True
    return False


def get_tactical_challenge_assets(self):
    tactical_challenge_assets_region = {
        'CN': [1109, 63, 1240, 102],
        'Global': [1109, 63, 1240, 102],
        'JP': [907, 68, 1045, 98]
    }
    return self.ocr.get_region_num(self.latest_img_array, tactical_challenge_assets_region[self.server], int,
                                   self.ratio)


def buy(self, buy_list):
    buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                 [700, 461], [857, 461], [1000, 461], [1162, 461]]
    i = 0
    length = len(buy_list)
    while i < length:
        if buy_list[i]:
            self.click(buy_list_for_common_items[i % 8][0], buy_list_for_common_items[i % 8][1],
                       wait_over=True, duration=0.1)
        if i % 8 == 7:
            if not buy_list[i + 1:].any():
                break
            if length - i > 0:
                if length - i > 5:
                    self.logger.info("SWIPE DOWNWARDS")
                    self.swipe(932, 550, 932, 0, duration=0.5)
                    time.sleep(0.3)
                else:
                    buy_list_for_common_items = buy_list_for_common_items[4:]
                    self.logger.info("SWIPE DOWNWARDS")
                    self.swipe(932, 275, 932, 0, duration=0.5)
                    time.sleep(0.3)
        i = i + 1
