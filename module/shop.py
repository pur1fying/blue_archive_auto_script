import time
import numpy as np
from core.utils import get_x_y,kmp
from gui.util import log
from gui.util.config_set import ConfigSet


def implement(self, activity="shop"):
    self.operation("stop_getting_screenshot_for_location")
    if activity == "collect_shop_power":
        refresh_time = int(self.config.get("ArenaShopRefreshTime"))
        log.d("REFRESH time: " + str(refresh_time), level=1, logger_box=self.loggerBox)
        buy_list = np.array(self.config.get("ArenaShopList"))
        self.operation("click", (100, 370), duration=0.5)
        for i in range(0, refresh_time + 1):
            # 选择商品
            buy_list_for_power_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                        [700, 461], [857, 461], [1000, 461], [1162, 461]]
            for j in range(0, 8):
                if buy_list[j]:
                    self.operation("click",(buy_list_for_power_items[j][0], buy_list_for_power_items[j][1]),duration=0.1)
            if buy_list[8:].any():
                log.d("SWIPE DOWNWARDS", level=1, logger_box=self.loggerBox)
                self.operation("swipe", [(932, 550), (932, 0)], duration=0.3)
                for j in range(8, 13):
                    if buy_list[j]:
                        time.sleep(0.1)
                        self.operation("click",(buy_list_for_power_items[j % 8][0], buy_list_for_power_items[j % 8][1]))

            # 判断是否能够购买
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
            print(return_data3)
            if return_data2[1][0] <= 1e-03:
                log.d("assets inadequate", level=1, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                break
            elif return_data1[1][0] <= 1e-03:
                log.d("buy operation succeeded", level=1, logger_box=self.loggerBox)
                self.operation("click", (return_data1[0][0], return_data1[0][1]), duration=0.5)
                self.operation("click", (770, 480), duration=1)
                if i != refresh_time:
                    self.operation("click@anywhere", (650, 58))
                    self.operation("click@anywhere", (650, 58), duration=0.5)
                else:   # 最后一次购买
                    self.operation("click@home", (1240, 29))
                    self.operation("click@home", (1240, 29))
                    self.operation("click@home", (1240, 29))
                    break
            elif return_data3[1][0] <= 1e-03:
                log.d("items have been brought", level=1, logger_box=self.loggerBox)
                if i == refresh_time:
                    self.operation("click@home", (1240, 29))
                    break
            else:
                log.d("Can't detect button", level=2, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                return False

            # 刷新
            self.common_icon_bug_detect_method("src/shop/update.png", 650, 58, "refresh", times=5)
            self.operation("click@refresh", (938, 660), duration=0.5)
            self.latest_img_array = self.operation("get_screenshot_array")
            ocr_res = self.img_ocr(self.latest_img_array)
            if kmp("通知", ocr_res):
                log.d("zero refresh time", level=2, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                self.operation("click@home", (1240, 29))
                break
            elif kmp("说明", ocr_res) or kmp("取消", ocr_res):
                log.d("refresh available", level=1, logger_box=self.loggerBox)
                self.operation("click@confirm", (773, 461),duration=0.5)
            else:
                log.d("Can't detect if refresh is available", level=2, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                self.operation("click@home", (1240, 29))
                break
    else:
        refresh_time = int(self.config.get("ShopRefreshTime"))
        log.d("REFRESH time: " + str(refresh_time), level=1, logger_box=self.loggerBox)
        buy_list = np.array(self.config.get("ShopList")) # ** 每日商品购买表 1 表示购买
        # buy_list = [0, 0, 0, 0,     # ** 每日商品购买表 1 表示购买
        #             1, 1, 1, 1,
        #             1, 1, 1, 1,
        #             1, 1, 1, 1]
        buy_list_for_common_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                     [700, 461], [857, 461], [1000, 461], [1162, 461]]
        for i in range(0, refresh_time + 1):
            # 选择商品
            buy_list_for_power_items = [[700, 204], [857, 204], [1000, 204], [1162, 204],
                                        [700, 461], [857, 461], [1000, 461], [1162, 461]]
            for j in range(0, 8):
                if buy_list[j]:
                    self.operation("click", (buy_list_for_power_items[j][0], buy_list_for_power_items[j][1]),
                                   duration=0.1)
            if buy_list[8:].any():
                log.d("SWIPE DOWNWARDS", level=1, logger_box=self.loggerBox)
                self.operation("swipe", [(932, 550), (932, 0)], duration=0.3)
                for j in range(8, 16):
                    if buy_list[j]:
                        time.sleep(0.1)
                        self.operation("click",
                                       (buy_list_for_power_items[j % 8][0], buy_list_for_power_items[j % 8][1]))

            # 判断是否能够购买
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
            print(return_data3)
            if return_data2[1][0] <= 1e-03:
                log.d("assets inadequate", level=1, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                break
            elif return_data1[1][0] <= 1e-03:
                log.d("buy operation succeeded", level=1, logger_box=self.loggerBox)
                self.operation("click", (return_data1[0][0], return_data1[0][1]), duration=0.5)
                self.operation("click", (770, 480), duration=1)
                if i != refresh_time:
                    self.operation("click@anywhere", (650, 58))
                    self.operation("click@anywhere", (650, 58), duration=0.5)
                else:  # 最后一次购买
                    self.operation("click@home", (1240, 29))
                    self.operation("click@home", (1240, 29))
                    self.operation("click@home", (1240, 29))
                    break
            elif return_data3[1][0] <= 1e-03:
                log.d("items have been brought", level=1, logger_box=self.loggerBox)
                if i == refresh_time:
                    self.operation("click@home", (1240, 29))
                    break
            else:
                log.d("Can't detect button", level=2, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                return False

            # 刷新
            self.common_icon_bug_detect_method("src/shop/update.png", 650, 58, "refresh", times=5)
            self.operation("click@refresh", (938, 660), duration=0.5)
            self.latest_img_array = self.operation("get_screenshot_array")
            ocr_res = self.img_ocr(self.latest_img_array)
            if kmp("通知", ocr_res):
                log.d("zero refresh time", level=2, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                self.operation("click@home", (1240, 29))
                break
            elif kmp("说明", ocr_res) or kmp("取消", ocr_res):
                log.d("refresh available", level=1, logger_box=self.loggerBox)
                self.operation("click@confirm", (773, 461), duration=0.5)
            else:
                log.d("Can't detect if refresh is available", level=2, logger_box=self.loggerBox)
                self.operation("click@home", (1240, 29))
                self.operation("click@home", (1240, 29))
                break

    if activity == "collect_shop_power":
        self.main_activity[5][1] = 1
        log.d("collect shop power task finished", level=1, logger_box=self.loggerBox)
    else:
        self.main_activity[4][1] = 1
        log.d("shop task finished", level=1, logger_box=self.loggerBox)

    self.operation("start_getting_screenshot_for_location")
    return True
