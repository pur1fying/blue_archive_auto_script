import json
import time

from core import image, picture
from core.image import swipe_search_target_str
from module import hard_task, main_story, normal_task


# 与导航或获取地图数据相关的函数
def to_region(self, region, isNormal: bool):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    curRegion = self.ocr.recognize_int(self.latest_img_array, square[self.server], self.ratio)
    self.logger.info("Current Region : " + str(curRegion))
    while curRegion != region and self.flag_run:
        if curRegion > region:
            self.click(40, 360, count=curRegion - region, rate=0.1, wait_over=True, duration=0.5)
        else:
            self.click(1245, 360, count=region - curRegion, rate=0.1, wait_over=True, duration=0.5)
        # TODO 检测是否是未解锁区域
        if isNormal:
            normal_task.to_normal_event(self)
        else:
            hard_task.to_hard_event(self)
        curRegion = self.ocr.recognize_number(self.latest_img_array, square[self.server], int, self.ratio)
        self.logger.info("Current Region : " + str(curRegion))


def to_mission_info(self, y=0):
    rgb_possibles = {"event_hard": (1114, y), "event_normal": (1114, y)}
    img_ends = [
        "normal_task_task-info",
        "activity_task-info",
        "normal_task_SUB"
    ]
    img_possibles = {
        'normal_task_select-area': (1114, y),
        'normal_task_challenge-menu': (640, 490)
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def get_stage_data(region, is_normal=True):
    t = "normal_task" if is_normal else "hard_task"
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


# 与执行任务相关的函数
def retreat(self):
    rgb_reactions = {"fighting_feature": (1226, 51)}
    img_reactions = {
        'normal_task_fight-pause': (908, 508),
        'normal_task_retreat-notice': (768, 507)
    }
    img_ends = ['normal_task_fail-confirm']
    picture.co_detect(self, rgb_reactions=rgb_reactions, img_ends=img_ends, img_reactions=img_reactions,
                      skip_loading=True)


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
    ocr_res = self.ocr.recognize_number(self.latest_img_array, region[self.server], int, self.ratio)
    if ocr_res == 7:
        ocr_res = 1
    if ocr_res not in [1, 2, 3, 4]:
        # 无法识别可能会导致死循环
        return get_formation_index(self)
    return ocr_res


def end_turn(self):
    img_ends = ['normal_task_end-turn']
    img_reactions = {
        'normal_task_task-operating-feature': (1170, 670),
        'normal_task_present': (640, 519)
    }
    picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_loading=True)

    # confirm the end turn pop-up
    img_ends = 'normal_task_task-operating-feature'
    img_reactions = {'normal_task_end-turn': (767, 501)}
    picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_loading=True)


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
    self.logger.info("teleport")
    img_ends = ['normal_task_task-operating-feature']
    img_reactions = {'normal_task_teleport-notice': (767, 501)}
    picture.co_detect(self, None, None, img_ends, img_reactions, True)


# 与任务循环相关的函数

def execute_grid_task(self, taskData):
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

    employ_units(self, taskData)

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
        if 'retreat' in action:  # 关闭自动战斗来处理撤退
            set_skip_status(self, False)
        wait_loading = False

        if operation.startswith('click'):
            description += f"Click @ ({position[0]}, {position[1]})\n"
            self.click(position[0], position[1], wait_over=True)
            if "teleport" in operation:
                confirm_teleport(self)
        elif operation == 'teleport':
            description += f"Teleport\n"
            confirm_teleport(self)
        elif operation.startswith("exchange"):  # 切换队伍
            description += f"Switch formation"
            current_formation = switch_formation(self, current_formation)
            if "twice" in operation:
                description += " x2"
                current_formation = switch_formation(self, current_formation)
            if "click" in operation:
                description += f" && Click @ ({position[0]}, {position[1]})"
                self.click(position[0], position[1], wait_over=True)
            description += "\n"
        elif operation == 'end-turn':  # 结束回合
            description += "End Turn"
            end_turn(self)
            if i != len(actions) - 1:
                # skip wait over if specified
                if not ('end-turn-wait-over' in action and action['end-turn-wait-over'] is False):
                    description += " (wait over specified)"
                    wait_over(self)
                    wait_loading = True
            description += "\n"

        elif operation == 'choose_and_change':  # 交换两条队伍
            description += f"Exchange formation @ ({position[0]}, {position[1]})\n"
            self.click(position[0], position[1], wait_over=True, duration=0.3)
            self.click(position[0] - 100, position[1], wait_over=True, duration=1)

        if 'retreat' in action:  # 处理撤退
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

        if 'description' in action:
            description += f"->info:{action['description']}\n"
        self.logger.info(description)

        if i != len(actions) - 1:
            handle_task_pop_ups(self, wait_loading)
    self.set_screenshot_interval(self.config['screenshot_interval'])


