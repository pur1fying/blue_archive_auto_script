import json
import time

from core import image, picture, Baas_thread, color
from core.image import swipe_search_target_str
from module import hard_task, main_story, normal_task


# Functions related to navigation or obtaining map data
# 与导航或获取地图数据相关的函数
def to_region(self, region: int, isNormal: bool) -> bool:
    ocr_area = [122, 178, 163, 208]
    curRegion = self.ocr.recognize_int(
        baas=self,
        region=ocr_area,
        log_info="Region Num",
        filter_score=0.2
    )
    self.logger.info("Current Region : " + str(curRegion))
    while curRegion != region and self.flag_run:
        if curRegion > region:
            if picture.match_img_feature(self, "normal_task_region-unavailable-left"):
                # region locked or not available
                return False
            self.click(40, 360, count=curRegion - region, rate=0.1, wait_over=True, duration=0.5)
        else:
            if picture.match_img_feature(self, "normal_task_region-unavailable-right"):
                # region locked or not available
                return False
            self.click(1245, 360, count=region - curRegion, rate=0.1, wait_over=True, duration=0.5)
        if isNormal:
            normal_task.to_normal_event(self)
        else:
            hard_task.to_hard_event(self)
        curRegion = self.ocr.recognize_int(
            baas=self,
            region=ocr_area,
            log_info="Region Num",
            filter_score=0.2
        )
        self.logger.info("Current Region : " + str(curRegion))
    return True


def to_mission_info(self, mission_button_y=0) -> bool:
    if color.rgb_in_range(self, 1150, mission_button_y, 40, 50, 70, 80, 85, 95):
        # mission locked or not available
        return False

    rgb_possibles = {"event_hard": (1114, mission_button_y), "event_normal": (1114, mission_button_y)}
    img_ends = [
        "normal_task_task-info",
        "activity_task-info",
        "normal_task_SUB"
    ]
    img_possibles = {
        'normal_task_select-area': (1114, mission_button_y),
        'normal_task_challenge-menu': (640, 490)
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)
    return True


def get_stage_data(region, isNormal):
    t = "normal_task" if isNormal else "hard_task"
    data_path = f"src/explore_task_data/{t}/{t}_{region}.json"
    with open(data_path, 'r') as f:
        stage_data = json.load(f)
    return stage_data


def get_challenge_state(self, challenge_count=1) -> list[int]:
    """
        Returns:
            list[int] :
                - int = 0, challenge unfinished
                - int = 1, challenge finished
                - int = -1, challenge state unknown
    """

    # to challenge menu
    challenge_button_y = {
        'CN': 272,
        'Global': 302,
        'JP': 302
    }
    img_ends = 'normal_task_challenge-menu'
    img_possibles = {
        "normal_task_challenge-button": (536, challenge_button_y[self.server]),
        "activity_quest-challenge-button": (319, 270)
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)

    result = []
    for i in range(1, challenge_count + 1):
        if image.compare_image(self, "normal_task_challenge" + str(i) + "-unfinished", 0.8, 10):
            result.append(0)
        elif image.compare_image(self, "normal_task_challenge" + str(i) + "-finished", 0.8, 10):
            result.append(1)
        else:
            result.append(-1)
    to_mission_info(self)
    return result


def convert_team_config(self: Baas_thread) -> dict:
    employ_method = self.config.choose_team_method
    teamConfig = {"burst": [], "pierce": [], "mystic": [], "shock": []}
    teamData = self.config.side_team_attribute if employ_method == "side" else self.config.preset_team_attribute
    for i, team in enumerate(teamData):
        for j, attr in enumerate(team):
            if attr in teamConfig:
                teamConfig[attr].append([0 if employ_method == "side" else i + 1, j + 1])
    return teamConfig


# Functions related to executing tasks
# 与执行任务相关的函数
def retreat(self):
    rgb_reactions = {"fighting_feature": (1226, 51)}
    img_reactions = {
        'normal_task_fight-pause': (908, 508),
        'normal_task_retreat-notice': (768, 507)
    }
    img_ends = ['normal_task_fail-confirm']
    picture.co_detect(self, rgb_reactions=rgb_reactions, img_ends=img_ends, img_reactions=img_reactions,
                      skip_first_screenshot=True)


