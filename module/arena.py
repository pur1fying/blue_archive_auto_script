import time

import cv2

from core import color, stage, image

x = {
    'menu': (107, 9, 162, 36),
    'edit-force': (107, 9, 162, 36),
    'battle-win': (571, 124, 702, 162),
    'battle-lost': (571, 191, 702, 229),
    'season-record': (682, 137, 746, 172),
    'best-record': (653, 139, 715, 172)
}


def implement(self):
    to_tactical_challenge(self)
    tickets = get_tickets(self.latest_img_array, self.ocrNUM, self.server)
    if tickets == 0:
        self.logger.info("INADEQUATE TICKETS COLLECT REWARD")
        collect_tactical_challenge_reward(self)
        return True
    else:
        self.logger.info("TICKETS: " + str(tickets))
        # choose_enemy(self)
        choice = 1
        x = 844
        y = [261, 414, 581]
        y = y[choice - 1]
        click_pos = [
            [x, y],
            [637, 590],
        ]
        los = [
            "tactical_challenge",
            "battle_opponent",
        ]
        ends = [
            "attack_team_formation",
        ]
        image.detect(self, 'arena_edit-force', {}, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, ends))
        res = check_skip_button(self.latest_img_array, self.server)
        if res == "OFF":
            self.logger.info("TURN ON SKIP")
            self.click(1108, 608, wait=False)
        elif res == "ON":
            self.logger.info("SKIP ON")
        else:
            self.logger.info("Can't find SKIP BUTTON")
            return False
        fight(self)
        to_tactical_challenge(self)
        if tickets > 1:
            self.next_time = 50
        elif tickets == 1:
            collect_tactical_challenge_reward(self)


def choose_enemy(self):
    less_level = 2
    self_lv = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[215:250, 165:208])['text'])
    self.logger.info("self level " + str(self_lv))
    refresh = 0
    while True:
        if refresh > 10:
            break
        opponent_lv = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[298:317, 551:581])['text'])
        self.logger.info("opponent level " + str(opponent_lv))
        if opponent_lv + less_level <= self_lv:
            break
        self.click(1158, 145)
        time.sleep(1)
        refresh += 1
        self.latest_img_array = self.get_screenshot_array()


def collect_tactical_challenge_reward(self):
    reward_status = [False, False]
    for i in range(0, 3):
        if color.judge_rgb_range(self.latest_img_array, 353, 404, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT TIME REWARD")
            self.click(353, 404)
            time.sleep(2)
            self.click(670, 96)
            self.click(670, 96)
            to_tactical_challenge(self)
        self.latest_img_array = self.get_screenshot_array()
        if color.judge_rgb_range(self.latest_img_array, 353, 404, 206, 226, 206, 226, 204, 224):
            reward_status[0] = True
            break

    self.latest_img_array = self.get_screenshot_array()
    for i in range(0, 3):
        if color.judge_rgb_range(self.latest_img_array, 353, 487, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT DAILY REWARD")
            self.click(353, 487)
            time.sleep(2)
            self.click(670, 96)
            self.click(670, 96)
            to_tactical_challenge(self)
        self.latest_img_array = self.get_screenshot_array()
        if color.judge_rgb_range(self.latest_img_array, 353, 487, 206, 226, 206, 226, 204, 224):
            reward_status[1] = True
            break

    self.logger.info("REWARD STATUS: " + str(reward_status))
    return True


def to_tactical_challenge(self):
    if self.server == 'CN':
        possible = {
            'main_page_home-feature': (1195, 576),
            'main_page_bus': (1093, 524),
            'arena_battle-win': (640, 530),
            'arena_battle-lost': (640, 468),
            'arena_season-record': (640, 538),
            'arena_best-record': (640, 538),
        }
        end = 'arena_menu'
        click_pos = [
            [640, 100]
        ]
        los = [
            'reward_acquired'
        ]
        image.detect(self, end, possible, pre_func=color.detect_rgb_one_time, pre_argv=(self, click_pos, los, []))
    elif self.server == 'Global':
        click_pos = [
            [1198, 580],
            [1096, 519],
            [1013, 100],
            [640, 116],
            [637, 471],
            [637, 530],
            [637, 530],
        ]
        los = [
            "main_page",
            "campaign",
            "battle_opponent",
            "reward_acquired",
            "battle_result_lose",
            "battle_result_win",
            "best_season_record_reached",
        ]
        ends = [
            "tactical_challenge",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)


def get_tickets(img, ocr, server):
    if server == 'CN':
        img = img[477:498, 193:206]
    elif server == 'Global':
        img = img[477:498, 209:227]
    ocr_res = ocr.ocr_for_single_line(img)
    print(ocr_res)
    if ocr_res["text"] == "-":
        return 0
    return int(ocr_res["text"])


def check_skip_button(img, server):
    if server == 'CN':
        temp = 1121
    elif server == 'Global':
        temp = 1108
    if color.judge_rgb_range(img, temp, 608, 74, 94, 222, 242, 235, 255):
        return "ON"
    if color.judge_rgb_range(img, temp, 608, 102, 122, 146, 166, 178, 198):
        return "OFF"
    return "NOT FOUND"


def fight(self):
    if self.server == 'CN':
        possibles = {
            'arena_edit-force': (1168, 669)
        }
        ends = [
            'arena_battle-win',
            'arena_battle-lost'
        ]
        image.detect(self, ends, possibles)
    elif self.server == 'Global':
        click_pos = [
            [1166, 675],
            [640, 546],
        ]
        los = [
            "attack_team_formation",
            "best_season_record_reached",
        ]
        ends = [
            "battle_result_lose",
            "battle_result_win",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)
