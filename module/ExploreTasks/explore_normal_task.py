import json
from core import color, image, picture
from module import main_story, normal_task, hard_task
from module.ExploreTasks.TaskUtils import to_mission_info, to_region, execute_grid_task, get_challenge_state, \
    employ_units


def validate_and_add_task(self, task: str, tasklist: list[tuple[int, int, dict]]) -> tuple[bool, str]:
    """
    Verifies the task information and returns the results.

    Args:
        self: The BAAS thread
        task: Task information. Example:16-2-sss
        tasklist: The list to contain tasks

    Returns:
        Tuple[bool, str]:
            - The first element (bool): The verification result. Returns True if verification passes; otherwise, False.
            - The second element (str): The error message. Returns a detailed error message if verification fails; otherwise, an empty string.
    """
    valid_chapter_range = self.static_config['explore_normal_task_region_range']
    info = task.split('-')
    if (not info[0].isdigit()) or int(info[0]) < valid_chapter_range[0] or int(info[0]) > valid_chapter_range[1]:
        return False, "Invalid chapter or unsupported chapter"
    if len(info) > 5:
        return False, "The length of info should not exceed 5"

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
            # TODO deal with X-X-A tasks
            pass
        else:
            return False, f"Invalid task type: {t}"

    region_data = get_stage_data(region)
    maxMission = 6 if region % 3 != 0 else 7
    for i in range(1, maxMission) if mission == -1 else [mission]:
        # if mission is specified, then add mission only ,otherwise add 1~5,
        # if the region has -A mission, then add -6
        if not any(f"{region}-{i}" in key for key in region_data.keys()):
            return False, f"No task data found for mission {region}-{i}"
        tasklist.append((region, i, {taskDataName: taskData for taskDataName, taskData in region_data.items()
                                     if taskDataName.startswith(f"{region}-{i}")}))

    return True, ""


def need_fight(self, taskDataName: str):
    """
    Determines if a fight is needed based on the given task parameters.

    This function checks various conditions (SSS rank, present requirement, and task completion)
    to decide whether a fight is necessary for the current task.

    Args:
        self: The BAAS Thread
        taskDataName: The task data name.

    Returns:
        bool: True if a fight is needed, False otherwise.
    """
    if (self.server == "CN" and
            image.compare_image(self, 'normal_task_SUB')):  # sub mission check (now only available in CN servers)
        return True
    if "-6" in taskDataName:  # mission A sss check
        return color.is_rgb_in_range(self, 768, 357, 60, 80, 60, 80, 60, 80)
    sss_check = color.check_sweep_availability(self, True)  # sss check
    if sss_check == 'no-pass' or sss_check == 'pass':
        return True
    if get_challenge_state(self, 1)[0] != 1:  # challenge check
        return True
    return False


def implement(self):
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

    for taskStr in str(self.config_set.config['explore_normal_task_list']).replace(" ", "").split(','):
        result = validate_and_add_task(self, taskStr, tasklist)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (taskStr, result[1]))
            continue
    self.logger.info("VALID TASK LIST {")
    for task in tasklist:
        taskName = str(task[0]) + "-" + (str(task[1]) if task[1] != 6 else "A")
        for taskDataName, taskData in task[2].items():
            self.logger.info(f"\t - {taskName}({taskDataName})")
    self.logger.info("}")
    if len(tasklist) == 0:
        return False

    self.quick_method_to_main_page()
    normal_task.to_normal_event(self, True)

    for task in tasklist:
        region = task[0]
        mission = task[1]
        for taskDataName, taskData in task[2].items():
            taskName = str(region) + "-" + (str(mission) if mission != 6 else "A")
            self.logger.info(f"--- Start exploring {taskName}({taskDataName}) ---")
            to_region(self, region, True)
            possible_strs = build_mission_name_possible_strs(region)
            p = image.swipe_search_target_str(
                self,
                "normal_task_enter-task-button",
                (1055, 191, 1201, 632),
                0.8,
                possible_strs,
                mission - 1,
                (917, 552, 917, 220, 0.2, 1.0),
                'Global',
                (-396, -7, 60, 33),
                None,
                3
            )
            y = p[1]
            to_mission_info(self, y)

            if not need_fight(self, taskDataName):
                self.logger.warning(f"{taskDataName} is already finished,skip.")
                normal_task.to_normal_event(self, True)
                continue

            # TODO: sub mission must be broken :D
            if mission == 6 or mission == 'sub':
                # to formation menu
                img_reactions = {
                    'normal_task_task-A-info': (946, 540)
                }
                img_ends = "normal_task_formation-menu"
                picture.co_detect(self, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)

                # get preset unit
                employ_units(self, taskData)

                # start battle
                img_reactions = {
                    'normal_task_formation-menu': (946, 540)
                }
                rgb_ends = "fighting_feature"
                picture.co_detect(self, rgb_ends=rgb_ends, img_reactions=img_reactions, skip_first_screenshot=True)
                main_story.auto_fight(self)
            else:
                execute_grid_task(self, taskData)
                main_story.auto_fight(self)
                if self.config['manual_boss']:
                    self.click(1235, 41)
            # skip unlocking animation by switching
            hard_task.to_hard_event(self, True)
            normal_task.to_normal_event(self, True)
    return True


def start_choose_side_team(self, index):
    self.logger.info("According to the config. Choose formation " + str(index))
    loy = [195, 275, 354, 423]
    y = loy[index - 1]
    img_possibles = {
        'normal_task_SUB': (637, 508),
        'normal_task_task-info': (946, 540)
    }
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_ends = "formation_edit" + str(index)
    rgb_possibles.pop("formation_edit" + str(index))
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)


def get_stage_data(region, is_normal=True):
    t = "normal_task" if is_normal else "hard_task"
    data_path = f"src/explore_task_data/{t}/{t}_{region}.json"
    with open(data_path, 'r') as f:
        stage_data = json.load(f)
    return stage_data


def build_mission_name_possible_strs(region):
    ret = []
    for i in range(1, 6):
        ret.append(f"{region}-{i}")
    if region % 3 == 0:
        ret.append(f"{region}-A")
    return ret
