from core import picture


def implement(self):
    self.quick_method_to_main_page()
    rgb_possible = {'main_page': (578, 648)}
    img_possible = {'main_page_home-feature': (578, 648)}
    img_ends = [
        'group_sign-up-reward',
        'group_menu',
        'group_join-club'
    ]
    res = picture.co_detect(self, None, rgb_possible, img_ends, img_possible, True)
    if res == 'group_sign-up-reward':
        self.logger.info('GET 10 AP')
    elif res == 'group_join-club':
        self.logger.warning('NOT in a club')
    return True
