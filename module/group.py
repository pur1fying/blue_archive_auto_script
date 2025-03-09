from core import picture


def implement(self):
    self.to_main_page()
    res = to_group(self)
    if res == 'group_sign-up-reward':
        self.logger.info('GET 10 AP')
    elif res == 'group_join-club':
        self.logger.warning('NOT in a club')
    return True


def to_group(self):
    group_x = {
        'CN': 578,
        'Global': 578,
        'JP': 565,
    }
    rgb_possible = {'main_page': (group_x[self.server], 648)}
    img_possible = {'group_enter-button': (297, 380)}
    img_ends = [
        'group_sign-up-reward',
        'group_menu',
        'group_join-club'
    ]
    img_possible.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    return picture.co_detect(self, None, rgb_possible, img_ends, img_possible, True)
