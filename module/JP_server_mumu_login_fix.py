import uiautomator2

from core import picture, image
import threading
def accept_su_thread(self):
    img_ends = "mumu_accept-su1"
    picture.co_detect(self, img_ends=img_ends, skip_first_screenshot=False)
    if not self.flag_run:
        return
    self.logger.info("Accept Super User Permission Automatically")
    img_possibles = {
        "mumu_accept-su1": (574, 553)
    }
    img_ends = "mumu_accept-su2"
    picture.co_detect(self, img_ends=img_ends, img_possibles=img_possibles,skip_first_screenshot=True)
    while image.compare_image(self, "mumu_accept-su2", False, 0.8, 20):
        self.click(751, 627, wait_over=True, duration=0.3)
        self.latest_img_array = self.get_screenshot_array()
        if not self.flag_run:
            return


def implement(self):
    self.logger.info("[ su ] response : ")
    threading.Thread(target=accept_su_thread, args=(self,)).start()
    res = self.connection.shell('su')
    self.logger.info(str(res))
    if not res.exit_code == 0:
        self.logger.error("Failed to get root permission,possible reason")
        self.logger.error("1. The device is not rooted")
        self.logger.error("2. You didn't enable disk read/write permission")
        self.logger.error("3. Window Size of the deivce is not correct, you have accept su manually")
        self.logger.error("Please Turn on the disk read and write permission and enable root permission, then try again")
        self.flag_run = False
        return False
    self.logger.info("[ su -c '{rm -rf /system/xbin/mu_bak' ] response : ")
    res = self.connection.shell('su -c \'rm -rf /system/xbin/mu_bak\'')
    self.logger.info(str(res))
    if not res.exit_code == 0:
        self.logger.error("Failed to delete file [ mu_bak ] and [ su ]")
        self.flag_run = False
        return False
    self.flag_run = False
    return True
