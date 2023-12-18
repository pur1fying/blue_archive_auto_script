import time


def common_rgb_detect_method(self, click, possible_los, ends):
    t_start = time.time()
    t_total = 0
    while t_total <= 60:
        if not self.flag_run:
            return False
        res = detect_rgb_one_time(self, click, possible_los, ends)
        if not res:
            time.sleep(self.screenshot_interval)
            continue
        elif res[0] == "end":
            return res[1]
        elif res[0] == "click":
            time.sleep(self.screenshot_interval)
            continue
        t_total = time.time() - t_start
    self.logger.critical("Wait Too Long")
    return False


def detect_rgb_one_time(self, click, possible_los, ends):
    self.latest_img_array = self.get_screenshot_array()
    for i in range(0, len(ends)):
        for j in range(0, len(self.rgb_feature[ends[i]][0])):
            if not judge_rgb_range(self.latest_img_array,
                                   self.rgb_feature[ends[i]][0][j][0],
                                   self.rgb_feature[ends[i]][0][j][1],
                                   self.rgb_feature[ends[i]][1][j][0],
                                   self.rgb_feature[ends[i]][1][j][1],
                                   self.rgb_feature[ends[i]][1][j][2],
                                   self.rgb_feature[ends[i]][1][j][3],
                                   self.rgb_feature[ends[i]][1][j][4],
                                   self.rgb_feature[ends[i]][1][j][5]):
                break
        else:
            self.logger.info("end : " + ends[i])  # 出现end中的任意一个，返回对应的位置字符串
            return "end", ends[i]
    for i in range(0, len(possible_los)):  # 可能的图标
        for j in range(0, len(self.rgb_feature[possible_los[i]][0])):  # 每个图标多个，判断rgb
            if not judge_rgb_range(self.latest_img_array,
                                   self.rgb_feature[possible_los[i]][0][j][0],
                                   self.rgb_feature[possible_los[i]][0][j][1],
                                   self.rgb_feature[possible_los[i]][1][j][0],
                                   self.rgb_feature[possible_los[i]][1][j][1],
                                   self.rgb_feature[possible_los[i]][1][j][2],
                                   self.rgb_feature[possible_los[i]][1][j][3],
                                   self.rgb_feature[possible_los[i]][1][j][4],
                                   self.rgb_feature[possible_los[i]][1][j][5]):
                break
        else:
            self.logger.info("position : " + possible_los[i])
            self.click(click[i][0], click[i][1])  # 出现possible_los中的任意一个，点击对应的click坐标
            return "click", True
    return False


def judge_rgb_range(shot_array, x, y, r_min, r_max, g_min, g_max, b_min, b_max):
    if r_min <= shot_array[y][x][2] <= r_max and \
            g_min <= shot_array[y][x][1] <= g_max and \
            b_min <= shot_array[y][x][0] <= b_max:
        return True
    return False


def check_sweep_availability(img, server):
    if server == "CN":
        if judge_rgb_range(img, 211, 369, 192, 212, 192, 212, 192, 212) and \
                judge_rgb_range(img, 211, 402, 192, 212, 192, 212, 192, 212) and \
                judge_rgb_range(img, 211, 436, 192, 212, 192, 212, 192, 212):
            return "no-pass"
        if judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) and \
                judge_rgb_range(img, 211, 404, 225, 255, 200, 255, 20, 60) and \
                judge_rgb_range(img, 211, 434, 225, 255, 200, 255, 20, 60):
            return "sss"
        if judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) or \
                judge_rgb_range(img, 211, 404, 225, 255, 200, 255, 20, 60) or \
                judge_rgb_range(img, 211, 434, 225, 255, 200, 255, 20, 60):
            return "pass"
        return "UNKNOWN"
    elif server == "Global":
        if judge_rgb_range(img, 169, 369, 192, 212, 192, 212, 192, 212) and \
                judge_rgb_range(img, 169, 405, 192, 212, 192,212, 192, 212) and \
                judge_rgb_range(img, 169, 439, 192, 212, 192, 212, 192, 212):
            return "no-pass"
        if judge_rgb_range(img, 169, 369, 225, 255, 200, 255, 20, 60) and \
                judge_rgb_range(img, 169, 405, 225, 255, 200,255, 20, 60) and \
                judge_rgb_range(img, 169, 439, 225, 255, 200, 255, 20, 60):
            return "sss"
        if judge_rgb_range(img, 169, 369, 225, 255, 200, 255, 20, 60) or \
                judge_rgb_range(img, 169, 405, 225, 255, 200,255, 20, 60) or \
                judge_rgb_range(img, 169, 439, 225, 255, 200, 255, 20, 60):
            return "pass"
        return "UNKNOWN"