def set_skip_status(self, status: bool) -> None:
    while self.flag_run:
        finish_adjustment = True
        if image.compare_image(self, 'normal_task_fight-skip') != status:
            finish_adjustment = False
            self.click(1194, 547, wait_over=True, duration=0.5)
        if image.compare_image(self, 'normal_task_auto-over') != status:
            finish_adjustment = False
            self.click(1194, 600, wait_over=True, duration=0.5)
        if finish_adjustment:
            return
        handle_task_pop_ups(self, False)


def switch_formation(self, current_formation, count: int = 1) -> int:
    for _ in range(count):
        self.click(83, 557, wait_over=True)
        while self.flag_run and get_formation_index(self) == current_formation:
            time.sleep(self.screenshot_interval)
    return get_formation_index(self)


def handle_task_pop_ups(self, skip_first_screenshot=False):
    img_reactions = {
        "normal_task_mission-operating-task-info-notice": (995, 101),
        "normal_task_end-turn": (890, 162),
        "normal_task_teleport-notice": (886, 162),
        'normal_task_present': (640, 519),
        "normal_task_fight-confirm": (1171, 670),
        'normal_task_fail-confirm': (640, 670),
    }
    img_ends = "normal_task_task-operating-feature"
    img_pop_ups = {"activity_choose-buff": (644, 570)}
    picture.co_detect(self, None, None, img_ends, img_reactions, skip_first_screenshot,
                      pop_ups_img_reactions=img_pop_ups)


def get_formation_index(self):
    region = {
        'CN': (116, 542, 131, 570),
        'Global': (116, 542, 131, 570),
        'JP': (116, 542, 131, 570)
    }
    handle_task_pop_ups(self)
    ocr_res = self.ocr.get_region_res(
        baas=self,
        region=region[self.server],
        language="en-us",
        log_info="Formation Index",
        candidates="1234",
        filter_score=0.2
    )
    try:
        ocr_res = int(ocr_res)
    except ValueError:
        return get_formation_index(self)
    if ocr_res not in [1, 2, 3, 4]:
        # TODO 无法识别可能会导致死循环
        return get_formation_index(self)
    return ocr_res


def end_turn(self):
    img_ends = ['normal_task_end-turn']
    img_reactions = {
        'normal_task_task-operating-feature': (1170, 670),
        'normal_task_present': (640, 519)
    }
    picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)

    # confirm the end turn pop-up
    img_ends = 'normal_task_task-operating-feature'
    img_reactions = {'normal_task_end-turn': (767, 501)}
    picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)


def wait_over(self):
    self.logger.info("Wait until move available")
    img_ends = "normal_task_mission-operating-task-info-notice"
    img_reactions = {
        'normal_task_task-operating-feature': (997, 670),
        'normal_task_teleport-notice': (885, 164),
        "normal_task_fight-confirm": (1171, 670),
        'normal_task_present': (640, 519),
    }
    picture.co_detect(self, None, None, img_ends, img_reactions,
                      True, pop_ups_rgb_reactions={"fighting_feature": (-1, -1)},
                      pop_ups_img_reactions={"activity_choose-buff": (644, 570)})


def confirm_teleport(self):
    self.logger.info("Wait Teleport Notice.")
    picture.co_detect(self, None, None, "normal_task_teleport-notice", None)
    self.logger.info("Confirm Teleport.")
    img_ends = ['normal_task_task-operating-feature']
    img_reactions = {'normal_task_teleport-notice': (767, 501)}
    picture.co_detect(self, None, None, img_ends, img_reactions, True)


# Functions related to task loops
# 与任务循环相关的函数

def execute_grid_task(self, taskData) -> bool:
    # enter the mission
    img_reactions = {
        'normal_task_help': (1017, 131),
        'normal_task_task-info': (946, 540),
        'activity_task-info': (946, 540),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
    }
    img_ends = "normal_task_task-wait-to-begin-feature"
    picture.co_detect(self, None, None, img_ends, img_reactions, True)

    if not employ_units(self, taskData, convert_team_config(self)):
        return False

    # start the mission
    img_ends = "normal_task_task-operating-feature"
    img_reactions = {
        'normal_task_task-begin-without-further-editing-notice': (768, 498),
        'normal_task_task-operating-round-over-notice': (888, 163),
        'normal_task_task-wait-to-begin-feature': (1171, 670),
        'normal_task_end-turn': (888, 163),
    }
    picture.co_detect(self, None, None, img_ends, img_reactions, True)

    wait_over(self)
    handle_task_pop_ups(self, True)
    set_skip_status(self, True)
    run_task_action(self, taskData['action'])
    return True


