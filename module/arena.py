from core import color, picture


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
        img_possibles = {
            "arena_menu": (x, y),
            "arena_opponent-info": (637, 590),
        }
        img_ends = ['arena_edit-force', 'arena_purchase-tactical-challenge-ticket']
        res = picture.co_detect(self, None, None, img_ends, img_possibles, True)
        if res == 'arena_purchase-tactical-challenge-ticket':
            self.logger.warning("no tickets")
            return True
        turn_on_arena_skip(self)
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
    self.logger.info("less level acceptable: " + str(less_level))
    self.logger.info("max refresh times: " + str(max_refresh))
    self_level_region = {
        'CN': (165, 215, 208, 250),
        'Global': (196, 192, 224, 213),
        'JP': (196, 192, 224, 213),
    }
    opponent_level_region = {
        'CN': (551, 298, 581, 317),
        'Global': (490, 298, 515, 317),
        'JP': (496, 291, 520, 315),
    }
    self_lv = self.ocr.get_region_num(self.latest_img_array, self_level_region[self.server], int, self.ratio)
    self.logger.info("self level " + str(self_lv))
    refresh = 0
    while self.flag_run:
        if refresh >= max_refresh:
            break
        opponent_lv = self.ocr.get_region_num(self.latest_img_array, opponent_level_region[self.server], int, self.ratio)
        if opponent_lv == "UNKNOWN":
            continue
        self.logger.info("opponent level " + str(opponent_lv))
        if opponent_lv + less_level <= self_lv:
            break
        self.logger.info("refresh total times : " + str(refresh + 1))
        self.click(1158, 145, wait_over=True, duration=1)
        color.wait_loading(self)
        refresh += 1


def collect_tactical_challenge_reward(self):
    reward_status = [False, False]
    for i in range(0, 3):
        if color.judge_rgb_range(self, 353, 404, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT TIME REWARD")
            self.click(353, 404, wait_over=True, duration=1)
            self.click(670, 96, wait_over=True)
            self.click(670, 96, wait_over=True)
            to_tactical_challenge(self)
        if color.judge_rgb_range(self, 353, 404, 206, 226, 206, 226, 204, 224):
            reward_status[0] = True
            break

    for i in range(0, 3):
        if color.judge_rgb_range(self, 353, 487, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT DAILY REWARD")
            self.click(353, 487, wait_over=True, duration=1)
            self.click(670, 96, wait_over=True)
            self.click(670, 96, wait_over=True)
            to_tactical_challenge(self)
        if color.judge_rgb_range(self, 353, 487, 206, 226, 206, 226, 204, 224):
            reward_status[1] = True
            break

    self.logger.info("REWARD STATUS: " + str(reward_status))
    return True


def to_tactical_challenge(self, skip_first_screenshot=False):
    rgb_possibles = {
        'reward_acquired': (640, 96),
        'main_page': (1195, 576),
    }
    img_ends = 'arena_menu'
    arena_location = {
        'CN': (1093, 524),
        'Global': (1093, 524),
        'JP': (877, 599),
    }
    img_possibles = {
        'main_page_bus': arena_location[self.server],
        'arena_battle-win': (640, 530),
        'arena_battle-lost': (640, 468),
        'arena_season-record': (640, 538),
        'arena_best-record': (640, 538),
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (910, 138)
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)


def get_tickets(self):
    ticket_num_region = {
        'CN': (193, 477, 206, 498),
        'Global': (209, 477, 227, 498),
        'JP': (196, 477, 218, 498),
    }
    ocr_res = self.ocr.get_region_num(self.latest_img_array, ticket_num_region[self.server], int, self.ratio)
    return ocr_res


def check_skip_button(self):
    skip_x = {
        'CN': 1121,
        'Global': 1108,
        'JP': 1108,
    }
    if color.judge_rgb_range(self, skip_x[self.server], 608, 74, 94, 222, 242, 235, 255):
        return "ON"
    if color.judge_rgb_range(self, skip_x[self.server], 608, 102, 122, 146, 166, 178, 198):
        return "OFF"
    return "NOT FOUND"


def fight(self, skip_first_screenshot=False):
    img_possibles = {
        'arena_edit-force': (1168, 669),
        'arena_best-record': (640, 546),
        'arena_season-record': (640, 546),
    }
    img_ends = [
        'arena_battle-win',
        'arena_battle-lost'
    ]
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def turn_on_arena_skip(self):
    res = check_skip_button(self)
    if res == "OFF":
        self.logger.info("TURN ON SKIP")
        self.click(1225, 608, wait_over=True, duration=0.3)
    elif res == "ON":
        self.logger.info("SKIP ON")
        return
    else:
        self.logger.info("Can't find SKIP BUTTON")
    self.latest_img_array = self.get_screenshot_array()
    return turn_on_arena_skip(self)
