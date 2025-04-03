from core import color, picture


def implement(self):
    self.to_main_page()
    to_tactical_challenge(self, True)
    tickets = get_tickets(self)
    if tickets == 0:
        self.logger.info("Inadequate Arena Ticket Collect Reward")
        collect_tactical_challenge_reward(self)
        return True
    else:
        self.logger.info("Ticket: " + str(tickets))
        choice = self.config.ArenaComponentNumber
        choose_enemy(self, choice)
        x = 844
        y = [261, 414, 581]
        y = y[choice - 1]
        img_possibles = {
            "arena_menu": (x, y),
            "arena_opponent-info": (637, 590),
        }
        img_ends = ['arena_edit-force', 'arena_purchase-tactical-challenge-ticket']
        res = picture.co_detect(self, None, None, img_ends, img_possibles, True)
        if res == 'arena_purchase-tactical-challenge-ticket':   # no ticket, collect and quit
            self.logger.warning("No Arena Ticket")
            to_tactical_challenge(self, True)
            collect_tactical_challenge_reward(self)
            return True
        check_skip_button(self)   # make sure skip is on
        fight(self, True)
        to_tactical_challenge(self, True)
        if tickets > 1:
            self.next_time = 55
            return True
        elif tickets == 1:
            collect_tactical_challenge_reward(self)
            return True


def choose_enemy(self, choice=1):
    less_level = self.config.ArenaLevelDiff
    max_refresh = self.config.maxArenaRefreshTimes
    self.logger.info("Less Level Acceptable: " + str(less_level))
    self.logger.info("Max Refresh Times    : " + str(max_refresh))
    self_level_region = {
        'CN': (213, 190, 247, 213),
        'Global': (196, 192, 224, 213),
        'JP': (196, 192, 224, 213),
    }
    opponent_level_region = {
        'CN': [(509, 291, 535, 314), (509, 449, 535, 476), (509, 610, 535, 630)],
        'Global': [(490, 294, 515, 313), (490, 453, 515, 477), (490, 611, 515, 633)],
        'JP': [(496, 291, 520, 315), (496, 449, 520, 476), (496, 611, 520, 633)],
    }
    opponent_level_region = opponent_level_region[self.server][choice - 1]
    self_lv = self.ocr.recognize_int(self, self_level_region[self.server], "Self Level")
    refresh = 0
    while self.flag_run:
        if refresh >= max_refresh:
            break
        opponent_lv = self.ocr.recognize_int(self, opponent_level_region, "Opponent Level")
        if opponent_lv + less_level <= self_lv:
            break
        self.logger.info("Refresh Total Times : " + str(refresh + 1))
        self.click(1158, 145, wait_over=True, duration=1)
        self.update_screenshot_array()
        refresh += 1


def collect_tactical_challenge_reward(self):
    reward_status = [False, False]
    for i in range(0, 3):
        if color.rgb_in_range(self, 353, 404, 206, 226, 206, 226, 204, 224):
            reward_status[0] = True
            break
        if color.rgb_in_range(self, 353, 404, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT TIME REWARD")
            self.click(353, 404, wait_over=True, duration=1)
            self.click(670, 96, wait_over=True)
            self.click(670, 96, wait_over=True)
            to_tactical_challenge(self)
        else:
            self.update_screenshot_array()

    for i in range(0, 3):
        if color.rgb_in_range(self, 353, 487, 206, 226, 206, 226, 204, 224):
            reward_status[1] = True
            break
        if color.rgb_in_range(self, 353, 487, 235, 255, 222, 242, 52, 92):
            self.logger.info("COLLECT DAILY REWARD")
            self.click(353, 487, wait_over=True, duration=1)
            self.click(670, 96, wait_over=True)
            self.click(670, 96, wait_over=True)
            to_tactical_challenge(self)
        else:
            self.update_screenshot_array()
    self.logger.info("REWARD STATUS: " + str(reward_status))
    return True


def to_tactical_challenge(self, skip_first_screenshot=False):
    rgb_possibles = {
        'reward_acquired': (640, 96),
        'main_page': (1195, 576),
    }
    img_ends = 'arena_menu'
    arena_location = {
        'CN': (1093, 576),
        'Global': (877, 599),
        'JP': (877, 599),
    }
    img_possibles = {
        'main_page_bus': arena_location[self.server],
        'arena_battle-win': (640, 530),
        'arena_battle-lost': (640, 468),
        'arena_season-record': (640, 538),
        'arena_best-record': (640, 538),
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (910, 138),
        'normal_task_unlock-notice': (887, 164),
        'arena_purchase-tactical-challenge-ticket': (883, 162)
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)


def get_tickets(self):
    ticket_num_region = {
        'CN': (190, 475, 231, 501),
        'Global_en-us': (212, 477, 248, 503),
        'Global_zh-tw': (165, 479, 194, 504),
        'Global_ko-kr': (157, 477, 197, 503),
        'JP': (203, 478, 241, 502),
    }
    ocr_res = self.ocr.get_region_res(
        self,
        ticket_num_region[self.identifier],
        "en-us",
        "Arena Ticket Number",
        "0123456789/"
    )
    if '/' in ocr_res:
        ocr_res = ocr_res.split('/')[0]
    try:
        return int(ocr_res)
    except ValueError:
        self.logger.warning("Failed to get Arena Ticket Number")
        return 999


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


def check_skip_button(self):
    self.logger.info("Check Arena Skip Button.")
    rgb_ends = "arena_skip_on"
    rgb_possibles = {
        'arena_skip_off': (1225, 608)
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, None, None, True)
