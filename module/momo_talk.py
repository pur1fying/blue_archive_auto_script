import time
from core import color, image, picture


def implement(self, need_check_mode=True):
    self.to_main_page()
    to_momotalk(self, True, 2)
    if need_check_mode:
        check_mode(self)
    main_to_momotalk = True
    first_try = True
    unread_location = []
    length = 0

    while 1:
        if need_check_mode and first_try:
            first_try = False
            for _ in range(3):  # try three times in the first time
                self.update_screenshot_array()
                unread_location = get_unread_location(self)
                length = len(unread_location)
                if length > 0:
                    break
                if _ != 2:
                    self.logger.info("No Unread Message Found, Detect Again.")
        else:
            color.wait_loading(self)
            unread_location = get_unread_location(self)
            length = len(unread_location)
        if length == 0:
            if main_to_momotalk:
                self.logger.info("momo_talk task Finished")
                return True
            else:
                self.logger.info("Restart momo_talk task")
                self.to_main_page()
                return implement(self, need_check_mode=False)
        else:
            for i in range(0, len(unread_location)):
                self.click(unread_location[i][0], unread_location[i][1], wait_over=True)
                common_solve_affection_story_method(self)
        main_to_momotalk = False
        to_momotalk(self, True, 1)
        to_momotalk(self, True, 2)


def check_mode(self):
    change_sort(self, "unread")
    change_direction(self, "down")


def change_sort(self, sort="unread"):
    self.logger.info(f"Change Sort to [{sort}]")
    all_sort_p = {
        "newest": (339, 296),
        "unread": (555, 296),
        "name": (339, 353),
        "affection": (555, 353),
        "starred": (339, 407)
    }
    p = all_sort_p[sort]
    keys = list(all_sort_p.keys())
    # to sort menu
    img_reactions = {
        "momo_talk_momotalk-peach": (511, 177),
    }
    img_ends = "momo_talk_sort-menu"
    picture.co_detect(self, None, None, img_ends, img_reactions, skip_first_screenshot=True)
    # change sort
    keys.remove(sort)
    img_reactions = {f"momo_talk_sort-{key}-chosen": p for key in keys}
    img_ends = f"momo_talk_sort-{sort}-chosen"
    picture.co_detect(self, None, None, img_ends, img_reactions, skip_first_screenshot=True)
    # confirm
    confirm_y = {
        "CN": 426,
        "Global": 475,
        "JP": 475
    }
    confirm_y = confirm_y[self.server]
    image.click_until_template_disappear(
        self,
        "momo_talk_sort-menu",
        461, confirm_y,
        0.8,
        20,
        True
    )


def change_direction(self, direction="down"):
    self.logger.info(f"Change Direction to [{direction}]")
    opposite = {
        "down": "up",
        "up": "down"
    }
    img_reactions = {
        f"momo_talk_{opposite[direction]}": (634, 169),
    }
    img_ends = f"momo_talk_{direction}"
    picture.co_detect(self, None, None, img_ends, img_reactions, skip_first_screenshot=True)


def to_momotalk(self, skip_first_screenshot=False, target=2):
    opposite = 3 - target
    momotalk_p = [(), (168, 280), (168, 202)]
    rgb_possibles = {
        "main_page": (166, 150),
        f"momotalk{opposite}": momotalk_p[opposite],
        "reward_acquired": (640, 100),
    }
    rgb_ends = f"momotalk{target}"
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
    while time.time() <= start_time + timeOut:  # when 10s no reply , conclude this conversation
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
            to_momotalk(self, False, 2)
            return True
    self.logger.info(str(timeOut) + "s Time Out Reached And Assume Current Conversation Over")


def getConversationState(self):
    self.update_screenshot_array()
    if image.compare_image(self, "plot_menu"):  # menu --> skip plot --> skip notice --> reward acquired
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
    return ['end']  # nothing found


def get_unread_location(self):
    y = 210
    dy = 18
    unread_location = []
    while y <= 620:
        if color.rgb_in_range(self, 637, y, 241, 255, 61, 81, 15, 35):
            unread_location.append([637, int(y + dy / 2)])
            y += 60
        else:
            y += 1
    self.logger.info("Find  " + str(len(unread_location)) + "  Unread Message")
    return unread_location
