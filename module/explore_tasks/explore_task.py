from __future__ import annotations

from typing import TYPE_CHECKING

from core import color, image, picture
from module import main_story
from module.explore_tasks.task_utils import to_mission_info, execute_grid_task, get_challenge_state, \
    employ_units, get_stage_data, convert_team_config, to_region, to_hard_event, to_normal_event

if TYPE_CHECKING:
    from core.Baas_thread import Baas_thread


def validate_and_add_task(self: Baas_thread, task: str, tasklist: list[tuple[int, int, dict]],
                          is_normal: bool) -> tuple[bool, str]:
    """
    Verifies the task information and returns the results.

    Args:
        self: The BAAS thread
        task: Task information. Example:16-2-sss
        tasklist: The list to contain tasks
        is_normal: Defines whether the task is a normal task or a hard task.

    Returns:
        Tuple[bool, str]:
            - The first element (bool): The verification result. Returns True if verification passes; otherwise, False.
            - The second element (str): The error message. Returns a detailed error message if verification fails; otherwise, an empty string.
    """
    task = task.strip()  # Remove leading and trailing spaces, and whitespaces
    valid_chapter_range = self.static_config.explore_normal_task_region_range if is_normal \
        else self.static_config.explore_hard_task_region_range  # Get the valid chapter range based on the task type
    info = task.split('-')
    if (not info[0].isdigit()) or int(info[0]) < valid_chapter_range[0] or int(info[0]) > valid_chapter_range[1]:
        return False, "Invalid chapter or unsupported chapter"

    region = int(info[0])
    mission = -1
    # if mission == 6 it stands for X-A mission

    for t in info[1:]:
        if t.isdigit():
            if mission != -1:
                return False, "Multiple mission specified"
            if int(t) < 0 or int(t) > 5:
                return False, "Invalid mission"
            mission = int(t)
        elif t == "A":
            if region % 3 != 0:
                return False, "Invalid mission"
            mission = 6
            pass
        else:
            return False, f"Invalid task type: {t}"

    region_data = get_stage_data(region, is_normal)
    if is_normal:
        max_mission = 6 if region % 3 != 0 else 7
    else:
        max_mission = 4
    for i in range(1, max_mission) if mission == -1 else [mission]:
        # For normal tasks:
        # if mission is specified, then add mission only ,otherwise add 1~5,
        # if the region has -A mission, then add -6
        if not any(f"{region}-{i}" in key for key in region_data.keys()):
            return False, f"No task data found for mission {region}-{i}"
        tasklist.append((region, i, {task_data_name: task_data for task_data_name, task_data in region_data.items()
                                     if task_data_name.startswith(f"{region}-{i}")}))

    return True, ""


def need_fight(self: Baas_thread, task_data_name: str, is_normal: bool):
    """
    Determines if a fight is needed based on the given task parameters.

    This function checks various conditions (SSS rank, present requirement, and task completion)
    to decide whether a fight is necessary for the current task.

    Args:
        self: The BAAS Thread
        task_data_name: The task data name.
        is_normal: Defines whether the task is a normal task or a hard task.

    Returns:
        bool: True if a fight is needed, False otherwise.
    """

    if is_normal:
        # sub mission check (now only available in CN servers)
        if self.server == "CN" and image.compare_image(self, 'normal_task_SUB'):
            return True
        if "-6" in task_data_name:  # mission A sss check
            return color.rgb_in_range(self, 768, 357, 60, 80, 60, 80, 60, 80)

    # sss check
    sss_check = color.check_sweep_availability(self, True)
    if sss_check == 'no-pass' or sss_check == 'pass':
        if not is_normal:
            return "sss" in task_data_name
        return True

    # present check of hard tasks
    if (not is_normal) and "present" in task_data_name and color.match_rgb_feature(self, 'hardTaskHasPresent'):
        return True

    # challenge check
    if not self.config.explore_task_use_simple_mode:  # simple mode has no challenge
        if is_normal or "task" in task_data_name:
            return get_challenge_state(self, 1)[0] != 1
    return False


def set_explore_task_mode(self: Baas_thread):
    st = "simple" if self.config.explore_task_use_simple_mode else "grid"
    self.logger.info("Set Explore Task Mode : [ " + st + " ]")

    mode = f"explore-task-{st}-mode"
    rgb_possibles = {
        "explore-task-grid-mode": (1120, 187),
        "explore-task-simple-mode": (611, 178)
    }
    rgb_ends = mode
    rgb_possibles.pop(mode)
    picture.co_detect(self, rgb_ends, rgb_possibles, skip_first_screenshot=True)


