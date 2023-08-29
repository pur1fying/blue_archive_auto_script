import os
import time
import log
from device_connect import device_connecter
from definemytime import my_time
import cv2
import numpy as np


class screen_operate(device_connecter, my_time):
    def get_x_y(self, target_path, template_path):
        img1 = cv2.imread(template_path)
        img2 = cv2.imread(target_path)

        height, width, channels = img1.shape

        result = cv2.matchTemplate(img2, img1, cv2.TM_SQDIFF_NORMED)
        upper_left = cv2.minMaxLoc(result)[2]

        location = (int(upper_left[0] + height / 2), int(upper_left[1] + width / 2))
        return location

    def get_screen_shot_path(self):
        screenshot = self.device.screenshot()
        save_folder = "logs"
        t = self.return_current_time()
        file_name = t + ".png"
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
        path1 = "logs//" + str(time.time()) + ".png"
        img = img[start_col:end_col, start_row:end_row]
        cv2.imwrite(path1, img)
        return path1

if __name__ == "__main__":

    t = screen_operate()
    t.get_screen_shot_path()