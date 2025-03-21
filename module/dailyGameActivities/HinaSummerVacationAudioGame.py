import time

from core import picture
from core.color import rgb_in_range
from core.device.screenshot.nemu import NemuScreenshot
from module.activities.PresidentHinasSummerVacation import to_activity

midy = 302


def implement(self):
    self.to_main_page()
    to_activity(self, "story")
    tasks = ["Normal", "Hard", "VeryHard", "Special"]
    for task in tasks:
        to_game(self, task)
        start_play(self, task)
        game_end_to_game_menu(self)
    return True


def blue_judge(self, x):
    if rgb_in_range(self, x, midy, 47, 67, 186, 206, 186, 206):
        return True
    return False


def yellow_judge(self, x):
    if rgb_in_range(self, x, midy, 210, 230, 170, 210, 0, 20):
        return True
    return False


def to_game(self, difficulty):
    img_ends = "activity_game-" + difficulty + "-chosen"
    img_possibles = dict()
    if difficulty in ["Normal", "Hard", "VeryHard"]:
        diff_list = ["Normal", "Hard", "VeryHard"]
        click__pos = {
            "Normal": (869, 244),
            "Hard": (1014, 244),
            "VeryHard": (1154, 244)
        }
        click__pos = click__pos[difficulty]
        for i in range(3):
            if diff_list[i] != difficulty:
                img_possibles["activity_game-" + diff_list[i] + "-chosen"] = click__pos
        img_possibles["activity_game-Special-chosen"] = (1258, 388)
    else:
        img_possibles = {
            "activity_game-Normal-chosen": (1258, 388),
            "activity_game-Hard-chosen": (1258, 388),
            "activity_game-VeryHard-chosen": (1258, 388),
        }
    img_possibles["activity_menu"] = (125, 187)
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def start_play(self, difficulty):
    screenshot = NemuScreenshot(self)
    self.click(1119, 663, wait_over=True)
    if difficulty == "Normal" or difficulty == "Hard" or difficulty == "VeryHard":
        t_total = 150
    elif difficulty == "Special":
        t_total = 135
    t_start = time.time()
    while time.time() - t_start < t_total:
        self.latest_img_array = screenshot.screenshot()
        i = 371
        first = False
        while 350 <= i <= 450:  # 首次点击
            if blue_judge(self, i):
                self.click(64, 377, wait_over=True)
                i = i + 100
                first = True
                break
            elif yellow_judge(self, i):
                self.click(1215, 377, wait_over=True)
                i = i + 100
                first = True
                break
            i = i + 2
        dealt_i = 0
        if first:  # 连续点击
            while 450 < i + dealt_i <= 1280 and dealt_i <= 100:
                if blue_judge(self, i + dealt_i):
                    if difficulty == "VeryHard":
                        time.sleep(0.08)
                    self.click(64, 377, wait_over=True)
                    i = i + dealt_i + 100
                    dealt_i = 0
                elif yellow_judge(self, i + dealt_i):
                    if difficulty == "VeryHard":
                        time.sleep(0.08)
                    self.click(1215, 377, wait_over=True)
                    i = i + dealt_i + 100
                    dealt_i = 0
                dealt_i += 2


def game_end_to_game_menu(self):
    img_possibles = {
        "activity_game-success-confirm": (1137, 659)
    }
    img_ends = "activity_game-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
