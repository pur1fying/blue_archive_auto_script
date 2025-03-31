import time
from module.mini_story import check_6_region_status
from core import color, picture, image


def implement(self):
    self.to_main_page()
    to_group_story(self, True)
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()
    while self.flag_run:
        need_check_next_page = judge_need_check_next_page(self)
        region_status = check_6_region_status(self)
        for i in range(0, len(region_status)):
            if region_status[i]:
                to_region(self, i + 1)
                while (not check_current_episode_cleared(self)) and self.flag_run:
                    res = one_detect(self)
                    while not res:
                        self.update_screenshot_array()
                        res = one_detect(self)
                        continue
                    to_episode_info(self, res, True)
                    clear_current_plot(self, True)
                to_group_story(self, True)
        if not need_check_next_page:
            self.logger.info("-- ALL EPISODES CLEARED --")
            return True
        else:
            self.logger.info("Check Next page")
            self.click(1255, 357, duration=1.5, wait_over=True)
            self.latest_img_array = self.get_screenshot_array()


def to_group_story(self, skip_first_screenshot=False):
    rgb_possibles = {'main_page': (1196, 572)}
    img_ends = "group_story_menu"
    img_possibles = {
        "main_page_bus": (1091, 260),
        "group_story_enter-group-story": (1019, 266),
        "group_story_select-episode": (56, 40),
        'group_story_episode-info': (916, 162),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def judge_need_check_next_page(self):
    for i in range(1231, 1280):
        if color.rgb_in_range(self, i, 357, 60, 80, 89, 109, 142, 162):
            self.logger.info("Need check next page")
            return True
    self.logger.info("Last page")
    return False


def to_region(self, num, skip_first_screenshot=False):
    click_pos = [
        [352, 240], [931, 240],
        [352, 396], [931, 396],
        [352, 537], [931, 537]
    ]
    img_possibles = {
        "group_story_menu": (click_pos[num - 1][0], click_pos[num - 1][1]),
        "group_story_episode-info": (916, 162),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519)
    }
    img_ends = "group_story_select-episode"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_episode_info(self, pos, skip_first_screenshot=False):
    img_possibles = {"group_story_select-episode": (pos[0], pos[1])}
    img_ends = "group_story_episode-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def check_current_episode_cleared(self):
    if image.compare_image(self, "group_story_episode-cleared-feature") or image.compare_image(self,
                                                                                               "group_story_plot-not-open"):
        self.logger.info("Current episode cleared")
        return True
    self.logger.info("Current episode not cleared")
    return False


def one_detect(self):
    possibles = [[1073, 251], [1073, 351]]
    for i in range(0, len(possibles)):
        if color.rgb_in_range(self, possibles[i][0], possibles[i][1], 109, 129, 211, 231, 245, 255):
            return possibles[i]
    return False


def clear_current_plot(self, skip_first_screenshot=False):
    rgb_possibles = {
        'reward_acquired': (640, 100),
    }
    img_possibles = {
        "group_story_episode-info": (650, 511),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519),
    }
    img_ends = "group_story_select-episode"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
