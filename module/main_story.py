import json
import os

from core import color, picture, image
from module.ExploreTasks.TaskUtils import execute_grid_task


def implement(self):
    self.logger.info("Pushing Main Story.")
    self.main_story_stage_data = get_stage_data()
    self.to_main_page()
    to_main_story(self, True)
    push_episode_list = process_regions(self, self.config.main_story_regions)
    if not push_episode_list:
        self.logger.warning("Use Default Push Episode List.")
        default_list = self.static_config.main_story_available_episodes
        push_episode_list = default_list[self.server]
    for i in range(0, len(push_episode_list)):
        current_episode = push_episode_list[i]
        is_final = False
        if current_episode == self.static_config.main_story_final_episode_num:
            is_final = True
        push_episode(self, current_episode, is_final)
    return True


def get_stage_data():
    path = "src/explore_task_data/main_story/main_story.json"
    with open(path, "r") as f:
        data = json.load(f)
    return data


def get_acceleration(self) -> int:
    """
    Determine the current acceleration phase based on the color of specific pixels on the screen.

    This function checks the RGB values at two specific pixel locations (1180, 621) and (1250, 621)
    to determine the current acceleration phase in the game.

    Parameters:
    self (object): The BAAS thread.

    Returns:
    int: The current acceleration phase.
         1 - First acceleration phase
         2 - Second acceleration phase
         3 - Third acceleration phase
         -1 - Unable to determine acceleration phase
    """
    if color.rgb_in_range(self, 1180, 621, 200, 255, 200, 255, 200, 255) and \
        color.rgb_in_range(self, 1250, 621, 200, 255, 200, 255, 200, 255):
        return 1
    elif color.rgb_in_range(self, 1250, 621, 100, 150, 200, 255, 200, 255) and \
        color.rgb_in_range(self, 1180, 621, 100, 155, 200, 255, 200, 255):
        return 2
    elif color.rgb_in_range(self, 1250, 621, 210, 255, 180, 240, 0, 80) and \
        color.rgb_in_range(self, 1180, 621, 200, 255, 180, 240, 0, 80):
        return 3
    return -1  # Unable to determine acceleration phase


def get_auto(self) -> int:
    """
    Determine the current auto mode status based on the color of specific pixels on the screen.

    This function checks the RGB values at two specific pixel locations (1250, 677) and (1170, 677)
    to determine whether the auto mode is on or off in the game.

    Parameters:
    self (object): The BAAS thread.

    Returns:
    int: The current auto mode status.
         0 - Auto mode is off
         1 - Auto mode is on
         -1 - Unable to determine auto mode status
    """
    if color.rgb_in_range(self, 1250, 677, 180, 255, 180, 255, 200, 255) and \
        color.rgb_in_range(self, 1170, 677, 180, 255, 180, 255, 200, 255):
        return 0
    elif color.rgb_in_range(self, 1250, 677, 200, 255, 180, 255, 0, 80) and \
        color.rgb_in_range(self, 1170, 677, 200, 255, 180, 255, 0, 80):
        return 1
    return -1


def set_acc_and_auto(self):
    # set acceleration phase to 3
    current_acceleration = get_acceleration(self)
    if current_acceleration == -1:
        self.logger.warning("Unable to detect acceleration phase.")
        return

    if current_acceleration != 3:
        self.click(1215, 625, wait_over=True, count=3 - current_acceleration)
    self.logger.info("Current acceleration phase: " + str(get_acceleration(self)))

    auto_phase = get_auto(self)
    if auto_phase == -1:
        self.logger.warning("Unable to detect auto status.")
    elif auto_phase == 0:
        self.click(1215, 677, wait_over=True)
    self.logger.info("Auto mode toggled:" + ("yes" if auto_phase else "no"))


def enter_battle(self):
    self.logger.info("Entering battle.")
    img_possibles = {
        'normal_task_present': (640, 519),
        'normal_task_teleport-notice': (886, 165),
        'plot_formation': (1157, 651),
        'plot_self-formation': (1157, 651)
    }
    img_ends = [
        "normal_task_fight-confirm",
        "normal_task_fail-confirm"
    ]
    rgb_ends = "fighting_feature"
    img_pop_ups = {
        "activity_choose-buff": (644, 570)
    }
    ret = picture.co_detect(self, rgb_ends, None, img_ends, img_possibles, True, pop_ups_img_reactions=img_pop_ups)
    if ret != "fighting_feature":
        self.logger.info("Fight Ended.")
    return ret


def auto_fight(self, need_change_acc=True):
    ret = enter_battle(self)
    if need_change_acc and ret == "fighting_feature":
        self.update_screenshot_array()
        set_acc_and_auto(self)


def check_episode(self):
    position1 = [982, 282]
    position2 = [833, 537]
    k = (position2[1] - position1[1]) / (position2[0] - position1[0])
    b = position1[1] - k * position1[0]
    for i in range(833, 982):
        y = int(k * i + b)
        if color.rgb_in_range(self, i, y, 250, 255, 177, 200, 0, 80):
            return i + 155, y + 17
    return "ALL_CLEAR"


