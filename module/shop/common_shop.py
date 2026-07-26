import numpy as np

from core import picture, image
from module.shop.shop_utils import get_purchase_state, to_common_shop, buy

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
            img_possibles = {
                "shop_purchase-notice1": (754, 581),
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
    img_possibles = {"shop_menu": (1160, 664)}
    if picture.co_detect(self, None, None, img_ends, img_possibles, True) == "shop_refresh_guide":
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
