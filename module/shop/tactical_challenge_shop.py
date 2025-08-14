import time
import numpy as np

from core import picture
from module.shop.shop_utils import get_purchase_state, to_common_shop, goto_shop_by_name

def implement(self):
    buy_list = np.array(self.config.TacticalChallengeShopList)
    if not buy_list.any():
        self.logger.info("Nothing to buy in tactical challenge shop.")
        return True
    self.to_main_page()
    to_common_shop(self, True)
    shop_name_idx = {
        "CN": 5,
        "Global": 5,
        "JP": 6
    }
    goto_shop_by_name(self, shop_name_idx[self.server])
    tactical_challenge_assets = get_tactical_challenge_assets(self)
    price = self.static_config.tactical_challenge_shop_price_list[self.server]
    temp = []
    for i in range(0, len(price)):
        temp.append(price[i][1])
    temp = np.array(temp)
    asset_required = (buy_list * temp).sum()
    refresh_time = min(self.config.TacticalChallengeShopRefreshTime, 3)
    refresh_price = [10, 10, 10]
    for i in range(0, refresh_time + 1):
        self.logger.info("Assets Required : " + str(asset_required))
        if asset_required > tactical_challenge_assets:
            self.logger.info("Inadequate Assets For Buying.")
            return True
        buy(self, buy_list)

        state = get_purchase_state(self)
        if state == "shop_purchase-available":
            self.logger.info("-- Purchase available --")
            img_possibles = {
                "shop_menu": (1163, 659),
            }
            img_ends = "shop_purchase-notice1"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            img_possibles = {
                "shop_purchase-notice1": (754, 581),
            }
            rgb_ends = "reward_acquired"
            img_ends = "main_page_full-notice"
            picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, True)
            to_shop_menu(self)
            tactical_challenge_assets = get_tactical_challenge_assets(self)
        elif state == "shop_purchase-unavailable":
            self.logger.info("-- Purchase Unavailable --")
            return True
        elif state == "shop_refresh-button-appear":
            self.logger.warning("Refresh Button Detected, assume item purchased previously.")
        self.latest_img_array = self.get_screenshot_array()
        if i != refresh_time:
            if tactical_challenge_assets >= refresh_price[i] + asset_required:
                self.logger.info("Refresh and purchase assets adequate.")
                if not to_refresh(self):
                    self.logger.info("refresh Times inadequate")
                    return True
                confirm_refresh(self)
                tactical_challenge_assets = get_tactical_challenge_assets(self)
    return True


def confirm_refresh(self):
    img_possibles = {
        "shop_refresh-notice": (767, 468),
    }
    img_ends = "shop_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_shop_menu(self):
    rgb_possibles = {
        "reward_acquired": (640, 89),
    }
    img_possibles = {
        'main_page_full-notice': (887, 165),
        "main_page_insufficient-inventory-space": (910, 138),
    }
    img_ends = "shop_menu"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def to_refresh(self):
    img_ends = [
        "shop_refresh-notice",
        "shop_refresh-unavailable-notice"
    ]
    img_possibles = {
        "shop_menu": (1160, 664)
    }
    img_pop_ups = {
        'main_page_full-notice': (887, 165),
        "main_page_insufficient-inventory-space": (910, 138),
    }
    res = picture.co_detect(self, None, None, img_ends, img_possibles, True, pop_ups_img_reactions=img_pop_ups)
    if res == "shop_refresh-notice":
        return True
    return False


def get_tactical_challenge_assets(self):
    ret = self.ocr.recognize_int(
        baas=self,
        region=(751, 68, 884, 98),
        log_info="Tactical Challenge Assets"
    )
    data = {
        "count": ret,
        "time": time.time()
    }
    self.config_set.set("tactical_challenge_coin", data)
    return ret


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
                    self.swipe(932, 550, 932, 0, duration=0.5, post_sleep_time=0.3)
                else:
                    buy_list_for_common_items = buy_list_for_common_items[4:]
                    self.logger.info("SWIPE DOWNWARDS")
                    self.swipe(932, 275, 932, 0, duration=0.5, post_sleep_time=0.3)
        i = i + 1
