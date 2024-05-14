import threading
import time


def wait_loading(self):
    t_start = time.time()
    while self.flag_run:
        screenshot_interval = time.time() - self.latest_screenshot_time
        if screenshot_interval < self.screenshot_interval:
            time.sleep(self.screenshot_interval - screenshot_interval)
        threading.Thread(target=self.screenshot_worker_thread).start()
        self.wait_screenshot_updated()
        not_white_position = [[937, 648], [919, 636]]
        white_position = [[929, 664], [941, 660], [979, 662], [1077, 665], [1199, 665]]
        if self.server == "CN":
            not_white_position = [[1048, 638], [950, 660]]
            white_position = [[1040, 654], [970, 651], [1102, 659], [1077, 665], [1201, 665]]
        for i in range(0, len(not_white_position)):
            if judge_rgb_range(self, not_white_position[i][0], not_white_position[i][1],
                               200, 255, 200, 255, 200, 255):
                break
        else:
            for i in range(0, len(white_position)):
                if not judge_rgb_range(self, white_position[i][0], white_position[i][1],
                                       200, 255, 200, 255, 200, 255):
                    break
            else:
                t_load = time.time() - t_start
                t_load = round(t_load, 3)
                self.logger.info("loading, t load : " + str(t_load))
                if t_load > 20:
                    self.logger.warning("LOADING TOO LONG add screenshot interval to 1")
                    t_start = time.time()
                    self.set_screenshot_interval(1)
                time.sleep(self.screenshot_interval)
                continue
        return True


def judge_rgb_range(self, x, y, r_min, r_max, g_min, g_max, b_min, b_max, check_nearby=False, nearby_range=1):
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


def check_sweep_availability(self, is_mainline=False):
    if self.server == "CN":
        if judge_rgb_range(self, 211, 369, 192, 212, 192, 212, 192, 212) and \
            judge_rgb_range(self, 211, 402, 192, 212, 192, 212, 192, 212) and \
            judge_rgb_range(self, 211, 436, 192, 212, 192, 212, 192, 212):
            return "no-pass"
        if judge_rgb_range(self, 211, 368, 225, 255, 200, 255, 20, 60) and \
            judge_rgb_range(self, 211, 404, 225, 255, 200, 255, 20, 60) and \
            judge_rgb_range(self, 211, 434, 225, 255, 200, 255, 20, 60):
            return "sss"
        if judge_rgb_range(self, 211, 368, 225, 255, 200, 255, 20, 60) or \
            judge_rgb_range(self, 211, 404, 225, 255, 200, 255, 20, 60) or \
            judge_rgb_range(self, 211, 434, 225, 255, 200, 255, 20, 60):
            return "pass"
        return "UNKNOWN"
    elif self.server == "Global" or (self.server == "JP" and not is_mainline):
        if judge_rgb_range(self, 169, 369, 192, 212, 192, 212, 192, 212) and \
            judge_rgb_range(self, 169, 405, 192, 212, 192, 212, 192, 212) and \
            judge_rgb_range(self, 169, 439, 192, 212, 192, 212, 192, 212):
            return "no-pass"
        if judge_rgb_range(self, 169, 369, 225, 255, 200, 255, 20, 60) and \
            judge_rgb_range(self, 169, 405, 225, 255, 200, 255, 20, 60) and \
            judge_rgb_range(self, 169, 439, 225, 255, 200, 255, 20, 60):
            return "sss"
        if judge_rgb_range(self, 169, 369, 225, 255, 200, 255, 20, 60) or \
            judge_rgb_range(self, 169, 405, 225, 255, 200, 255, 20, 60) or \
            judge_rgb_range(self, 169, 439, 225, 255, 200, 255, 20, 60):
            return "pass"
    elif self.server == "JP" and is_mainline:
        if judge_rgb_range(self, 169, 469, 192, 212, 192, 212, 192, 212) and \
            judge_rgb_range(self, 169, 401, 192, 212, 192, 212, 192, 212) and \
            judge_rgb_range(self, 169, 436, 192, 212, 192, 212, 192, 212):
            return "no-pass"
        if judge_rgb_range(self, 169, 469, 225, 255, 200, 255, 20, 60) and \
            judge_rgb_range(self, 169, 401, 225, 255, 200, 255, 20, 60) and \
            judge_rgb_range(self, 169, 436, 225, 255, 200, 255, 20, 60):
            return "sss"
        if judge_rgb_range(self, 169, 469, 225, 255, 200, 255, 20, 60) or \
            judge_rgb_range(self, 169, 401, 225, 255, 200, 255, 20, 60) or \
            judge_rgb_range(self, 169, 436, 225, 255, 200, 255, 20, 60):
            return "pass"
        return "UNKNOWN"
