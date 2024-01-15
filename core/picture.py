import time
from core import color, image


def co_detect(self, rgb_ends=None,rgb_possibles=None,  img_ends=None,img_possibles=None,  skip_first_screenshot=False, tentitive_click = False):
    fail_cnt = 0
    while True:
        if not self.flag_run:
            return False
        if skip_first_screenshot:
            skip_first_screenshot = False
        else:
            color.wait_loading(self)
        if rgb_ends is not None:
            if type(rgb_ends) is str:
                rgb_ends = [rgb_ends]
            for i in range(0, len(rgb_ends)):
                if rgb_ends[i] not in self.rgb_feature:
                    continue
                for j in range(0, len(self.rgb_feature[rgb_ends[i]][0])):
                    if not color.judge_rgb_range(self.latest_img_array,
                                                 self.rgb_feature[rgb_ends[i]][0][j][0],
                                                 self.rgb_feature[rgb_ends[i]][0][j][1],
                                                 self.rgb_feature[rgb_ends[i]][1][j][0],
                                                 self.rgb_feature[rgb_ends[i]][1][j][1],
                                                 self.rgb_feature[rgb_ends[i]][1][j][2],
                                                 self.rgb_feature[rgb_ends[i]][1][j][3],
                                                 self.rgb_feature[rgb_ends[i]][1][j][4],
                                                 self.rgb_feature[rgb_ends[i]][1][j][5]):
                        break
                else:
                    self.logger.info("end : " + rgb_ends[i])
                    return rgb_ends[i]
        if img_ends is not None:
            if type(img_ends) is str:
                img_ends = [img_ends]
            for i in range(0, len(img_ends)):
                if image.compare_image(self, img_ends[i], 3, image=self.latest_img_array, need_log=False):
                    self.logger.info('end : ' + img_ends[i])
                    return img_ends[i]
        f = 0
        if rgb_possibles is not None:
            for position, click in rgb_possibles.items():
                if position not in self.rgb_feature:
                    continue
                for j in range(0, len(self.rgb_feature[position][0])):
                    if not color.judge_rgb_range(self.latest_img_array,
                                                 self.rgb_feature[position][0][j][0],
                                                 self.rgb_feature[position][0][j][1],
                                                 self.rgb_feature[position][1][j][0],
                                                 self.rgb_feature[position][1][j][1],
                                                 self.rgb_feature[position][1][j][2],
                                                 self.rgb_feature[position][1][j][3],
                                                 self.rgb_feature[position][1][j][4],
                                                 self.rgb_feature[position][1][j][5]):
                        break
                else:
                    fail_cnt = 0
                    self.logger.info("find : " + position)
                    self.click(click[0], click[1], False)
                    self.latest_screenshot_time = time.time()
                    f = 1
                    break
        if f == 0:
            for position, click in img_possibles.items():
                threshold = 3
                if len(position) == 3:
                    threshold = position[2]
                if image.compare_image(self, position, threshold, need_loading=False, image=self.latest_img_array,
                                       need_log=False):
                    self.logger.info("find " + position)
                    self.click(click[0], click[1], False)
                    self.latest_screenshot_time = time.time()
                    fail_cnt = 0
                    break
            if tentitive_click:
                fail_cnt += 1
                if fail_cnt > 20:
                    self.logger.info("tentative clicks")
                    self.click(1228, 41, False)
                    time.sleep(self.screenshot_interval)
                    fail_cnt = 0
