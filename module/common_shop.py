import time
import numpy as np
from core import color, image

x = {
    'confirm': (737, 446, 766, 476),
    'refresh-notice':(575,270, 628,302),
    'refresh-unavailable-notice':(547,315, 600,350)
}


def to_refresh(self):
    if self.server == 'CN':
        ends = [
            "shop_refresh-notice",
            "shop_refresh-unavailable-notice",

        ]
        click_pos = [[949, 664]]
        los = ["common_shop"]
        if image.detect(self,end=ends,pre_func=color.detect_rgb_one_time,pre_argv=(self,click_pos, los, [])) == "shop_refresh-unavailable-notice":
            return False
        return True
    elif self.server == 'Global':
        click_pos = [[1160, 620]]
        los = ["common_shop"]
        ends = [
            "shop_refresh_guide",
            "refresh_unavailable_notice"
        ]
        if color.common_rgb_detect_method(self, click_pos, los, ends) == "refresh_unavailable_notice":
            return False
        return True


def implement(self):
    to_common_shop(self)
    time.sleep(0.5)
    creditpoints = self.get_creditpoints()
    pyroxenes = self.get_pyroxene()
    buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                 [700, 461], [857, 461], [1000, 461], [1162, 461]]
    buy_list = np.array(self.config["CommonShopList"])
    if self.server == 'CN':
        pass
    elif self.server == 'Global':
        price = np.array(
            [
                12500, 125000, 300000, 500000,
                10000, 40000, 96000, 128000,
                10000, 40000, 96000, 128000,
                20000, 80000, 192000, 256000,
                8000, 8000, 25000, 25000
            ], dtype=int)
        if price.shape != buy_list.shape:
            self.logger.critical("price shape not match buy_list shape")
            return True
        asset_required = (buy_list * price).sum()

    refresh_time = min(self.config['CommonShopRefreshTime'], 3)
    refresh_price = [40, 60, 80]

    for i in range(0, refresh_time + 1):
        if self.server == 'CN':
            pass
        elif self.server == 'Global':
            self.logger.info("asset_required : " + str(asset_required))
            if asset_required > creditpoints != -1:
                self.logger.info("INADEQUATE assets for BUYING")
                return True
        for j in range(0, 8):
            if buy_list[j]:
                self.click(buy_list_for_common_items[j][0], buy_list_for_common_items[j][1], wait=False)
                time.sleep(0.1)
        if buy_list[8:].any():
            self.logger.info("SWIPE DOWNWARDS")
            self.swipe(932, 550, 932, 0, duration=0.5)
            time.sleep(0.5)
            for j in range(8, 16):
                if buy_list[j]:
                    self.click(buy_list_for_common_items[j % 8][0], buy_list_for_common_items[j % 8][1], wait=False)
                    time.sleep(0.1)
        if self.server == 'CN':
            pass
        elif self.server == 'Global':
            if buy_list[16:].any():
                self.logger.info("SWIPE DOWNWARDS")
                self.swipe(932, 275, 932, 0, duration=0.5)
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
            if self.server == 'CN':
                pass
            if self.server == 'Global':
                if creditpoints != -1:
                    creditpoints = creditpoints - asset_required
                    self.logger.info("left creditpoints : " + str(creditpoints))
            to_common_shop(self)
        elif color.judge_rgb_range(self.latest_img_array, 1126, 665, 206, 226, 206, 226, 206, 226):
            self.logger.info("Purchase Unavailable")
            self.click(1240, 39, wait=False)
            return True
        self.latest_img_array = self.get_screenshot_array()
        if i != refresh_time:
            if pyroxenes != -1 and pyroxenes > refresh_price[i]:
                self.logger.info("Refresh assets adequate")
                if not to_refresh(self):
                    self.logger.info("refresh Times inadequate")
                    return True
                pyroxenes = pyroxenes - refresh_price[i]
                self.logger.info("left pyroxenes : " + str(pyroxenes))
                self.click(767, 468, wait=False)
                time.sleep(0.5)
                to_common_shop(self)

    return True


def to_common_shop(self):
    if self.server == 'CN':
        click_pos = [
            [823, 653],  # main_page
            [640, 89],
            [100, 141],
        ]
        los = [
            "main_page",
            "reward_acquired",
            "tactical_challenge_shop",
        ]
        ends = [
            "common_shop",
        ]
        image.detect(self,pre_func=color.detect_rgb_one_time,pre_argv=(self, click_pos, los, ends))
    elif self.server == 'Global':
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
