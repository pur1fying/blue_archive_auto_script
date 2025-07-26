from core.picture import co_detect, GAME_ONE_TIME_POP_UPS


def implement(self):
    if self.server != "JP":
        self.logger.info("Collect Pass Reward is only available in JP server.")
        return True
    self.to_main_page()
    main_page_to_pass_menu(self)
    to_page_pass_mission(self)
    collect_reward(self)
    to_page_pass_menu(self)
    collect_reward(self)
    return True


def collect_reward(self):
    img_possibles = {
        "pass_collect-reward-available": (1206, 643)
    }
    rgb_possibles = {
        "reward_acquired": (777, 491),
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
        "reward_acquired": (777, 491),
    }
    co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def to_page_pass_mission(self):
    img_possibles = {
        "pass_menu": (382, 649)
    }
    img_ends = "pass_mission-menu"
    co_detect(self, None, None, img_ends, img_possibles, True)
