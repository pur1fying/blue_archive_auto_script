import time

from core import color, stage, image

x = {
    'menu': (107, 9, 162, 36),
    'edit-force': (107, 9, 162, 36),
    'id': (476, 424, 496, 442),
    'cd': (153, 516, 212, 535),
    '0-5': (194, 479, 227, 497),
    'skip': (1109, 591, 1135, 614),
    'attack': (1140, 654, 1197, 681)
}
finish_seconds = 55


def to_arena(self):
    possible = {
        'home_home-feature': (1195, 576, 3),
        'home_bus': (1093, 524, 3),
    }
    end = ('arena_menu', 3)
    image.detect(self, end, possible, pre_argv=home.go_home(self))


def implement(self):
    if self.server == "CN":
        to_arena(self)

        # 开始战斗
        start_fight(self)

    elif self.server == "Global":
        self.go_home()
        global_implement(self)
    self.go_home()


def get_prize(self):
    if color.check_rgb_similar(self, (320, 400, 321, 401)):
        # 领取时间奖励
        self.click(353, 385)
        # 关闭奖励
        stage.close_prize_info(self)
    if color.check_rgb_similar(self, (330, 480, 331, 481)):
        # 领取挑战奖励
        self.click(348, 465)
        # 关闭奖励
        stage.close_prize_info(self)


def start_fight(self, wait=False):
    # 检查余票
    time.sleep(0.5)
    if image.compare_image(self, 'arena_0-5', 0):
        self.logger.info("没票了")
        get_prize(self)
        return True
    # 检测已有冷却
    if wait or not image.compare_image(self, 'arena_cd', 0):
        self.finish_seconds = finish_seconds
        return False
    # 选择对手
    choose_enemy(self)
    # 编队
    self.click(640, 570, True, 1, 0.5)
    # 等待出击加载
    image.compare_image(self, 'arena_edit-force', 999, 20, False, self.click, (1125, 599, False), 0.5)

    # 检查跳过是否勾选
    image.compare_image(self, 'arena_skip', 999, 20, False, self.click, (1125, 599, False), 0.5)

    # 出击
    image.compare_image(self, 'arena_edit-force', threshold=10, mis_fu=self.click, mis_argv=(1163, 658), rate=1, n=True)
    while True:
        # 检查有没有出现ID
        if image.compare_image(self, 'arena_id', 0):
            break
        # 关闭弹窗
        self.click(1235, 82, False)
        time.sleep(self.bc['baas']['base']['ss_rate'])
    start_fight(self, True)


def choose_enemy(self):
    less_level = int(self.tc['config']['less_level'])
    # 识别自己等级
    my_lv = float(ocr.screenshot_get_text(self, (165, 215, 208, 250), self.ocrNum))
    refresh = 0
    while True:
        # 超出最大次数,敌人预期等级-1
        if refresh > self.tc['config']['max_refresh']:
            less_level -= 1
            refresh = 0
            continue
        # 识别对手等级
        enemy_lv = float(ocr.screenshot_get_text(self, (551, 298, 581, 317), self.ocrNum))
        self.logger.info("对手等级 {0}".format(enemy_lv))
        if enemy_lv + less_level <= my_lv:
            break
        # 更换对手
        self.double_click(1158, 145)
        refresh += 1
    # 选择对手
    self.click(769, 251)


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


def get_tickets(img, ocr):
    img = img[477:498, 209:227]
    ocr_res = ocr.ocr_for_single_line(img)
    print(ocr_res)
    if ocr_res["text"] == "-":
        return 0
    return int(ocr_res["text"])


def check_skip_button(img):
    if color.judge_rgb_range(img, 1108, 608, 74, 94, 222, 242, 235, 255):
        return "ON"
    if color.judge_rgb_range(img, 1108, 608, 102, 122, 146, 166, 178, 198):
        return "OFF"
    return "NOT FOUND"


def fight(self):
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


def global_implement(self):
    to_tactical_challenge(self)
    tickets = get_tickets(self.latest_img_array, self.ocr)
    if tickets == 0:
        self.logger.info("INADEQUATE TICKETS COLLECT REWARD")
        collect_tactical_challenge_reward(self)
        return True
    else:
        self.logger.info("TICKETS: " + str(tickets))
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
        color.common_rgb_detect_method(self, click_pos, los, ends)
        if check_skip_button(self.latest_img_array) == "OFF":
            self.logger.info("TURN ON SKIP")
            self.click(1108, 608, wait=False)
        elif check_skip_button(self.latest_img_array) == "ON":
            self.logger.info("SKIP ON")
        else:
            self.logger.info("Can't find SKIP BUTTON")
            return False
        fight(self)
        to_tactical_challenge(self)
        if tickets > 1:
            self.finish_seconds = finish_seconds
        elif tickets == 1:
            collect_tactical_challenge_reward(self)
