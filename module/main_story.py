import importlib
import os
import time
from core import color, picture, image
from module.explore_normal_task import start_action, to_formation_edit_i, start_mission, \
    to_normal_task_wait_to_begin_page, check_skip_fight_and_auto_over


def implement(self):
    self.logger.info("START pushing main story")
    stage_module = importlib.import_module("src.explore_task_data.main_story.main_story")
    self.main_story_stage_data = getattr(stage_module, "stage_data")
    self.quick_method_to_main_page()
    to_main_story(self, True)
    push_episode_list = process_regions(self, self.config['main_story_regions'])
    if not push_episode_list:
        default_list = {
            'CN': [1, 2, 3, 4],
            'Global': [1, 2, 3, 4, 5, 4],
            'JP': [1, 2, 3, 4, 5, 4, 6]
        }
        push_episode_list = default_list[self.server]
    for i in range(0, len(push_episode_list)):
        current_episode = push_episode_list[i]
        is_final = False
        if current_episode == 5:
            is_final = True
        push_episode(self, current_episode, is_final)
    return True


def judge_acc(self):
    if color.judge_rgb_range(self, 1180, 621, 200, 255, 200, 255, 200, 255) and \
        color.judge_rgb_range(self, 1250, 621, 200, 255, 200, 255, 200, 255):
        return 1
    elif color.judge_rgb_range(self, 1250, 621, 100, 150, 200, 255, 200, 255) and \
        color.judge_rgb_range(self, 1180, 621, 100, 155, 200, 255, 200, 255):
        return 2
    elif color.judge_rgb_range(self, 1250, 621, 210, 255, 180, 240, 0, 80) and \
        color.judge_rgb_range(self, 1180, 621, 200, 255, 180, 240, 0, 80):
        return 3


def judge_auto(self):
    if color.judge_rgb_range(self, 1250, 677, 180, 255, 180, 255, 200, 255) and \
        color.judge_rgb_range(self, 1170, 677, 180, 255, 180, 255, 200, 255):
        return 'off'
    elif color.judge_rgb_range(self, 1250, 677, 200, 255, 180, 255, 0, 80) and \
        color.judge_rgb_range(self, 1170, 677, 200, 255, 180, 255, 0, 80):
        return 'on'


def change_acc_auto(self):
    self.logger.info("-- CHANGE acceleration phase and auto --")
    y = 625
    acc_phase = judge_acc(self)
    if acc_phase == 1:
        self.logger.info("CHANGE acceleration phase from 1 to 3")
        self.click(1215, y, wait_over=True, count=2)
    elif acc_phase == 2:
        self.logger.info("CHANGE acceleration phase from 2 to 3")
        self.click(1215, y, wait_over=True)
    elif acc_phase == 3:
        self.logger.info("ACCELERATION phase 3")
    else:
        self.logger.warning("CAN'T DETECT acceleration BUTTON")
    y = 677

    auto_phase = judge_auto(self)
    if auto_phase == 'off':
        self.logger.info("CHANGE MANUAL to auto")
        self.click(1215, y)
    elif auto_phase == 'on':
        self.logger.info("AUTO")
    else:
        self.logger.warning("can't identify auto button")


def enter_fight(self):
    img_possibles = {
        'normal_task_present': (640, 519),
        'normal_task_teleport-notice': (886, 165)
    }
    rgb_ends = "fighting_feature"
    img_pop_ups = {"activity_choose-buff": (644, 570)}
    picture.co_detect(self, rgb_ends, None, None, img_possibles, True, img_pop_ups=img_pop_ups)


def auto_fight(self, need_change_acc=True):
    enter_fight(self)
    if need_change_acc:
        time.sleep(2)
        self.latest_img_array = self.get_screenshot_array()
        change_acc_auto(self)


def check_episode(self):
    position1 = [982, 282]
    position2 = [833, 537]
    k = (position2[1] - position1[1]) / (position2[0] - position1[0])
    b = position1[1] - k * position1[0]
    for i in range(833, 982):
        y = int(k * i + b)
        if color.judge_rgb_range(self, i, y, 250, 255, 177, 200, 0, 80):
            return i + 155, y + 17
    return "ALL_CLEAR"


def to_episode(self, num):
    origin_position = {
        'CN': [0, [305, 255], [526, 449], [892, 255], [597, 449]],
        'Global': [0, [305, 255], [526, 449], [892, 255], [263, 470], [850, 630]],
        'JP': [0, [305, 255], [526, 449], [892, 255], [278, 463], [850, 630], [729, 249]]
    }
    episode_position = origin_position[self.server]
    if num in [1, 2, 3, 4]:
        self.swipe(14, 364, 654, 364, duration=0.1, post_sleep_time=0.5)
    if num == 4:
        self.swipe(654, 364, 14, 364, duration=0.1, post_sleep_time=0.5)
    img_possibles = {
        "main_story_menu": episode_position[num],
        "main_story_select-episode": (60, 36)
    }
    img_ends = "main_story_episode" + str(num)
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    return True


def check_current_plot_status(self, position):
    if color.judge_rgb_range(self, position[0], position[1], 245, 255, 214, 234, 0, 40):
        return "CLEAR"
    if color.judge_rgb_range(self, position[0], position[1], 170, 196, 178, 199, 178, 199):
        return "UNLOCK"
    if color.judge_rgb_range(self, position[0], position[1], 197, 207, 200, 210, 200, 210):
        return "UNCLEAR"


