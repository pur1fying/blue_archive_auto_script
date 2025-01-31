import json
from core import color, image, picture
from module import main_story, normal_task, hard_task
from module.ExploreTasks.TaskUtils import to_mission_info, to_region, execute_grid_task, get_challenge_state


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
    submission = -1
    for t in info[1:]:
        if t.isdigit():
            if submission != -1:
                return False, "Multiple submission specified"
            if int(t) < 0 or int(t) > 5:
                return False, "Invalid submission"
            submission = int(t)
        elif t == "A":
            if region % 3 != 0:
                return False, "Invalid submission"
            # TODO deal with X-X-A tasks
            pass
        else:
            return False, f"Invalid task type: {t}"

    data_path = f"src/explore_task_data/normal_task/normal_task_{region}.json"
    with open(data_path, 'r') as file:
        region_data = json.load(file)
        for i in range(1, 6) if submission == -1 else [submission]:
            # if submission is specified, then add submission only ,otherwise add 1~5
            if f"{region}-{i}" in region_data:
                tasklist.append((region, i, region_data[f"{region}-{i}"]))
            else:
                return False, f"No task data found for region {region}-{i}"
    return True, ""


def need_fight(self):
    """
    Determines if a fight is needed based on the given task parameters.

    This function checks various conditions (SSS rank, present requirement, and task completion)
    to decide whether a fight is necessary for the current task.

    Args:
        self: The BAAS Thread

    Returns:
        bool: True if a fight is needed, False otherwise.
    """
    if (self.server == "CN" and
        image.compare_image(self, 'normal_task_SUB')):  # submission check (now only available in CN servers)
        return True
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
        - submission (int): The submission ID or count.
        - stage_data (dict): The stage data.
    """

    for taskStr in str(self.config_set.config['explore_normal_task_regions']).split(','):
        result = validate_and_add_task(self, taskStr, tasklist)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (taskStr, result[1]))
            continue
    self.logger.info("VALID TASK LIST {")
    for task in tasklist:
        self.logger.info(f"\t- {task[0]}-{task[1]}")
    self.logger.info("}")
    if len(tasklist) == 0:
        return False

    self.quick_method_to_main_page()
    normal_task.to_normal_event(self)

    for task in tasklist:
        region = task[0]
        mission = task[1]
        self.logger.info(f"--- Start exploring {region}-{mission} ---")

        normal_task_y_coordinates = [242, 341, 439, 537, 611]

        to_region(self, region, True)
        self.swipe(917, 220, 917, 552, duration=0.2, post_sleep_time=1)
        to_mission_info(self, normal_task_y_coordinates[mission - 1])

        if not need_fight(self):
            self.logger.warning(f"{region}-{mission} is already finished,skip.")
            normal_task.to_normal_event(self, True)
            continue

        if mission == 'sub':
            start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
            rgb_possibles = {
                "formation_edit" + str(self.config[self.stage_data[str(region)]['SUB']]): (1171, 670),
            }
            rgb_ends = "fighting_feature"
            picture.co_detect(self, rgb_ends, rgb_possibles, None, None, True)
        else:
            execute_grid_task(self, task[2])
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