def run_task_action(self, actions):
    self.set_screenshot_interval(1)
    self.logger.info(f"------Starting actions. Total actions: {len(actions)}------")
    for i, action in enumerate(actions):
        description = f"-->Action {i + 1}:"

        operation = action['t']
        position = [-1, -1]
        if "p" in action:
            position = action["p"]

        current_formation = get_formation_index(self)
        self.logger.info("[-]Current formation : " + str(current_formation))

        if 'pre-wait' in action:
            self.logger.info(f"---Delaying {action['pre-wait']} second(s)---\n")
            time.sleep(action['pre-wait'])

        # turn off skip fight mode to handle retreat
        # 关闭自动战斗来处理撤退
        if 'retreat' in action:
            set_skip_status(self, False)
        wait_loading = False

        if operation.startswith('click'):
            description += f"Click @ ({position[0]}, {position[1]})"
            self.click(position[0], position[1], wait_over=True)
            if "teleport" in operation:
                confirm_teleport(self)
        elif operation.startswith("exchange"):
            # 切换队伍
            # Switch formation
            description += f"Switch formation"
            current_formation = switch_formation(self, current_formation)
            if "twice" in operation:
                description += " x2"
                current_formation = switch_formation(self, current_formation)
            if "click" in operation:
                description += f" && Click @ ({position[0]}, {position[1]})"
                self.click(position[0], position[1], wait_over=True)
            description += "\n"
        elif operation == 'end-turn':
            # End this turn
            # 结束回合
            description += "End Turn"
            end_turn(self)
            if i != len(actions) - 1:
                # skip wait over if specified
                if not ('end-turn-wait-over' in action and action['end-turn-wait-over'] is False):
                    description += " (wait over specified)"
                    wait_over(self)
                    wait_loading = True
            description += "\n"

        elif operation == 'choose_and_change':
            # exchange the formation
            # 交换两条队伍
            description += f"Exchange formation @ ({position[0]}, {position[1]})\n"
            self.click(position[0], position[1], wait_over=True, duration=0.3)
            self.click(position[0] - 100, position[1], wait_over=True, duration=1)

        if 'description' in action:
            description += f"->info:{action['description']}\n"
        self.logger.info(description)

        if 'retreat' in action:
            # handle retreat
            # 处理撤退
            description += f"Retreating fight {action['retreat'][1:]}\n"
            fight_counts = action['retreat'][0]
            for current_fight_index in range(0, fight_counts):
                main_story.auto_fight(self)
                if current_fight_index + 1 in action['retreat'][1:]:
                    retreat(self)
                handle_task_pop_ups(self, False)
            set_skip_status(self, True)

        if 'ec' in action:
            while self.flag_run and get_formation_index(self) == current_formation:
                time.sleep(self.screenshot_interval)

        if 'wait-over' in action:
            wait_over(self)
            wait_loading = True
            time.sleep(2)

        if 'post-wait' in action:
            self.logger.info(f"---Delaying {action['pre-wait']} second(s)---\n")
            time.sleep(action['post-wait'])

        if i != len(actions) - 1:
            handle_task_pop_ups(self, wait_loading)
    self.set_screenshot_interval(self.config.screenshot_interval)


