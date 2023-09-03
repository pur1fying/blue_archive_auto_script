import os
import time
import log
from device_connect import device_connecter
from definemytime import my_time
import cv2
import numpy as np


class screen_operate(device_connecter, my_time):
    def get_x_y(self, target_path, template_path):
        img1 = cv2.imread(target_path)
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

    def get_screen_shot_path(self):
        screenshot = self.device.screenshot()
        save_folder = "logs"
        t = self.return_current_time()
        file_name = t + ".jpg"
        save_path = os.path.join(save_folder, file_name)
        screenshot.save(save_path)
        return save_path

    def clicker(self, path1, add_x=0, add_y=0):
        shot_path = self.get_screen_shot_path()
        lo = self.get_x_y(shot_path, path1)
        log.o_p("click(" + str(lo[0]) + "," + str(lo[1]) + ")", 1)
        self.device.click(lo[0]+add_x, lo[1]+add_y)

    def img_crop(self, path1, start_row, end_row, start_col, end_col):
        img = cv2.imread(path1)
        path1 = "logs//" + str(time.time()) + ".jpg"
        img = img[start_col:end_col, start_row:end_row]
        cv2.imwrite(path1, img)
        return path1

if __name__ == "__main__":
    # 1215 625
    t = screen_operate()

#    img1 = cv2.imread(path1)
#    print(img1.shape)
#    print(img1[625][1196], img1[625][1215], img1[625][1230])
#    for i in range(0, 3):
#       print((img1[625][1196][i]//3+img1[625][1215][i]//3+img1[625][1230][i]//3))
    path1 = t.get_screen_shot_path()
    path2 = "src/create/finish_instantly.png"
    path3 = "src/create/start_button_grey.png"
    return_data1 = t.get_x_y(path1, path2)
    return_data2 = t.get_x_y(path1, path3)
    print(return_data1[1][0], return_data2[1][0])