def explore_normal_task(self: Baas_thread):
    """
        Implement the logic for exploring normal tasks.
    """

    tasklist: list[tuple[int, int, dict]] = []
    """
    Define tasklist as a list of tuple:
        - region (int): The region number.
        - mission (int): The mission number.
        - taskDatas (dict): The task datas.
    """
    self.to_main_page()
    for task_str in str(self.config_set.config.explore_normal_task_list).split(','):
        result = validate_and_add_task(self, task_str, tasklist, True)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (task_str, result[1]))
            continue
    self.logger.info("VALID TASK LIST {")
    for task in tasklist:
        task_name = str(task[0]) + "-" + (str(task[1]) if task[1] != 6 else "A")
        for task_data_name, task_data in task[2].items():
            self.logger.info(f"\t - {task_name}({task_data_name})")
    self.logger.info("}")
    if len(tasklist) == 0:
        return False

    team_config = convert_team_config(self)

    for task in tasklist:
        region, mission = task[0], task[1]

        # skip navigate to mission if previous task is already finished
        skip_navigate = False

        for task_data_name, task_data in task[2].items():
            task_name = str(region) + "-" + (str(mission) if mission != 6 else "A")
            self.logger.info(f"--- Start exploring {task_name}({task_data_name}) ---")

            if not skip_navigate:
                to_normal_event(self, True)
                if not to_region(self, region, True):
                    self.logger.error(f"Skipping task {task_name} since it's not available.")
                    continue
                full_mission_list = []
                for i in range(1, 6):
                    full_mission_list.append(f"{region}-{i}")
                if region % 3 == 0:
                    full_mission_list.append(f"{region}-A")
                mission_button_pos = image.swipe_search_target_str(
                    self=self,
                    name="normal_task_enter-task-button",
                    search_area=(1055, 191, 1201, 632),
                    threshold=0.8,
                    possible_strs=full_mission_list,
                    target_str_index=mission - 1,
                    swipe_params=(917, 552, 917, 220, 0.2, 1.0),
                    ocr_language='en-us',
                    ocr_region_offsets=(-396, -7, 60, 33),
                    ocr_str_replace_func=None,
                    max_swipe_times=3,
                    ocr_candidates="1234567890-A" if region % 3 == 0 else "1234567890-",
                    ocr_filter_score=0.2,
                )
                if not to_mission_info(self, mission_button_pos[1]):
                    self.logger.error(f"Skipping task {task_name} since it's not available.")
                    continue

            if not (mission == 6 or mission == 'sub'):
                set_explore_task_mode(self)
            if not need_fight(self, task_data_name, True):
                self.logger.warning(f"{task_name} is already finished,skip.")
                skip_navigate = True
                continue
            skip_navigate = False

            # TODO: sub mission must be broken :D
            if mission == 6 or mission == 'sub':
                # to formation menu
                img_reactions = {
                    'normal_task_task-A-info': (946, 540)
                }
                img_ends = "normal_task_formation-menu"
                picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)

                # get preset unit
                if not employ_units(self, self.config.choose_team_method, task_data, team_config):
                    self.logger.error(f"Skipping task {task_name} due to employ team error.")
                    continue

                main_story.auto_fight(self)
            elif self.config.explore_task_use_simple_mode:
                # to formation menu
                img_reactions = {
                    'normal_task_task-info': (946, 540)
                }
                img_ends = "normal_task_formation-menu"
                picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)

                # get preset unit
                if not employ_units(self, self.config.choose_team_method, extract_first_team(task_data), team_config):
                    self.logger.error(f"Skipping task {task_name} due to employ team error.")
                    continue

                main_story.auto_fight(self)
            else:
                if not execute_grid_task(self, task_data):
                    self.logger.error(f"Skipping task {task_name} due to error.")
                    continue
                main_story.auto_fight(self)
                if self.config.manual_boss:
                    self.click(1235, 41)
            # skip unlocking animation by switching
            to_hard_event(self, True)
            to_normal_event(self, True)
    return True


# We only need the first team for simple mode
def extract_first_team(taskData):
    for attribute, _ in taskData["start"]:
        if attribute in ["burst", "pierce", "mystic", "shock"]:
            return {"start": [[attribute, [0, 0]]]}


def explore_hard_task(self: Baas_thread):
    """
    Implement the logic for exploring hard tasks.
    """

    tasklist: list[tuple[int, int, dict]] = []
    """
    Define tasklist as a list of tuple:
        - region (int): The region number.
        - mission (int): The mission number.
        - taskDatas (dict): The task datas.
    """
    self.to_main_page()

    for task_str in str(self.config_set.config.explore_hard_task_list).split(','):
        result = validate_and_add_task(self, task_str, tasklist, False)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (task_str, result[1]))
            continue
    self.logger.info("VALID TASK LIST {")
    for task in tasklist:
        task_name = str(task[0]) + "-" + (str(task[1]) if task[1] != 6 else "A")
        for task_data_name, task_data in task[2].items():
            self.logger.info(f"\t - {task_name}({task_data_name})")
    self.logger.info("}")

    for task in tasklist:
        region, mission = task[0], task[1]

        # skip navigate to mission if previous task is already finished
        skip_navigate = False
        for task_data_name, task_data in task[2].items():
            task_name = str(region) + "-" + (str(mission) if mission != 6 else "A")
            self.logger.info(f"--- Start exploring H{task_name}({task_data_name}) ---")

            mission_los = [249, 363, 476]
            if not skip_navigate:
                to_hard_event(self, True)
                if not (to_region(self, region, False) and to_mission_info(self, mission_los[mission - 1])):
                    self.logger.error(f"Skipping task {task_name} since it's not available.")
                    continue

            set_explore_task_mode(self)

            if not need_fight(self, task_data_name, False):
                self.logger.warning(f"H{task_data_name} is already finished,skip.")
                skip_navigate = True
                continue
            skip_navigate = False

            if self.config.explore_task_use_simple_mode:
                # to formation menu
                img_reactions = {
                    "normal_task_task-info": (946, 540)
                }
                img_ends = "normal_task_formation-menu"
                picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)

                # get preset unit
                team_config = convert_team_config(self)
                if not employ_units(self, self.config.choose_team_method, extract_first_team(task_data), team_config):
                    self.logger.error(f"Skipping task {task_name} due to employ team error.")
                    continue

                main_story.auto_fight(self)
            else:
                if not execute_grid_task(self, task_data):
                    self.logger.error(f"Skipping task {task_name} due to error.")
                    continue

            main_story.auto_fight(self)
            if self.config.manual_boss:
                self.click(1235, 41)
            # skip unlocking animation by switching
            to_normal_event(self, True)
            to_hard_event(self, True)
    return True
