from core.utils import get_screen_shot_array, img_crop, kmp
import uiautomator2 as u2
import time

from gui.util import log


def implement(self):
    region_name = ["沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区"]

    lo = [[300, 267], [645, 267], [985, 267],
          [300, 413], [645, 413], [985, 413],
          [300, 531], [645, 531], [985, 531]]
    region_schedule_total_count = [7, 7, 8, 8, 8]
    cur_num = self.schedule_pri[0]
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    for i in range(0, len(self.schedule_pri)):
        tar_num = self.schedule_pri[i]
        log.d("begin schedule in <" + region_name[tar_num - 1] + ">", level=1, logger_box=self.loggerBox)
        while cur_num != tar_num:
            if cur_num > tar_num:
                self.connection.click(left_change_page_x, change_page_y)
                self.set_click_time()
                log.d("Click :(" + str(left_change_page_x) + " " + str(
                    change_page_y) + ")" + " click_time = " + str(self.click_time), level=1,
                      logger_box=self.loggerBox)
            else:
                self.connection.click(right_change_page_x, change_page_y)
                self.set_click_time()
                log.d("Click :(" + str(right_change_page_x) + " " + str(
                    change_page_y) + ")" + " click_time = " + str(self.click_time), level=1,
                      logger_box=self.loggerBox)
            cur_lo = self.pd_pos()
            cur_num = int(cur_lo[8:])
            log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
        x = 1160
        y = 664
        self.connection.click(x, y)
        self.set_click_time()
        log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
              logger_box=self.loggerBox)
        if not self.pd_pos() == "all_schedule":
            log.d("not in page all schedule , return", level=3, logger_box=self.loggerBox)
            return
        img_shot = get_screen_shot_array()
        img_cro = img_crop(img_shot, 126, 1167, 98, 719)
        res = self.img_ocr(img_cro)
        count = kmp("需要评级", res)
        start = region_schedule_total_count[self.schedule_pri[0] - 1] - count
        for j in range(0, start):
            x = lo[start - j - 1][0]
            y = lo[start - j - 1][1]
            self.connection.click(x, y)
            log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
                  logger_box=self.loggerBox)
            time.sleep(0.6)
            x = 640
            y = 556
            self.connection.click(640, 556)
            log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
                  logger_box=self.loggerBox)
            self.set_click_time()
            if self.pd_pos() == "notice":
                self.main_activity[7][1] = 1
                log.d("task schedule finished", level=1, logger_box=self.loggerBox)
                return
            time.sleep(2)
            self.set_click_time()
            while self.pd_pos(True) != "all_schedule":
                self.click(919, 116)