def employ_units(self, taskData: dict) -> tuple[bool, str]:
    # get employ presets data
    priority = {"burst": "mystic", "mystic": "shock", "shock": "pierce", "pierce": "burst"}

    unit_available = {attribute: len(preset) for attribute, preset in tmp_teams.items()}
    # Number of units available for each attribute: burst, pierce, mystic, shock
    total_available = sum([len(preset) for attribute, preset in tmp_teams.items()])
    # Number of units available in total
    unit_used = {attribute: 0 for attribute, count in tmp_teams.items()}
    # Number of units used for each attribute: burst, pierce, mystic, shock
    currently_used = 0

    employ_presets: list[list[int, int]] = []

    for attribute, info in taskData["start"]:
        if attribute == "swipe":  # skip if it's a swipe command.
            continue
        if attribute not in ["burst", "pierce", "mystic", "shock"]:
            return False, f"Invalid attribute {attribute} in task data."

        current_attribute = attribute
        if total_available <= currently_used:
            return (False,
                    f"Insufficient presets. Currently used: {currently_used}, total available: {total_available}")
        while unit_available[current_attribute] - unit_used[current_attribute] == 0 \
            or (self.server == "CN" and current_attribute == "shock"):
            current_attribute = priority[current_attribute]
        employ_presets.append(tmp_teams[current_attribute][unit_used[current_attribute]])
        unit_used[current_attribute] += 1
        currently_used += 1

    employed = 0
    for command, info in taskData["start"]:
        if command == "swipe":
            time.sleep(1)
            self.swipe(info[0], info[1], info[2], info[3], duration=info[4])
            time.sleep(1)
        else:  # employ units from presets
            preset_column = employ_presets[employed][0]
            preset_row = employ_presets[employed][1]
            self.logger.info(f"Choosing team from preset {preset_column}-{preset_row}.")

            # open formation menu -> preset menu -> choose column
            img_reactions = {
                "normal_task_task-wait-to-begin-feature": (info[0], info[1]),  # info:[x,y]
            }
            img_ends = "normal_task_formation-menu"
            picture.co_detect(self, img_reactions=img_reactions, img_ends=img_ends, skip_loading=True)
            img_reactions = {
                "normal_task_formation-menu": (1204, 486),
                "normal_task_formation-preset": (178 + (preset_column - 1) * 156, 153)
            }
            rgb_ends = "preset_choose" + str(preset_column)
            picture.co_detect(self, img_reactions=img_reactions, rgb_ends=rgb_ends, skip_loading=True)

            offsets = {
                'CN': (-1103, 0, 16, 33),
                'Global': (-1048, -4, 20, 36),
                'JP': (-1103, 0, 16, 33)
            }

            p = swipe_search_target_str(
                self,
                "normal_task_formation-edit-preset-name",
                search_area=(1156, 201, 1229, 553),
                threshold=0.8,
                possible_strs=["1", "2", "3", "4", "5"],
                target_str_index=4,
                swipe_params=(145, 578, 145, 273, 1.0, 0.5),
                ocr_language="NUM",
                ocr_region_offsets=offsets[self.server],
                ocr_str_replace_func=None,
                max_swipe_times=5
            )

            # confirm use preset
            preset_y = p[1] + 76
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
                              skip_loading=True)

            employed += 1


tmp_teams = {"burst": [[1, 1], [3, 2]], "pierce": [[1, 2], [4, 4]], "shock": [[1, 3], [2, 3]],
             "mystic": [[1, 3], [2, 3]]}
