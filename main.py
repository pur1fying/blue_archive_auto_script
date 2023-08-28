import log
from activity_solver import solver


class baas(solver):
    def __init__(self):
        super().__init__()
        # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
        self.package_name = 'com.RoamingStar.BlueArchive'
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
            if not self.exit_loop :



if __name__ == '__main__':
    bbaas = baas()
    bbaas.start_ba()