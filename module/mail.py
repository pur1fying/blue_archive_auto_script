from core import color, image

import time

x = {
    'menu': (107, 9, 162, 36)
}


def to_mail(self):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (1141, 43)
        }
        image.detect(self, end='mail_menu', possibles=possibles, skip_first_screenshot=True)
    elif self.server == 'Global':
        click_pos = [[1141, 43]]
        pd_los = ["main_page"]
        end = ["mail"]
        color.common_rgb_detect_method(self, click_pos, pd_los, end, True)


def implement(self):
    self.quick_method_to_main_page()
    to_mail(self)
    img = self.latest_img_array
    if color.judge_rgb_range(img, 1142, 646, 206, 226, 207, 227, 208, 228):
        self.logger.info("mail reward HAS BEEN COLLECTED, quit")
        self.click(1236, 39)
    elif color.judge_rgb_range(img, 1142, 646, 235, 255, 233, 243, 65, 85):
        self.logger.info("COLLECT mail reward")
        time.sleep(0.5)
        self.click(1142, 670, duration=2, wait_over=True)
        self.click(1236, 39, wait_over=True)
        self.click(1236, 39, wait_over=True)
        self.click(1236, 39, wait_over=True)
    else:
        self.logger.info("Can't detect button")
        self.click(1236, 39)
        return False
    return True
