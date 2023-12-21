from core import color, image
from datetime import datetime

x = {
    'menu': (107, 9, 162, 36),
    'sign-up-reward': (610, 141, 673, 176)
}


def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    next_time = datetime(year, month, day+1, 4)
    return next_time.timestamp()


def implement(self):
    if self.server == 'CN':
        possible = {
            'main_page_home-feature': (578, 648),
        }
        end = [
            'group_sign-up-reward',
            'group_menu',
        ]
        res = image.detect(self, end, possible)
        if res == 'group_sign-up-reward':
            self.logger.info('get 10 AP')
    elif self.server == "Global":
        res = to_club(self)
        if res == "club_attendance_reward":
            self.logger.info("get 10 AP")
        self.click(1236, 39, wait=False, count=2)
        return True
    return True


def to_club(self):
    click_pos = [
        [562, 656]
    ]
    los = [
        "main_page"
    ]
    ends = [
        "club",
        "club_attendance_reward"
    ]
    return color.common_rgb_detect_method(self, click_pos, los, ends)
