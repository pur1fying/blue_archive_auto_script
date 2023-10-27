import time

from core.utils import get_x_y
from gui.util import log
from gui.util.config_set import ConfigSet


def implement(self, activity="shop"):
    if activity == "collect_shop_power":
        buy_list = self.config.get("ArenaShopList")
        self.operation("click", (100, 370), duration=0.5)
        buy_list_for_power_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                    [700, 461], [857, 461], [1000, 461], [1162, 461]]
        for i in range(0, 8):
            if buy_list[i]:
                self.operation("click", (buy_list_for_power_items[i][0], buy_list_for_power_items[i][1]), duration=0.1)
        log.d("SWIPE DOWNWARDS", level=1, logger_box=self.loggerBox)
        self.operation("swipe", [(932, 600), (932, 0)], duration=0.3)
        for i in range(8, 12):
            if buy_list[i]:
                time.sleep(0.1)
                self.operation("click", (buy_list_for_power_items[i % 8][0], buy_list_for_power_items[i % 8][1]))
    else:
        buy_list = self.config.get("ShopList")
        buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                     [700, 461], [857, 461], [1000, 461], [1162, 461]]
        for i in range(0, 8):
            if buy_list[i]:
                time.sleep(0.1)
                self.operation("click", (buy_list_for_common_items[i][0], buy_list_for_common_items[i][1]),
                               duration=0.1)
        log.d("SWIPE DOWNWARDS", level=1, logger_box=self.loggerBox)
        self.operation("swipe", [(932, 600), (932, 0)], duration=0.3)
        for i in range(8, 16):
            if buy_list[i]:
                self.operation("click", (buy_list_for_common_items[i % 8][0], buy_list_for_common_items[i % 8][1]),
                               duration=0.2)

    time.sleep(0.5)
    self.latest_img_array = self.operation("get_screenshot_array")

    path2 = "src/shop/buy_bright.png"
    path3 = "src/shop/buy_grey.png"
    path4 = "src/shop/update.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    return_data2 = get_x_y(self.latest_img_array, path3)
    return_data3 = get_x_y(self.latest_img_array, path4)
    print(return_data1)
    print(return_data2)
    if return_data2[1][0] <= 1e-03:
        log.d("assets inadequate", level=1, logger_box=self.loggerBox)
    elif return_data1[1][0] <= 1e-03:
        log.d("buy operation succeeded", level=1, logger_box=self.loggerBox)
        self.operation("click", (return_data1[0][0], return_data1[0][1]), duration=0.5)
        self.operation("click", (770, 480))
    elif return_data3[1][0] <= 1e-03:
        log.d("items have been brought", level=1, logger_box=self.loggerBox)
    else:
        log.d("Can't detect button", level=2, logger_box=self.loggerBox)
        return False
    if activity == "collect_shop_power":
        self.main_activity[5][1] = 1
        log.d("collect shop power task finished", level=1, logger_box=self.loggerBox)
    else:
        self.main_activity[4][1] = 1
        log.d("shop task finished", level=1, logger_box=self.loggerBox)
    return True
