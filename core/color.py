import threading
import time
import numpy as np


def wait_loading(self):
    t_start = time.time()
    while self.flag_run:
        screenshot_interval = time.time() - self.latest_screenshot_time
        if screenshot_interval < self.screenshot_interval:
            time.sleep(self.screenshot_interval - screenshot_interval)
        threading.Thread(target=self.screenshot_worker_thread).start()
        self.wait_screenshot_updated()
        if judgeRGBFeature(self, "loadingNotWhite") and judgeRGBFeature(self, "loadingWhite"):
                t_load = time.time() - t_start
                t_load = round(t_load, 3)
                self.logger.info("loading, t load : " + str(t_load))
                if t_load > 20:
                    self.logger.warning("LOADING TOO LONG add screenshot interval to 1")
                    t_start = time.time()
                    self.set_screenshot_interval(1)
                time.sleep(self.screenshot_interval)
                continue
        return True


def judge_rgb_range(self, x, y, r_min, r_max, g_min, g_max, b_min, b_max, check_nearby=False, nearby_range=1):
    if r_min <= self.latest_img_array[int(y * self.ratio)][int(x * self.ratio)][2] <= r_max and \
        g_min <= self.latest_img_array[int(y * self.ratio)][int(x * self.ratio)][1] <= g_max and \
        b_min <= self.latest_img_array[int(y * self.ratio)][int(x * self.ratio)][0] <= b_max:
        return True
    if check_nearby:
        for i in range(nearby_range * -1, nearby_range + 1):
            for j in range(nearby_range * -1, nearby_range + 1):
                if r_min <= self.latest_img_array[int(y * self.ratio) + i][int(x * self.ratio) + j][2] <= r_max and \
                    g_min <= self.latest_img_array[int(y * self.ratio) + i][int(x * self.ratio) + j][1] <= g_max and \
                    b_min <= self.latest_img_array[int(y * self.ratio) + i][int(x * self.ratio) + j][0] <= b_max:
                    return True
    return False


def judgeRGBFeature(self, featureName):                                         # all rgb in range return True
    if featureName not in self.rgb_feature:
        return False
    if featureName in self.rgb_feature:
        for i in range(0, len(self.rgb_feature[featureName][0])):
            if not judge_rgb_range(self,
                                   self.rgb_feature[featureName][0][i][0],
                                   self.rgb_feature[featureName][0][i][1],
                                   self.rgb_feature[featureName][1][i][0],
                                   self.rgb_feature[featureName][1][i][1],
                                   self.rgb_feature[featureName][1][i][2],
                                   self.rgb_feature[featureName][1][i][3],
                                   self.rgb_feature[featureName][1][i][4],
                                   self.rgb_feature[featureName][1][i][5]):
                return False
    return True


def judgeRGBFeatureOr(self, featureName):                                   # any rgb in range return True
    if featureName in self.rgb_feature:
        for i in range(0, len(self.rgb_feature[featureName][0])):
            if judge_rgb_range(self,
                               self.rgb_feature[featureName][0][i][0],
                               self.rgb_feature[featureName][0][i][1],
                               self.rgb_feature[featureName][1][i][0],
                               self.rgb_feature[featureName][1][i][1],
                               self.rgb_feature[featureName][1][i][2],
                               self.rgb_feature[featureName][1][i][3],
                               self.rgb_feature[featureName][1][i][4],
                               self.rgb_feature[featureName][1][i][5]):
                return True
    return False


def check_sweep_availability(self, is_mainline=False):
    if self.server == "CN" or self.server == "Global" or (self.server == "JP" and is_mainline):
        if judgeRGBFeature(self, "mainLineTaskNoPass"):
            return "no-pass"
        if judgeRGBFeature(self, "mainLineTaskSSS"):
            return "sss"
        if judgeRGBFeatureOr(self, "mainLineTaskSSS"):
            return "pass"
    if self.server == "JP" and not is_mainline:
        if judgeRGBFeature(self, "sideTaskNoPass"):
            return "no-pass"
        if judgeRGBFeature(self, "sideTaskSSS"):
            return "sss"
        if judgeRGBFeatureOr(self, "sideTaskSSS"):
            return "pass"
    return "UNKNOWN"


def getRegionMeanRGB(image, x1, y1, x2, y2):
    return image[y1:y2, x1:x2].mean(axis=0).mean(axis=0)


def compareTotalRGBDiff(rgb1, rgb2, threshold):
    return calcTotalRGBDiff(rgb1, rgb2) < threshold


def compareEachRGBDiff(rgb1, rgb2, threshold):
    if type(threshold) is int:
        threshold = [threshold, threshold, threshold]
    return abs(rgb1[0] - rgb2[0]) < threshold[0] and abs(rgb1[1] - rgb2[1]) < threshold[1] and abs(rgb1[2] - rgb2[2]) < \
        threshold[2]


def calcTotalRGBDiff(rgb1, rgb2):
    return abs(rgb1[0] - rgb2[0]) + abs(rgb1[1] - rgb2[1]) + abs(rgb1[2] - rgb2[2])


def calcTotalRGBMeanABSDiff(img1, img2):
    return np.abs(img1 - img2).mean()
