from core import picture
from core.picture import GAME_ONE_TIME_POP_UPS


def implement(self):
    if self.server in ["CN"]:
        self.logger.info("Collect Daily Free Power is only available in JP and Global server.")
        return True
    self.to_main_page()
    to_purchase_pyroxenes_menu(self)
    to_purchase_type(self, "package")
    if detect_free_power_availability(self):
        collect_daily_free_power(self)
    else:
        self.logger.info("Daily Free Power Already Collected.")

    return_to_main_page(self)
    return True

def collect_daily_free_power(self):
    self.logger.info("Collect Daily Free Power.")

    img_possibles = {
        "main_page_purchase-pyroxenes-menu": (385, 479),
        "main_page_purchase-pyroxenes-confirm-purchase-notice": (749, 571),
    }
    img_ends = "main_page_full-notice"
    rgb_ends = "reward_acquired"
    picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, skip_first_screenshot=True)
    self.logger.info("Get 10 AP")

def return_to_main_page(self):
    img_possibles = {
        "main_page_purchase-pyroxenes-menu": (1011, 114),
        "main_page_full-notice": (887, 165)
    }
    rgb_possibles = {
        "reward_acquired": (640, 180)
    }
    rgb_ends = "main_page"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot=True)

def to_purchase_pyroxenes_menu(self):
    img_possibles = GAME_ONE_TIME_POP_UPS[self.server]
    rgb_possibles = {
        "main_page": (982, 28)
    }
    img_ends = "main_page_purchase-pyroxenes-menu"

    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)

def to_purchase_type(self, tp):
    # position when " limited " exist
    p_1 = {
        "limited": (488, 186),
        "pyroxenes": (750, 186),
        "package": (1000, 186)
    }
    p_1 = p_1[tp]
    # position when " limited " not exist
    p_2 = {
        "pyroxenes": (590, 186),
        "package": (996, 186)
    }
    p_2 = p_2[tp]
    img_ends = {
        "limited": [
            "main_page_purchase-pyroxenes-limited-selected"
        ],
        "pyroxenes": [
            "main_page_purchase-pyroxenes-pyroxenes-selected-1",
            "main_page_purchase-pyroxenes-pyroxenes-selected-2"
        ],
        "package": [
            "main_page_purchase-pyroxenes-package-selected-1",
            "main_page_purchase-pyroxenes-package-selected-2"
        ]
    }
    img_ends = img_ends[tp]
    img_possibles = {
        "main_page_purchase-pyroxenes-limited-selected": p_1,
        "main_page_purchase-pyroxenes-pyroxenes-selected-1": p_1,
        "main_page_purchase-pyroxenes-package-selected-1":p_1,
        "main_page_purchase-pyroxenes-pyroxenes-selected-2": p_2,
        "main_page_purchase-pyroxenes-package-selected-2": p_2
    }
    for img_end in img_ends:
        img_possibles.pop(img_end, None)
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)

def detect_free_power_availability(self):
    img_ends = [
        "main_page_purchase-pyroxenes-daily-free-purchasable",
        "main_page_purchase-pyroxenes-daily-free-non-purchasable",
    ]
    ret = picture.co_detect(self, None, None, img_ends, None, skip_first_screenshot=True)
    if ret == "main_page_purchase-pyroxenes-daily-free-purchasable":
        return True
    return False