def to_episode(self, num):
    """
        ensure goto required episode page, may not single swipe
    """
    final_num = self.static_config.main_story_final_episode_num
    if num == final_num:
        img_possibles = {
            "main_story_menu": (850, 630),
            "main_story_select-episode": (60, 36)
        }
        img_ends = "main_story_episode" + str(num)
        return picture.co_detect(self, None, None, img_ends, img_possibles, True)
    detect_episode_list = self.static_config.main_story_available_episodes[self.server].copy()
    detect_episode_list.remove(final_num)

    wait_to_detect_list = detect_episode_list.copy()
    last_detected_ep = False
    last_detected_pos = False

    while self.flag_run:
        last_detected_ep, last_detected_pos = search_episode(self, wait_to_detect_list)
        if not last_detected_ep:
            to_main_story(self, False)
            continue
        if num in last_detected_ep:
            img_possibles = {
                "main_story_menu": last_detected_pos[last_detected_ep.index(num)],
                "main_story_select-episode": (60, 36)
            }
            img_ends = "main_story_episode" + str(num)
            return picture.co_detect(self, None, None, img_ends, img_possibles, True)
        else:
            _min = min(last_detected_ep)
            _max = max(last_detected_ep)
            x_start, x_end = 0, 400
            if num < _min:  # search left to _max
                wait_to_detect_list = detect_episode_list[:detect_episode_list.index(_max)]
            else:  # search right from _min
                x_start, x_end = x_end, x_start
                wait_to_detect_list = detect_episode_list[detect_episode_list.index(_min) + 1:]
            self.swipe(x_start, 142, x_end, 142, 0.7, post_sleep_time=1)
            to_main_story(self, False)
    return True


def search_episode(self, possible_list):
    self.logger.info("Search Episode " + str(possible_list))
    regions = [[0, 293, 910, 362], [0, 506, 812, 588]]
    appeared_episodes = []
    position = []
    for i in range(0, len(possible_list)):
        for j in range(0, len(regions)):
            ret = image.search_in_area(self, "main_story_episode-" + str(possible_list[i]) + "-title", regions[j], 0.8)
            if ret:
                self.logger.info("Episode " + str(possible_list[i]) + " detected at " + str(ret))
                appeared_episodes.append(possible_list[i])
                position.append(ret)
                break
    if len(appeared_episodes) == 0:
        return False, False
    return appeared_episodes, position


def check_current_plot_status(self, position):
    if color.rgb_in_range(self, position[0], position[1], 245, 255, 214, 234, 0, 40):
        return "CLEAR"
    if color.rgb_in_range(self, position[0], position[1], 170, 196, 178, 199, 178, 199):
        return "UNLOCK"
    if color.rgb_in_range(self, position[0], position[1], 197, 207, 200, 210, 200, 210):
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
        'main_story_get-new-search-data': (514, 510),
    }
    img_ends = [
        "main_story_episode-cleared-feature",
        "main_story_plot-index",
        "main_story_plot-not-open",
        ("plot_formation", 0.9),
        ("plot_self-formation", 0.9),
        "normal_task_task-wait-to-begin-feature",
        "main_story_continue-plot",
    ]
    res = picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    if res == "main_story_continue-plot":
        self.click(772, 516, wait_over=True)
        return clear_current_plot(self)
    if res == "main_story_episode-cleared-feature" or res == "main_story_plot-index":
        return res
    if res == "normal_task_task-wait-to-begin-feature":
        stage_data = check_state_and_get_stage_data(self)
        execute_grid_task(self, stage_data)
    auto_fight(self)
    return clear_current_plot(self)


def auto_choose_formation(self, skip_first_screenshot=False, rgb_possibles=None, rgb_ends=None):
    self.logger.info("AUTO choose formation")
    img_possibles = {"plot_self-formation": (1180, 183)}
    img_ends = [
        "plot_change-unit-formation",
        "plot_edit-self-formation"
    ]
    ret = picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    if ret == "plot_change-unit-formation":
        self.click(649, 596, wait_over=True)
    else:
        self.click(936, 592, wait_over=True)
    img_possibles = {
        "plot_edit-self-formation": (1174, 595),
        "plot_change-unit-formation": (1130, 586)
    }
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
    final_num = self.static_config.main_story_final_episode_num
    img_possibles = {
        "main_page_bus": (1098, 261),
        "main_story_enter-main-story": (327, 510),
        "main_story_episode" + str(final_num): (149, 109),
        "main_story_select-episode": (60, 36),
    }
    img_ends = "main_story_menu"
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_select_episode(self, res, skip_first_screenshot):
    final_num = self.static_config.main_story_final_episode_num
    img_possibles = {
        "main_story_menu": res,
        "main_story_episode" + str(final_num): res
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
    img_possibles = {"normal_task_task-wait-to-begin-feature": (993, 642)}
    img_ends = "normal_task_mission-operating-task-info-notice"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    path = "src/images" + "/" + self.server + "/main_story/grid_mission_info"
    for files, dirs, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".png"):
                name = "main_story_" + filename[:-4]
                if image.compare_image(self, name):
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
