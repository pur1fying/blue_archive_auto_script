import time

from core import color, image, picture


def implement(self, need_check_mode=True):
    self.to_main_page()
    to_momotalk2(self, True)
    if need_check_mode:
        check_mode(self)
        time.sleep(0.5)
        self.latest_img_array = self.get_screenshot_array()
    main_to_momotalk = True
    while 1:
        color.wait_loading(self)
        y = 210
        dy = 18
        unread_location = []
        while y <= 620:
            if color.rgb_in_range(self, 637, y, 241, 255, 61, 81, 15, 35):
                unread_location.append([637, int(y + dy / 2)])
                y += 60
            else:
                y += 1
        length = len(unread_location)
        self.logger.info("find  " + str(length) + "  unread message")
        if length == 0:
            if main_to_momotalk:
                self.logger.info("momo_talk task finished")
                return True
            else:
                self.logger.info("restart momo_talk task")
                self.to_main_page()
                return implement(self, need_check_mode=False)
        else:
            for i in range(0, len(unread_location)):
                self.click(unread_location[i][0], unread_location[i][1], wait_over=True)
                common_solve_affection_story_method(self)
        main_to_momotalk = False
        self.click(170, 197, duration=0.2, wait_over=True)
        self.click(170, 270, duration=0.2, wait_over=True)


def check_mode(self):
    if not image.compare_image(self, "momo_talk_unread"):
        y = {
            "CN": 426,
            "Global": 475,
            "JP": 475
        }
        y = y[self.server]
        self.logger.info("change NEWEST to UNREAD mode")
        self.click(514, 177, duration=0.3, wait_over=True)
        self.click(562, 297, duration=0.3, wait_over=True)
        self.click(461, y, duration=0.3, wait_over=True)
    else:
        self.logger.info("UNREAD mode")
    self.latest_img_array = self.get_screenshot_array()
    if image.compare_image(self, "momo_talk_up"):
        self.logger.info("change UP to DOWN")
        self.click(634, 169, duration=0.2, wait_over=True)
    elif image.compare_image(self, "momo_talk_down"):
        self.logger.info("DOWN mode")
    else:
        self.logger.info("can't detect up/down button")
    return True


def to_momotalk2(self, skip_first_screenshot=False):
    rgb_possibles = {
        "main_page": (166, 150),
        "momotalk1": (170, 278),
        "reward_acquired": (640, 100),
    }
    rgb_ends = "momotalk2"
    img_possibles = picture.GAME_ONE_TIME_POP_UPS[self.server]
    return picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles,
                             skip_first_screenshot=skip_first_screenshot)


def common_solve_affection_story_method(self):
    res = getConversationState(self)
    if res[0] == 'end':
        self.swipe(924, 330, 924, 230, duration=0.1)
        self.click(924, 330, wait_over=True)
    start_time = time.time()
    timeOut = 10
    while time.time() <= start_time + timeOut:       # when 10s no reply , conclude this conversation
        res = getConversationState(self)
        if res[0] == 'reply':
            if res[1] >= 625:
                self.logger.warning("Replay can‘t be clicked, swipe upward")
                self.swipe(924, 330, 924, 230, duration=0.1)
                self.click(924, 330, wait_over=True)
            else:
                self.logger.info("Reply")
                self.click(826, res[1])
            start_time = time.time()
        elif res[0] == 'affection':
            timeOut = 20
            self.logger.info("To Relationship Story")
            self.click(826, res[1], wait_over=True)
        elif res[0] == 'enter':
            self.logger.info("Begin Relationship Story")
            self.click(920, 556, wait_over=True)
        elif res[0] == 'plot_menu':
            self.logger.info("Find Menu Button")
            img_possibles = {
                'plot_menu': (1202, 37),
                'plot_skip-plot-button': (1208, 116),
                'plot_skip-plot-notice': (770, 519),
            }
            rgb_ends = "reward_acquired"
            picture.co_detect(self, rgb_ends, None, None, img_possibles, skip_first_screenshot=True)
            self.logger.info("Relationship Story Over")
            to_momotalk2(self, True)
            return True
        time.sleep(self.screenshot_interval)
    self.logger.info(str(timeOut) + "s Time Out Reached And Assume Current Conversation Over")


def getConversationState(self):
    self.latest_img_array = self.get_screenshot_array()
    if image.compare_image(self, "plot_menu"):      # menu --> skip plot --> skip notice --> reward acquired
        return ['plot_menu']
    if color.rgb_in_range(self, 817, 582, 110, 130, 210, 230, 245, 255) and \
        color.rgb_in_range(self, 761, 418, 35, 55, 66, 86, 104, 124) and \
        color.rgb_in_range(self, 1034, 582, 110, 130, 210, 230, 245, 255):  # blue enter
        return ['enter']
    i = 657
    while i > 156:
        if color.rgb_in_range(self, 786, i, 29, 49, 143, 163, 219, 239, True, 1) and \
            color.rgb_in_range(self, 786, i + 10, 29, 49, 143, 163, 219, 239, True, 1):  # reply
            return ['reply', i + 65]
        elif color.rgb_in_range(self, 862, 813 - i, 245, 255, 227, 247, 230, 250) and \
            color.rgb_in_range(self, 862, 823 - i, 245, 255, 125, 155, 145, 175):  # pink enter
            return ['affection', min(625, 843 - i)]
        else:
            i -= 1
    return ['end'] # nothing found




