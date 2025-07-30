import time

from core.picture import co_detect, GAME_ONE_TIME_POP_UPS


def implement(self):
    if self.server != "JP":
        self.logger.info("Collect Pass Reward is only available in JP server.")
        return True
    self.to_main_page()
    main_page_to_pass_menu(self)

    # collect point
    to_page_pass_mission(self)
    collect_reward(self)

    # collect reward
    to_page_pass_menu(self)
    collect_reward(self)

    detect_statistics(self)
    return True


def collect_reward(self):
    img_possibles = {
        "pass_collect-reward-available": (1206, 643),
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (908, 138)
    }
    rgb_possibles = {
        "reward_acquired": (640, 100),
    }
    img_ends = "pass_collect-reward-unavailable"
    co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def main_page_to_pass_menu(self):
    rgb_possibles = {
        "main_page": (394, 556)
    }
    img_ends =  "pass_menu"
    co_detect(self, None, rgb_possibles, img_ends, GAME_ONE_TIME_POP_UPS[self.server], True)


def to_page_pass_menu(self):
    img_possibles = {
        "pass_mission-menu": (33, 48)
    }
    img_ends = "pass_menu"
    rgb_possibles = {
        "reward_acquired": (640, 100),
    }
    co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def to_page_pass_mission(self):
    img_possibles = {
        "pass_menu": (382, 649)
    }
    img_ends = "pass_mission-menu"
    co_detect(self, None, None, img_ends, img_possibles, True)


def detect_statistics(self):
    self.logger.info("Detect Pass Statistics")
    data = {
        "level": -1,
        "max_level": 60,
        "next_level_point": -1,
        "next_level_point_required": -1,
        "weekly_point": -1,
        "max_weekly_point": -1,
        "time": time.time()
    }
    detect_pass_level(self, data)
    detect_pass_next_level_point(self, data)
    detect_pass_weekly_point(self, data)
    self.config_set.set("_pass", data)

def detect_pass_level(self, d):
    region = {
        "JP": (67, 428, 135, 476)
    }
    ret = self.ocr.recognize_int(
        baas=self,
        region=region[self.server],
        log_info="Pass Current Level"
    )
    d["level"] = ret


def detect_pass_next_level_point(self, d):
    region = {
        "JP": (53, 496, 187, 522)
    }
    ocr_res = self.ocr.get_region_res(
        self,
        region[self.server],
        "en-us",
        "Pass Next Level Point",
        "0123456789/"
    )
    _max = -1
    if '/' in ocr_res:
        ocr_res = ocr_res.split('/')
        _max = ocr_res[1]
        ocr_res = ocr_res[0]
    try:
        ocr_res = int(ocr_res)
        _max = int(_max)
        self.logger.info(f"Current :{ocr_res}")
        self.logger.info(f"Required:{_max}")
        d["next_level_point"] = ocr_res
        d["next_level_point_required"] = _max
    except ValueError:
        self.logger.warning("Failed to detect Pass Next Level Point.")


def detect_pass_weekly_point(self, d):
    region = {
        "JP": (53, 560, 187, 589)
    }
    ocr_res = self.ocr.get_region_res(
        self,
        region[self.server],
        "en-us",
        "Pass Weekly Point",
        "0123456789/"
    )
    _max = -1
    if '/' in ocr_res:
        ocr_res = ocr_res.split('/')
        _max = ocr_res[1]
        ocr_res = ocr_res[0]
    try:
        ocr_res = int(ocr_res)
        _max = int(_max)
        self.logger.info(f"Current :{ocr_res}")
        self.logger.info(f"Max     :{_max}")
        d["weekly_point"] = ocr_res
        d["max_weekly_point"] = _max
    except ValueError:
        self.logger.warning("Failed to detect Pass Weekly Point.")


