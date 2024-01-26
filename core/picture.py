import time
from core import color, image


def co_detect(self, rgb_ends=None,rgb_possibles=None,  img_ends=None,img_possibles=None,  skip_first_screenshot=False, tentitive_click=False, tentitivex=1238,tentitivey=45, max_fail_cnt=10):
    fail_cnt = 0
    while self.flag_run:
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
        if f == 1:
            continue
        if img_possibles is not None:
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
                    f = 1
                    break
        if f == 1:
            continue
        if not deal_with_pop_ups(self):
            if tentitive_click:
                fail_cnt += 1
                if fail_cnt > 10:
                    self.logger.info("tentative clicks")
                    self.click(tentitivex,tentitivey, False)
                    time.sleep(self.screenshot_interval)
                    fail_cnt = 0


def deal_with_pop_ups(self):
    img_possibles = {
        'CN': {
            'main_page_news': (1142, 104),
            'main_page_news2': (1142, 104),
        },
        'JP': {
            'main_page_news': (1142, 104),
        },
        'Global': {
            'main_page_news': (1227, 56),
            'main_page_login-store': (883, 162),
        }
    }
    for position, click in img_possibles[self.server].items():
        threshold = 3
        if len(position) == 3:
            threshold = position[2]
        if image.compare_image(self, position, threshold, need_loading=False, image=self.latest_img_array,
                               need_log=False):
            self.logger.info("find " + position)
            self.click(click[0], click[1], False)
            self.latest_screenshot_time = time.time()
            return True, position
    return False
