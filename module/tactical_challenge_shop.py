import time

import numpy as np

from core import color, image


def implement(self):
    self.quick_method_to_main_page()
    to_tactical_challenge_shop(self)
    time.sleep(0.5)
    tactical_challenge_assets = get_tactical_challenge_assets(self.latest_img_array, self.ocrNUM)
    self.logger.info("tactical assets : " + str(tactical_challenge_assets))
    buy_list_for_power_items = [
        [700, 204], [857, 204], [1000, 204], [1162, 204],
        [700, 461], [857, 461], [1000, 461], [1162, 461]
    ]
    buy_list = np.array(self.config["TacticalChallengeShopList"])
    if self.server == 'CN':
        price = np.array([
            50, 50, 50, 15,
            30, 5, 25, 60,
            100, 4, 20, 60,
            100], dtype=int)
    elif self.server == 'Global':
        price = np.array([
            50, 50, 50, 50,
            50, 15, 30, 5,
            25, 60, 100, 4,
            20, 60, 100], dtype=int)
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
                self.click(buy_list_for_power_items[j][0], buy_list_for_power_items[j][1], wait=False)
                time.sleep(0.1)
        if buy_list[8:].any():
            self.logger.info("SWIPE DOWNWARDS")
            self.swipe(932, 550, 932, 0, duration=0.5)
            time.sleep(0.5)
            for j in range(8, len(buy_list)):
                if buy_list[j]:
                    self.click(buy_list_for_power_items[j % 8][0], buy_list_for_power_items[j % 8][1], wait=False)
                    time.sleep(0.1)

        self.latest_img_array = self.get_screenshot_array()

        if color.judge_rgb_range(self.latest_img_array, 1126, 662, 235, 255, 222, 242, 64, 84):
            self.logger.info("Purchase available")
            self.click(1160, 662, wait=False)
            time.sleep(0.5)
            self.click(767, 488, wait=False)
            time.sleep(2)
            self.click(640, 80, wait=False)
            self.click(640, 80, wait=False)

            tactical_challenge_assets = tactical_challenge_assets - asset_required
            self.logger.info("left assets : " + str(tactical_challenge_assets))

            to_tactical_challenge_shop(self)

        elif color.judge_rgb_range(self.latest_img_array, 1126, 662, 206, 226, 206, 226, 206, 226):
            self.logger.info("Purchase Unavailable")
            self.click(1240, 39, wait=False)
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
                self.click(767, 468, wait=False)
                time.sleep(0.5)
                to_tactical_challenge_shop(self)
    return True


def to_tactical_challenge_shop(self):
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
                     pre_argv=(self, click_pos, los, ends))
    elif self.server == 'Global':
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
        color.common_rgb_detect_method(self, click_pos, los, ends)


def to_refresh(self):
    if self.server == 'CN':
        ends = [
            "shop_refresh-notice",
            "shop_refresh-unavailable-notice"
        ]
        click_pos = [[949, 664]]
        los = ["tactical_challenge_shop"]
        if image.detect(self, end=ends, pre_func=color.detect_rgb_one_time,
                        pre_argv=(self,click_pos, los, [])) == "shop_refresh-unavailable-notice":
            return False
        return True
    elif self.server == 'Global':
        click_pos = [[1160, 620]]
        los = ["tactical_challenge_shop"]
        ends = [
            "shop_refresh_guide",
            "refresh_unavailable_notice"
        ]
        if color.common_rgb_detect_method(self, click_pos, los, ends) == "refresh_unavailable_notice":
            return False
        return True


def get_tactical_challenge_assets(img, ocr):
    img = img[63:102, 1140:1240]
    t1 = time.time()
    ocr_res = ocr.ocr_for_single_line(img)
    print(time.time() - t1)
    return int(ocr_res["text"])