def employ_units(self, taskData: dict, teamConfig: dict) -> bool:
    self.logger.info(f"Employ team method: {self.config.choose_team_method}.")
    attribute_type_fallbacks = {"burst": "mystic", "mystic": "shock", "shock": "pierce", "pierce": "burst"}

    employ_pos: list[list[int, int]] = []

    if self.config.choose_team_method == "order":
        # give employ pos a fallback value to let it employ formations by order(from 1-4)_
        employ_pos = [[0, 1], [0, 2], [0, 3], [0, 4]]
    else:
        # Number of units available for each attribute: burst, pierce, mystic, shock
        unit_available = {attribute: len(preset) for attribute, preset in teamConfig.items()}

        # Number of units used for each attribute: burst, pierce, mystic, shock
        unit_used = {attribute: 0 for attribute, count in teamConfig.items()}

        # Number of units available in total
        total_available = sum([len(preset) for attribute, preset in teamConfig.items()])

        unit_need = len([attribute for attribute, info in taskData["start"] if attribute != "swipe"])
        if total_available <= unit_need:
            self.logger.error(
                f"Employ failed: Insufficient presets. Currently used: {unit_need}, total available: {total_available}")
            return False

        for attribute, info in taskData["start"]:
            if attribute == "swipe":  # skip if it's a swipe command.
                continue

            # switch to the next attribute available.
            cur_attribute = attribute
            while unit_available[cur_attribute] == unit_used[cur_attribute] \
                    or (self.server == "CN" and cur_attribute == "shock"):
                cur_attribute = attribute_type_fallbacks[cur_attribute]

            employ_pos.append(teamConfig[cur_attribute][unit_used[cur_attribute]])
            unit_used[cur_attribute] += 1

    employed = 0
    for command, info in taskData["start"]:
        if command == "swipe":
            time.sleep(1)
            self.u2_swipe(info[0], info[1], info[2], info[3], duration=info[4], post_sleep_time=1)
        else:
            # employ command
            column = employ_pos[employed][0]
            row = employ_pos[employed][1]
            self.logger.info(f"Choosing team from preset {column}-{row}.")

            preset_y = 0

            # choose from side
            if column == 0:
                loy = [195, 275, 354, 423]
                y = loy[row - 1]
                img_reactions = {
                    "normal_task_task-wait-to-begin-feature": (info[0], info[1]),  # info:[x,y] the entry of employ
                }
                rgb_reactions = {
                    "normal_task_formation-menu": (74, y)
                }
                rgb_ends = "formation_edit" + str(row)
                picture.co_detect(self, rgb_ends, rgb_reactions, None, img_reactions, True)
            else:
                # open formation menu -> preset menu -> choose column
                img_reactions = {
                    "normal_task_task-wait-to-begin-feature": (info[0], info[1]),  # info:[x,y]
                }
                img_ends = "normal_task_formation-menu"
                picture.co_detect(self, img_reactions=img_reactions, img_ends=img_ends, skip_first_screenshot=True)

                img_reactions = {
                    "normal_task_formation-menu": (1204, 486),
                    "normal_task_formation-preset": (178 + (column - 1) * 156, 153)
                }
                rgb_ends = "preset_choose" + str(column)
                picture.co_detect(self, img_reactions=img_reactions, rgb_ends=rgb_ends, skip_first_screenshot=True)

                offsets = {
                    'CN': (-1103, 0, 16, 33),
                    'Global': (-1048, -4, 20, 36),
                    'JP': (-1103, 0, 16, 33)
                }

                presetButtonPos = swipe_search_target_str(
                    self,
                    "normal_task_formation-edit-preset-name",
                    search_area=(1156, 201, 1229, 553),
                    threshold=0.8,
                    possible_strs=["1", "2", "3", "4", "5"],
                    target_str_index=row - 1,
                    swipe_params=(145, 578, 145, 273, 1.0, 0.5),
                    ocr_language="en-us",
                    ocr_region_offsets=offsets[self.server],
                    ocr_str_replace_func=None,
                    max_swipe_times=5,
                    ocr_candidates="12345",
                    ocr_filter_score=0.2
                )
                preset_y = presetButtonPos[1] + 76

            # confirm employ
            img_reactions = {
                "normal_task_formation-preset": (1151, preset_y),
                "normal_task_formation-set-confirm": (761, 574),
                "normal_task_formation-menu": (1154, 625),
                "task-begin-without-further-editing-notice": (888, 164)
            }
            img_ends = [
                "normal_task_task-wait-to-begin-feature",
                "normal_task_task-operating-feature"
            ]
            rgb_ends = "fighting_feature"
            picture.co_detect(self, rgb_ends=rgb_ends, img_reactions=img_reactions, img_ends=img_ends,
                              skip_first_screenshot=True)

            employed += 1
    return True
