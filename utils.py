import cv2
import time


def get_x_y(target_path, template_path):
    img1 = cv2.imread(template_path)
    img2 = cv2.imread(target_path)

    height, width, channels = img1.shape

    result = cv2.matchTemplate(img2, img1, cv2.TM_SQDIFF_NORMED)
    upper_left = cv2.minMaxLoc(result)[2]

    location = (int(upper_left[0] + height / 2), int(upper_left[1] + width / 2))
    return location


def img_crop(path1, start_row, end_row, start_col, end_col):
    img = cv2.imread(path1)
    path1 = "logs//" + str(time.time()) + ".png"
    img = img[start_col:end_col, start_row:end_row]
    cv2.imwrite(path1, img)
    return path1
