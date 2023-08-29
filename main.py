import log
from activity_solver import solver
import threading
import time
import os


class baas(solver):
    def __init__(self):
        super().__init__()
        # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.package_name = 'com.RoamingStar.BlueArchive'
        self.exit_loop = False
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
        t2 = time.time()
        path = self.get_screen_shot_path()
        shot_time = time.time() - self.base_time
        print(shot_time)
        self.get_keyword_appear_time(self.img_ocr(path))
        locate_res = self.return_location()
        print(locate_res)
        ct = time.time()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, ct - self.base_time])
        if len(self.pos) > 2:
            self.pos.pop()

    def run(self):
        self.base_time = time.time()
        while 1:
            if self.exit_loop:
                break
            threading.Thread(target=self.worker).start()
            time.sleep(1)

    def Thread_starter(self):
        thread_run = threading.Thread(target=self.run)
        thread_run.start()

        if len(self.pos) == 2 and self.pos[0] == self.pos[1]:
            log.o_p("current_location : " + self.pos[0], 1)
            self.solve(self.pos[0])
            self.pos.clear()
            self.click_time = time.time()



if __name__ == '__main__':
    b_aas = baas()
    b_aas.Thread_starter()
