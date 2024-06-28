from core import picture, image
import threading
def accept_su_thread(self):
    img_ends = "mumu_accept-su1"
    picture.co_detect(self, img_ends=img_ends, skip_first_screenshot=False)
    self.logger.info("Accept Super User Permission Automatically")
    img_possibles = {
        "mumu_accept-su1": (574, 553)
    }
    img_ends = "mumu_accept-su2"
    picture.co_detect(self, img_ends=img_ends, img_possibles=img_possibles,skip_first_screenshot=True)
    while self.flag_run or image.compare_image(self, "mumu_accept-su2", False, 0.8, 20):
        self.click(751, 627, wait_over=True, duration=0.3)
        self.latest_img_array = self.get_screenshot_array()


def implement(self):
    self.logger.info("[ su ] response : ")
    threading.Thread(target=accept_su_thread, args=(self,)).start()
    res = str(self.connection.shell('su'))
    self.logger.info(res)
    if res.find("exit_code=0") == -1:
        self.logger.error("Failed to get root permission possible reason")
        self.logger.error("1. The device is not rooted")
        self.logger.error("2. You didn't enable disk read/write permission")
        self.logger.error("Please Turn on the disk read and write permission and enable root permission, then try again")
        self.flag_run = False
        return False
    self.logger.info("[ su rm -rf /system/xbin/{su,mu_bak} /system/bin/su ] response : ")
    self.logger.info(str(self.connection.shell('su rm -rf /system/xbin/{su,mu_bak} /system/bin/su')))
    self.flag_run = False
    return True
