import log
from activity_solver import Solver


class baas(Solver):
    def __init__(self):
        super().__init__()
        # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.package_name = 'com.RoamingStar.BlueArchive.bilibili'
        self.exit_loop = False

    def start_ba(self):
        self.device.app_start(self.package_name)
        t = self.device.window_size()
        log.o_p("Screen Size  " + str(t), 1)
        if t[0] == 1080 and t[1] == 1920:
            log.o_p("Screen Size Fitted", 1)
        else:
            log.o_p("Screen Size unfitted", 3)

    def loop(self):
        while 1:
            if not self.exit_loop:
                pass


if __name__ == '__main__':
    baas().start_ba()