def clear_current_plot(self, skip_first_screenshot=False):
    rgb_possibles = {
        'reward_acquired': (640, 100),
    }
    img_possibles = {
        "main_story_episode-info": (650, 511),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519),
        'main_page_notice': (887, 166),
        'normal_task_fight-confirm': (1168, 659),
        'normal_task_fail-confirm': (643, 658),
        'normal_task_task-finish': (1038, 662),
    }
    img_ends = [
        "main_story_episode-cleared-feature",
        "main_story_plot-index",
        "main_story_plot-not-open",
        ("plot_formation", 0.9),
        ("plot_self-formation", 0.9),
        "normal_task_task-wait-to-begin-feature",
        "main_story_continue-plot",
        "episode5"
    ]
    res = picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    if res == "main_story_continue-plot":
        self.click(772, 516, wait_over=True)
        return clear_current_plot(self)
    if res == "main_story_episode-cleared-feature" or res == "main_story_plot-index":
        return res
    if res == "normal_task_task-wait-to-begin-feature":
        stage_data = check_state_and_get_stage_data(self)
        for i in range(0, len(stage_data['start'])):
            to_formation_edit_i(self, i + 1, stage_data['start'][i])
            auto_choose_formation(self, True, {"formation_edit" + str(i + 1): (1183, 183)},
                                  "formation_edit" + str(i + 1))
            to_normal_task_wait_to_begin_page(self, True)
        start_mission(self)
        check_skip_fight_and_auto_over(self)
        start_action(self, stage_data['actions'])
    rgb_ends = "fighting_feature"
    img_possibles = {"plot_formation": (1157, 651)}
    if res == "plot_self-formation":
        auto_choose_formation(self, True)
        img_possibles = {"plot_self-formation": (1157, 651)}
    picture.co_detect(self, rgb_ends, None, None, img_possibles, True)
    auto_fight(self)
    return clear_current_plot(self)


def auto_choose_formation(self, skip_first_screenshot=False, rgb_possibles=None, rgb_ends=None):
    self.logger.info("AUTO choose formation")
    img_possibles = {"plot_self-formation": (1180, 183)}
    img_ends = "plot_change-unit-formation"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    self.click(649, 596, wait_over=True)
    img_possibles = {"plot_change-unit-formation": (1130, 586)}
    img_ends = "plot_self-formation"
    picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, True)


def push_episode(self, num, is_final=False):
    if not is_final:
        self.logger.info("-- Pushing Episode " + str(num) + " --")
        to_main_story(self, True)
    else:
        self.logger.info("-- Pushing Final Episode --")
    to_episode(self, num)
    episode_status = check_episode(self)
    while episode_status != "ALL_CLEAR":
        res = to_select_episode(self, episode_status, skip_first_screenshot=True)
        while res == "main_story_plot-index":
            possible_pos = [[728, 257], [668, 362]]
            for pos in possible_pos:
                if check_current_plot_status(self, pos) == "UNCLEAR":
                    to_episode_info(self, pos, True)
                    res = clear_current_plot(self, True)
                    break
            else:
                res = to_select_episode(self, episode_status, False)
        if not is_final:
            to_main_story(self, True)
        to_episode(self, num)
        episode_status = check_episode(self)
    if not is_final:
        self.logger.warning("-- Episode " + str(num) + " ALL Cleared --")
    else:
        self.logger.warning("-- Final Episode ALL Cleared --")


def to_main_story(self, skip_first_screenshot=False):
    rgb_possibles = {
        'main_page': (1188, 575)
    }
    img_possibles = {
        "main_page_bus": (1098, 261),
        "main_story_enter-main-story": (327, 510),
        "main_story_episode5": (149, 109),
        "main_story_select-episode": (60, 36),
    }
    img_ends = "main_story_menu"
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_select_episode(self, res, skip_first_screenshot):
    img_possibles = {
        "main_story_menu": res,
        "main_story_episode5": res
    }
    img_ends = [
        "main_story_episode-cleared-feature",
        "main_story_plot-index",
        "main_story_plot-not-open",
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_episode_info(self, pos, skip_first_screenshot=False):
    img_possibles = {"main_story_select-episode": (pos[0] + 466, pos[1])}
    img_ends = "main_story_episode-info"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def check_state_and_get_stage_data(self):
    self.logger.info("-- CHECKING CURRENT STATE --")
    img_possibles = {"normal_task_mission-operating-task-info": (993, 642)}
    img_ends = "normal_task_mission-operating-task-info-notice"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    path = "src/images" + "/" + self.server + "/main_story/grid_mission_info"
    for files, dirs, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".png"):
                name = "main_story_" + filename[:-4]
                if image.compare_image(self, name, need_log=False):
                    self.logger.info("CURRENT STATE: " + filename[:-4])
                    img_possibles = {"normal_task_mission-operating-task-info-notice": (993, 97)}
                    img_ends = "normal_task_task-wait-to-begin-feature"
                    picture.co_detect(self, None, None, img_ends, img_possibles, True)
                    return self.main_story_stage_data[filename[:-4]]


def process_regions(self, value):
    if type(value) is list:
        return value
    if type(value) is int:
        return [value]
    value = value.split(',')
    res = []
    for i in range(0, len(value)):
        try:
            res.append(int(value[i]))
        except ValueError:
            self.logger.error("Invalid region value : " + value[i])
    return res
