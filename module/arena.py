import time

from core import color, image

x = {
    'menu': (107, 9, 162, 36),
    'edit-force': (107, 9, 162, 36),
    'battle-win': (571, 124, 702, 162),
    'battle-lost': (571, 191, 702, 229),
    'season-record': (682, 137, 746, 172),
    'best-record': (653, 139, 715, 172)
}


def implement(self):
    self.quick_method_to_main_page()
    to_tactical_challenge(self, True)
    tickets = get_tickets(self)
    if tickets == 0:
        self.logger.info("INADEQUATE TICKETS COLLECT REWARD")
        collect_tactical_challenge_reward(self)
        return True
    else:
        self.logger.info("TICKETS: " + str(tickets))
        choose_enemy(self)
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
        possibles = {
            "arena_menu": (x, y),
            "arena_opponent-info": (637, 590),
        }
        if self.server == 'CN' or self.server == 'JP':
            image.detect(self, 'arena_edit-force', possibles, pre_func=color.detect_rgb_one_time,
                         pre_argv=(self, click_pos, los, ends), skip_first_screenshot=True)
        elif self.server == 'Global':
            color.common_rgb_detect_method(self, click_pos, los, ends, True)
        res = check_skip_button(self.latest_img_array, self.server)
        if res == "OFF":
            self.logger.info("TURN ON SKIP")
            self.click(1108, 608, wait=False, wait_over=True)
        elif res == "ON":
            self.logger.info("SKIP ON")
        else:
            self.logger.info("Can't find SKIP BUTTON")
            return False
        fight(self, True)
        to_tactical_challenge(self, True)
        if tickets > 1:
            self.next_time = 55
            return True
        elif tickets == 1:
            collect_tactical_challenge_reward(self)
            return True


def choose_enemy(self):
    less_level = self.config['ArenaLevelDiff']
    max_refresh = self.config['maxArenaRefreshTimes']
    self.logger.info("less level acceptable:" + str(less_level))
    self.logger.info("max refresh times:" + str(max_refresh))
    self_level_region = {
        'CN': (165, 215, 208, 250),
        'Global': (165, 215, 208, 250),
        'JP': (196, 192, 224, 213),
    }
    opponent_level_region = {
        'CN': (551, 298, 581, 317),
        'Global': (551, 298, 581, 317),
        'JP': (496, 291, 520, 315),
    }
    self_lv = self.ocr.get_region_num(self.latest_img_array, self_level_region[self.server])
    self.logger.info("self level " + str(self_lv))
    refresh = 0
    while True:
        if refresh >= max_refresh:
            break
        opponent_lv = self.ocr.get_region_num(self.latest_img_array, opponent_level_region[self.server])
        if opponent_lv == "UNKNOWN":
            continue
        self.logger.info("opponent level " + str(opponent_lv))
        if opponent_lv + less_level <= self_lv:
            break
        self.logger.info("refresh")
        self.click(1158, 145, wait=False, wait_over=True)
        time.sleep(1)
        color.wait_loading(self)
        refresh += 1


def collect_tactical_challenge_reward(self):
    reward_status = [False, False]
    for i in range(0, 3):
        if color.judge_rgb_range(self.latest_img_array, 353, 404, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT TIME REWARD")
            self.click(353, 404, wait=False, wait_over=True)
            time.sleep(1.5)
            self.click(670, 96, wait=False, wait_over=True)
            self.click(670, 96, wait=False, wait_over=True)
            to_tactical_challenge(self)
        if color.judge_rgb_range(self.latest_img_array, 353, 404, 206, 226, 206, 226, 204, 224):
            reward_status[0] = True
            break

    for i in range(0, 3):
        if color.judge_rgb_range(self.latest_img_array, 353, 487, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT DAILY REWARD")
            self.click(353, 487, wait=False, wait_over=True)
            time.sleep(1.5)
            self.click(670, 96, wait=False, wait_over=True)
            self.click(670, 96, wait=False, wait_over=True)
            to_tactical_challenge(self)
        if color.judge_rgb_range(self.latest_img_array, 353, 487, 206, 226, 206, 226, 204, 224):
            reward_status[1] = True
            break

    self.logger.info("REWARD STATUS: " + str(reward_status))
    return True


def to_tactical_challenge(self, skip_first_screenshot=False):
    if self.server == 'CN' or self.server == 'JP':
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
        image.detect(self, end, possible, skip_first_screenshot=skip_first_screenshot,
                     pre_func=color.detect_rgb_one_time, pre_argv=(self, click_pos, los, []))
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
        color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot)


def get_tickets(self):
    ticket_num_region = {
        'CN': (193, 477, 206, 498),
        'Global': (209, 477, 227, 498),
        'JP': (196, 477, 218, 498),
    }
    ocr_res = self.ocr.get_region_num(self.latest_img_array, ticket_num_region[self.server])
    return ocr_res


def check_skip_button(img, server):
    skip_x = {
        'CN': 1121,
        'Global': 1108,
        'JP': 1108,
    }
    if color.judge_rgb_range(img, skip_x[server], 608, 74, 94, 222, 242, 235, 255):
        return "ON"
    if color.judge_rgb_range(img, skip_x[server], 608, 102, 122, 146, 166, 178, 198):
        return "OFF"
    return "NOT FOUND"


def fight(self, skip_first_screenshot=False):
    if self.server == 'CN' or self.server == 'JP':
        possibles = {
            'arena_edit-force': (1168, 669)
        }
        ends = [
            'arena_battle-win',
            'arena_battle-lost'
        ]
        image.detect(self, ends, possibles, skip_first_screenshot=skip_first_screenshot)
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
        color.common_rgb_detect_method(self, click_pos, los, ends, skip_first_screenshot)
