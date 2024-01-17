import time
from core import color, picture


def to_main_story(self, skip_first_screenshot=False):
    rgb_possibles = {
        'main_page': (1188, 575)
    }
    img_possibles = {
        "main_page_bus": (1098, 261),
        "main_story_enter-main-story": (327, 510),
        "main_story_final-ep-feature": (149, 109),
    }
    img_ends = "main_story_menu"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def implement(self):
    self.logger.info("START pushing main story")
    self.quick_method_to_main_page()
    to_main_story(self)

    return True

def change_acc_auto(self):
    y = 625
    acc_r_ave = int(self.latest_img_array[y][1196][0]) // 3 + int(self.latest_img_array[y][1215][0]) // 3 + int(
        self.latest_img_array[y][1230][0]) // 3
    if 250 <= acc_r_ave <= 260:
        self.logger.info("CHANGE acceleration phase from 2 to 3")
        self.click(1215, y)
    elif 0 <= acc_r_ave <= 60:
        self.logger.info("ACCELERATION phase 3")
    elif 140 <= acc_r_ave <= 180:
        self.logger.info("CHANGE acceleration phase from 1 to 3")
        self.click(1215, y, wait=False, count=2)
    else:
        self.logger.warning("CAN'T DETECT acceleration BUTTON")
    y = 677
    auto_r_ave = int(self.latest_img_array[y][1171][0]) // 2 + int(self.latest_img_array[y][1246][0]) // 2
    if 190 <= auto_r_ave <= 230:
        self.logger.info("CHANGE MANUAL to auto")
        self.click(1215, y, wait=False)
    elif 0 <= auto_r_ave <= 60:
        self.logger.info("AUTO")
    else:
        self.logger.warning("can't identify auto button")


def enter_fight(self):
    t_start = time.time()
    while time.time() <= t_start + 20:
        self.latest_img_array = self.get_screenshot_array()
        if not color.judge_rgb_range(self.latest_img_array, 831, 692, 0, 64, 161, 217, 240, 255):
            time.sleep(self.screenshot_interval)
        else:
            break


def auto_fight(self):
    enter_fight(self)
    change_acc_auto(self)
