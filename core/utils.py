import os
import sys

import numpy as np
import uiautomator2 as u2

import cv2


def build_next_array(patten):
    next_array = [0]
    prefix_len = 0
    i = 1
    while i < len(patten):
        if patten[prefix_len] == patten[i]:
            prefix_len += 1
            next_array.append(prefix_len)
            i += 1
        else:
            if prefix_len == 0:
                next_array.append(0)
                i += 1
            else:
                prefix_len = next_array[prefix_len - 1]
    return next_array


def kmp(patten, string):
    next_array = build_next_array(patten)
    i = 0
    j = 0
    cnt = 0
    len1 = len(patten)
    len2 = len(string) - 1
    while i <= len2:
        if string[i] == patten[j]:
            i += 1
            j += 1
        elif j >= 1:
            j = next_array[j - 1]
        else:
            i += 1
        if j == len1:
            cnt += 1
            j = next_array[j - 1]
    return cnt


def get_screen_shot_array():
    screenshot = u2.connect().screenshot()
    numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
    return numpy_array


def img_crop(img, start_row, end_row, start_col, end_col):
    img = img[start_col:end_col, start_row:end_row]
    return img


def get_x_y(target_array, template_path: str):
    print(target_array.dtype)
    if template_path.startswith("./src"):
        template_path = template_path.replace("./src", "src")
    elif template_path.startswith("../src"):
        template_path = template_path.replace("../src", "src")
    img1 = target_array
    img2 = cv2.imread(template_path)
    # sys.stdout = open('data.log', 'w+')
    height, width, channels = img2.shape

    print(img2.shape)
    for i in range(0, height):
        print([x for x in img2[i, :, 0]])

    result = cv2.matchTemplate(img1, img2, cv2.TM_SQDIFF_NORMED)
    upper_left = cv2.minMaxLoc(result)[2]
    print(img1.shape)
    print(upper_left[0], upper_left[1])
    # cv2.imshow("img2", img2)

    converted = img1[upper_left[1]:upper_left[1] + height, upper_left[0]:upper_left[0] + width, :]

#     cv2.imshow("img1", converted)
    sub = cv2.subtract(img2, converted)
    # cv2.imshow("result", cv2.subtract(img2, converted))
    for i in range(0, height):
        print([x for x in converted[i, :, 0]])
    # cv2.imshow("img1", img1)
    # cv2.waitKey(0)
    location = (int(upper_left[0] + height / 2), int(upper_left[1] + width / 2))
    return location, result[upper_left[1], [upper_left[0]]]
