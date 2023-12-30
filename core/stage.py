import time

import cv2
import numpy as np
from core import color, image


def wait_loading(self):
    t_start = time.time()
    while 1:
        self.latest_img_array = self.get_screenshot_array()
        if not color.judge_rgb_range(self.latest_img_array, 937, 648, 200, 255, 200, 255, 200, 255) or not \
                color.judge_rgb_range(self.latest_img_array, 919, 636, 200, 255, 200, 255, 200, 255):
            loading_pos = [[929, 664], [941, 660], [979, 662], [1077, 665], [1199, 665]]
            rgb_loading = [[200, 255, 200, 255, 200, 255], [200, 255, 200, 255, 200, 255],
                           [200, 255, 200, 255, 200, 255], [200, 255, 200, 255, 200, 255],
                           [255, 255, 255, 255, 255, 255]]
            t = len(loading_pos)
            for i in range(0, t):
                if not color.judge_rgb_range(self.latest_img_array, loading_pos[i][0], loading_pos[i][1],
                                             rgb_loading[i][0],
                                             rgb_loading[i][1], rgb_loading[i][2], rgb_loading[i][3],
                                             rgb_loading[i][4], rgb_loading[i][5]):
                    break
            else:
                t_load = time.time() - t_start
                t_load = round(t_load, 3)
                self.logger.info("loading, t load : " + str(t_load))
                if t_load > 20:
                    self.logger.warning("LOADING TOO LONG add screenshot interval to 1")
                    t_start = time.time()
                    self.screenshot_interval = 1
                time.sleep(self.screenshot_interval)
                continue

        return True
