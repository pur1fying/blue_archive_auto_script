import log
from get_location import locate
import threading
import time
import os


class baas(locate):
    def __init__(self):
        super().__init__()
        self.main_activity = ["group", "mail", "schedule", "energy_clear", "cafe", "momo_talk", "create",
                              "story", "combat_power_fight", "arena", "rewarded_task", "collect_daily_reward", "shop"]
        self.to_group = [[580], [650], ["group"]]

        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]
        # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.package_name = 'com.RoamingStar.BlueArchive'
        self.exit_loop = False
        self.unknown_ui_page_count = 0
        self.pos = []
        self.base_time = 0.0
        self.alas_pause = False
        self.click_time = 0.0

    def start_ba(self):
        self.device.app_start(self.package_name)
        t = self.device.window_size()
        log.o_p("Screen Size  " + str(t), 1)
        if t[0] == 1280 and t[1] == 720:
            log.o_p("Screen Size Fitted", 1)
        else:
            log.o_p("Screen Size unfitted", 3)

    def worker(self):
        shot_time = time.time() - self.base_time
        path = self.get_screen_shot_path()

        self.get_keyword_appear_time(self.img_ocr(path))
        locate_res = self.return_location()
        ct = time.time()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, ct - self.base_time])
        if len(self.pos) > 2:
            self.pos.pop()
        print(self.pos)

    def run(self):
        self.base_time = time.time()
        while 1:
            if self.exit_loop:
                break
            threading.Thread(target=self.worker).start()
            time.sleep(2)

    def thread_starter(self):
        thread_run = threading.Thread(target=self.run)
        thread_run.start()
        for i in range(0, len(self.main_activity)):
            while self.main_activity[i][1] == 0:
                self.to_main_page()
                if self.solve(self.main_activity[0][0]):
                    self.main_activity[i][1] = 1

    def pd_pos(self):
        while 1:
            if len(self.pos) == 2 and self.pos[0][0] == self.pos[1][0]:
                lo = self.pos[0][0]
                self.pos.clear()
                log.o_p("current_location : " + lo, 1)
                self.click_time = time.time() - self.base_time
                return lo
            time.sleep(0.5)
    def solve(self, activity):
        log.o_p("begin Group task", 1)
        self.to_main_page()
        if activity == "group":
            for i in range(0, len(self.to_group[0])):
                x = self.to_group[0][i]
                y = self.to_group[1][i]
                page = self.to_group[2][i]
                self.device.click(x, y)
                self.click_time = time.time() - self.base_time
                log.o_p("Click :(" + str(x) + " " + str(y) + ")", 1)
                if self.pd_pos() != page:
                    self.to_main_page()
                    i = 0
        self.to_main_page()
        self.main_activity[1] = 1
        log.o_p("Group task finished", 1)

    def to_main_page(self):
        while 1:
            if not self.pd_pos() == "main_page":
                self.device.click(60, 40)
                log.o_p("Click :(60,40)", 1)
            else:
                break



if __name__ == '__main__':
    b_aas = baas()
    b_aas.thread_starter()
