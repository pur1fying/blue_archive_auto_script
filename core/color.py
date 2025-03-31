import time
import typing

import numpy as np

from core import Baas_thread


def wait_loading(self: Baas_thread) -> None:
    startTime = time.time()
    while (self.flag_run and
           match_rgb_feature(self, "loadingNotWhite") and match_rgb_feature(self, "loadingWhite")):
        self.update_screenshot_array()
        loadingTime = round(time.time() - startTime, 3)
        self.logger.info("Detected loading, loading time: " + str(loadingTime))
        time.sleep(self.screenshot_interval)
    return


def rgb_in_range(self, x: int, y: int, r_min: int, r_max: int, g_min: int, g_max: int, b_min: int, b_max: int,
                 check_nearby=False, nearby_range=1):
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


def match_rgb_feature(self, featureName):
    """
    Check if all RGB values in the specified feature are within the defined range.

    Args:
        self: The BAAS thread.
        featureName (str): The name of the feature to match.

    Returns:
        bool: True if all RGB values in the feature are within the range, False otherwise.
    """
    if featureName not in self.rgb_feature:
        return False
    for i in range(0, len(self.rgb_feature[featureName][0])):
        if not rgb_in_range(self,
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


def match_any_rgb_feature(self: Baas_thread, featureList: list[typing.Union[tuple, str]]) -> bool:
    for rgb_feature in featureList:
        if match_rgb_feature(self, rgb_feature):
            return True
    return False


def match_any_rgb_in_feature(self, featureName):
    """
    Check if any RGB values in the specified feature are within the defined range.

    Args:
        self: The BAAS thread.
        featureName (str): The name of the feature to match.

    Returns:
        bool: True if at least a group of RGB values in the feature are within the range, False otherwise.
    """
    if featureName in self.rgb_feature:
        for i in range(0, len(self.rgb_feature[featureName][0])):
            if rgb_in_range(self,
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
    if is_mainline:
        if match_rgb_feature(self, "mainLineTaskNoPass"):
            return "no-pass"
        if match_rgb_feature(self, "mainLineTaskSSS"):
            return "sss"
        if match_any_rgb_in_feature(self, "mainLineTaskSSS"):
            return "pass"
    if not is_mainline:
        if match_rgb_feature(self, "sideTaskNoPass"):
            return "no-pass"
        if match_rgb_feature(self, "sideTaskSSS"):
            return "sss"
        if match_any_rgb_in_feature(self, "sideTaskSSS"):
            return "pass"
    return "unknown"


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
