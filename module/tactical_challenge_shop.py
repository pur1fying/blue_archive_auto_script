import time

import numpy as np

from core import color, image, picture


def implement(self):
    self.quick_method_to_main_page()
    to_tactical_challenge_shop(self, skip_first_screenshot=True)
    time.sleep(0.5)
    tactical_challenge_assets = get_tactical_challenge_assets(self)
    self.logger.info("tactical assets : " + str(tactical_challenge_assets))
    buy_list_for_power_items = [
        [700, 204], [857, 204], [1000, 204], [1162, 204],
        [700, 461], [857, 461], [1000, 461], [1162, 461]
    ]
    buy_list = np.array(self.config["TacticalChallengeShopList"])
    price = np.array(self.static_config["tactical_challenge_shop_price_list"][self.server], dtype=int)
    if buy_list.shape != price.shape:
        self.logger.error("buy_list and price shape not match")
        return True
    asset_required = (buy_list * price).sum()
    refresh_time = min(self.config['TacticalChallengeShopRefreshTime'], 3)
    refresh_price = [10, 10, 10]
    for i in range(0, refresh_time + 1):
        self.logger.info("asset_required : " + str(asset_required))
        if asset_required > tactical_challenge_assets:
            self.logger.info("INADEQUATE assets for BUYING")
            return True
        for j in range(0, 8):
            if buy_list[j]:
                self.click(buy_list_for_power_items[j][0], buy_list_for_power_items[j][1],
                           duration=0.1, wait=False, wait_over=True)
        if buy_list[8:].any():
            self.logger.info("SWIPE DOWNWARDS")
            self.swipe(932, 550, 932, 0, duration=0.5)
            time.sleep(0.5)
            for j in range(8, len(buy_list)):
                if buy_list[j]:
                    self.click(buy_list_for_power_items[j % 8][0], buy_list_for_power_items[j % 8][1],
                               duration=0.1, wait=False, wait_over=True)

        self.latest_img_array = self.get_screenshot_array()

        if color.judge_rgb_range(self.latest_img_array, 1126, 662, 235, 255, 222, 242, 64, 84):
            self.logger.info("Purchase available")
            self.click(1160, 662, wait=False, wait_over=True)
            time.sleep(0.5)
            self.click(767, 488, wait=False, wait_over=True)
            time.sleep(2)
            self.click(640, 80, wait=False, wait_over=True)
            self.click(640, 80, wait=False, wait_over=True)

            tactical_challenge_assets = tactical_challenge_assets - asset_required
            self.logger.info("left assets : " + str(tactical_challenge_assets))
            to_tactical_challenge_shop(self)

        elif color.judge_rgb_range(self.latest_img_array, 1126, 662, 206, 226, 206, 226, 206, 226):
            self.logger.info("Purchase Unavailable")
            self.click(1240, 39, wait=False, wait_over=True)
            return True
        self.latest_img_array = self.get_screenshot_array()
        if i != refresh_time:
            if tactical_challenge_assets > refresh_price[i]:
                self.logger.info("Refresh assets adequate")
                if not to_refresh(self):
                    self.logger.info("refresh Times inadequate")
                    return True
                tactical_challenge_assets = tactical_challenge_assets - refresh_price[i]
                self.logger.info("left coins : " + str(tactical_challenge_assets))
                self.click(767, 468, duration=0.5, wait=False, wait_over=True)
                to_tactical_challenge_shop(self)
    return True


def to_tactical_challenge_shop(self, skip_first_screenshot=False):
    if self.server == 'CN':
        click_pos = [
            [823, 653],  # main_page
            [640, 89],
            [100, 378],
        ]
        los = [
            "main_page",
            "reward_acquired",
            "common_shop",
        ]
        ends = [
            "tactical_challenge_shop",
        ]
        possibles = {
            'main_page_full-notice': (887, 165),
        }
        image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, ends), skip_first_screenshot=skip_first_screenshot)
    elif self.server == 'Global' or self.server == 'JP':
        click_pos = [
            [796, 653],  # main_page
            [160, 531],  # common shop
            [922, 192],  # buy notice bright
            [922, 192],  # buy notice grey
            [886, 213],  # shop refresh guide
            [640, 89],
            [889, 162],
            [910, 138],
        ]
        los = [
            "main_page",
            "common_shop",
            "buy_notice_bright",
            "buy_notice_grey",
            "shop_refresh_guide",
            "reward_acquired",
            "full_ap_notice",
            "insufficient_inventory_space",
        ]
        ends = [
            "tactical_challenge_shop",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot)


def to_refresh(self):
    refresh_lo = {
        'CN': [949, 664],
        'Global': [1160, 657],
        'JP': [1160, 664]
    }
    img_ends = [
        "shop_refresh-notice",
        "shop_refresh-unavailable-notice"
    ]
    rgb_possibles = {"tactical_challenge_shop": refresh_lo[self.server]}
    res = picture.co_detect(self, None, rgb_possibles, img_ends, None, True)
    if res == "shop_refresh_guide" or res == "shop_refresh-notice":
        return True
    return False


def get_tactical_challenge_assets(self):
    tactical_challenge_assets_region = {
        'CN': [1140, 63, 1240, 102],
        'Global': [1109, 63, 1240, 102],
        'JP': [907, 68, 1045, 98]
    }
    return self.ocr.get_region_num(self.latest_img_array, tactical_challenge_assets_region[self.server])
