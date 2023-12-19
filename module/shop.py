import time
import numpy as np
from core import color

x = {
    'menu': (107, 9, 162, 36),
    'buy3': (682, 311, 714, 327),
    'buy2': (682, 311, 714, 327),
    'buy1': (682, 311, 714, 327),
    'confirm': (737, 446, 766, 476)
}


def to_refresh(self, shop):
    click_pos = [[1160, 620]]
    if shop == "tactical_challenge_shop":
        los = ["tactical_challenge_shop", ]
    elif shop == "common_shop":
        los = ["common_shop", ]
    ends = [
        "shop_refresh_guide",
        "refresh_unavailable_notice"
    ]
    if color.common_rgb_detect_method(self, click_pos, los, ends) == "refresh_unavailable_notice":
        return False
    return True


def implement(self):
    to_tactical_challenge_shop(self)
    tactical_challenge_assets = get_tactical_challenge_assets(self.latest_img_array, self.ocr)
    self.logger.info("tactical assets : " + str(tactical_challenge_assets))

    buy_list_for_power_items = [
        [700, 204], [857, 204], [1000, 204], [1162, 204],
        [700, 461], [857, 461], [1000, 461], [1162, 461]
    ]
    price = np.array([
        50, 50, 50, 50,
        50, 15, 30, 5,
        25, 60, 100, 4,
        20, 60, 100], dtype=int)
    buy_list = np.array(self.global_config["tactical_challenge_shop_buy_list"])
    asset_required = (buy_list * price).sum()
    refresh_time = min(self.global_config['tactical_challenge_shop_refresh_time'], 3)
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
        if buy_list[8:15].any():
            self.logger.info("SWIPE DOWNWARDS")
            self.d.swipe(932, 550, 932, 0, duration=0.5)
            time.sleep(0.5)
            for j in range(8, 15):
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
            if tactical_challenge_assets > refresh_price[i] and color.judge_rgb_range(self.latest_img_array, 1130, 670,
                                                                                      245, 255, 245, 255, 245,
                                                                                      255) and color.judge_rgb_range(
                    self.latest_img_array, 1121, 656, 35, 55, 60, 80, 89, 209):
                self.logger.info("Refresh available")
                self.click(1160, 662, wait=False)
                time.sleep(0.5)
                if not to_refresh(self, "tactical_challenge_shop"):
                    self.logger.info("refresh Times inadequate")
                    return True
                tactical_challenge_assets = tactical_challenge_assets - refresh_price[i]
                self.click(767, 468, wait=False)
                time.sleep(0.5)
                to_tactical_challenge_shop(self)
    to_common_shop(self)
    time.sleep(0.5)
    creditpoints = self.get_creditpoints()
    pyroxenes = self.get_pyroxene()
    buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                 [700, 461], [857, 461], [1000, 461], [1162, 461]]
    price = np.array(
        [
            12500, 125000, 300000, 500000,
            10000, 40000, 96000, 128000,
            10000, 40000, 96000, 128000,
            20000, 80000, 192000, 256000,
            8000, 8000, 25000, 25000
        ], dtype=int)

    buy_list = np.array(self.global_config["common_shop_buy_list"])
    asset_required = (buy_list * price).sum()
    refresh_time = min(self.global_config['common_shop_refresh_time'], 3)
    refresh_price = [40, 60, 80]

    for i in range(0, refresh_time + 1):
        self.logger.info("asset_required : ", asset_required)
        if asset_required > creditpoints != -1:
            self.logger.info("INADEQUATE assets for BUYING")
            return True
        for j in range(0, 8):
            if buy_list[j]:
                self.click(buy_list_for_common_items[j][0], buy_list_for_common_items[j][1], wait=False)
                time.sleep(0.1)
        if buy_list[8:].any():
            self.logger.info("SWIPE DOWNWARDS")
            self.d.swipe(932, 550, 932, 0, duration=0.5)
            time.sleep(0.5)
            for j in range(8, 16):
                if buy_list[j]:
                    self.click(buy_list_for_common_items[j % 8][0], buy_list_for_common_items[j % 8][1], wait=False)
                    time.sleep(0.1)
        if buy_list[16:].any():
            self.logger.info("SWIPE DOWNWARDS")
            self.d.swipe(932, 275, 932, 0, duration=0.5)
            time.sleep(0.5)
            for j in range(16, 20):
                if buy_list[j]:
                    self.click(buy_list_for_common_items[j % 8 + 4][0], buy_list_for_common_items[j % 8 + 4][1],
                               wait=False)
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
            if creditpoints != -1:
                creditpoints = creditpoints - asset_required
                self.logger.info("left creditpoints : " + str(creditpoints))
            to_common_shop(self)
        elif color.judge_rgb_range(self.latest_img_array, 1126, 665, 206, 226, 206, 226, 206, 226):
            self.logger.info("Purchase Unavailable")
            self.click(1240, 39, wait=False)
            return True
        self.latest_img_array = self.operation("get_screenshot_array")
        if i != refresh_time:
            if pyroxenes != -1 and pyroxenes > refresh_price[i] and \
                    color.judge_rgb_range(self.latest_img_array, 1130, 670, 245, 255, 245, 255, 245,
                                          255) and color.judge_rgb_range(self.latest_img_array, 1121, 656, 35, 55, 60,
                                                                         80, 89, 209):
                self.logger.info("Refresh available")
                self.click(1160, 662, wait=False)
                time.sleep(0.5)
                if not to_refresh(self, "common_shop"):
                    self.logger.info("refresh Times inadequate")
                    return True
                pyroxenes = pyroxenes - refresh_price[i]
                self.logger.info("left pyroxenes : " + str(pyroxenes))
                self.click(767, 468, wait=False)
                time.sleep(0.5)
                to_common_shop(self)

    return True


def to_common_shop(self):
    click_pos = [
        [799, 653],  # main_page
        [922, 192],  # buy notice bright
        [922, 192],  # buy notice grey
        [886, 213],  # shop refresh guide
        [640, 89],
        [889, 162],
        [910, 138],
        [157, 135],
    ]
    los = [
        "main_page",
        "buy_notice_bright",
        "buy_notice_grey",
        "shop_refresh_guide",
        "reward_acquired",
        "full_ap_notice",
        "insufficient_inventory_space",
        "tactical_challenge_shop",
    ]
    ends = [
        "common_shop",
    ]
    color.common_rgb_detect_method(self, click_pos, los, ends)
