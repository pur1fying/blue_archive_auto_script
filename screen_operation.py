import os
import time
from definemytime import my_time
import cv2
import uiautomator2 as u2
import io
import numpy as np
from PIL import Image

class screen_operate( my_time):
    def get_x_y(self, target_array, template_path):
        img1 = target_array
        img2 = cv2.imread(template_path)
        t2 = time.time()
        width, height, channels = img2.shape
        result = cv2.matchTemplate(img1, img2, cv2.TM_SQDIFF_NORMED)
        t3 = time.time()
        upper_left = cv2.minMaxLoc(result)[2]
#        cv2.rectangle(img1, upper_left, [upper_left[0]+height,upper_left[1]+width], (0, 255, 0), 2)
#        cv2.imshow("Matched Image", img1)
#        cv2.waitKey(0)
#        cv2.destroyAllWindows()

        location = (int(upper_left[0] + height / 2), int(upper_left[1] + width / 2))
        return location, result[upper_left[1], [upper_left[0]]]

    def get_screen_shot_array(self):
        screenshot = u2.connect().screenshot()
        #screenshot.save('./logs/1.png')
        # image = Image.open(io.BytesIO(screenshot))
        numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
        # print(numpy_array.shape)
        # cv2.imshow('Image', numpy_array)
        # screenshot.show()
        return numpy_array

    def img_crop(self, img, start_row, end_row, start_col, end_col):
        img = img[start_col:end_col, start_row:end_row]
        return img

if __name__ == "__main__":
    # 1215 625
    t = screen_operate()

#    img1 = cv2.imread(path1)
#    print(img1.shape)
#    print(img1[625][1196], img1[625][1215], img1[625][1230])
#    for i in range(0, 3):
#       print((img1[625][1196][i]//3+img1[625][1215][i]//3+img1[625][1230][i]//3))
    img_shot = t.get_screen_shot_array()
    path1 = "src/common_button/fail_check.png"
    path2 = "src/common_button/back_to_main_page.png"
    path3 = "src/arena/collect_reward1.png"
    return_data1 = t.get_x_y(img_shot, path1)
    return_data2 = t.get_x_y(img_shot, path2)
    return_data3 = t.get_x_y(img_shot, path3)
    print(return_data1[1][0], return_data2[1][0],return_data3[1][0])
