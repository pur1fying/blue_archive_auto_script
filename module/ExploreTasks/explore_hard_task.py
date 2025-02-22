from core import color
from module import main_story, hard_task, normal_task
from module.ExploreTasks.TaskUtils import get_challenge_state, to_region, execute_grid_task, to_mission_info
from module.ExploreTasks.explore_normal_task import get_stage_data


def validate_and_add_task(self, task: str, tasklist: list[tuple[int, int, list[str], dict]]) -> tuple[bool, str]:
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
    valid_chapter_range = self.static_config.explore_hard_task_region_range
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
            if int(t) < 0 or int(t) > 3:
                return False, "Invalid submission"
            submission = int(t)
        else:
            return False, f"Invalid task type: {t}"

    region_data = get_stage_data(region, False)

    for i in range(1, 4) if submission == -1 else [submission]:
        tasks = ["sss", "present", "task"]
        while len(tasks) > 0:
            current_task = [tasks.pop(0)]
            current_task_stage_data = ""
            for key in region_data.keys():
                if key.startswith(f"{region}-{i}"):  # Find the stage data for the current region and submission
                    current_stage_data_tasks = key.split("-")[2:]
                    if current_task[0] in current_stage_data_tasks:  # Check if the stage data contains the current task
                        current_task_stage_data = region_data[key]
                        temp = 0
                        # Check if the stage data contains the remaining tasks
                        while len(tasks) != 0 and temp < len(tasks):
                            if tasks[temp] in current_stage_data_tasks:
                                current_task.append(tasks.pop(temp))
                            else:
                                temp += 1
                        tasklist.append((region, i, current_task, current_task_stage_data))
                        break
            if current_task_stage_data == "":
                return False, f"No task data found for region {region}-{i}-{current_task[0]}"
    return True, ""


def need_fight(self, check_data: list[str]):
    """
    Determines if a fight is needed based on the given task parameters.

    This function checks various conditions (SSS rank, present requirement, and task completion)
    to decide whether a fight is necessary for the current task.

    Args:
        self: The BAAS Thread
        check_data: The list of task data to check
    Returns:
        bool: True if a fight is needed, False otherwise.
    """
    if "sss" in check_data:
        sss_check = color.check_sweep_availability(self, True)  # sss check
        if sss_check == 'no-pass' or sss_check == 'pass':
            return True
    if "present" in check_data:
        if color.judgeRGBFeature(self, 'hardTaskHasPresent'):  # present check
            return True
    if "task" in check_data:
        if get_challenge_state(self, 1)[0] != 1:  # challenge check
            return True
    return False


def calc_team_number(self, current_task_stage_data):
    priority = {
        'pierce1': ['pierce1', 'pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2', 'shock1', 'shock2'],
        'pierce2': ['pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2', 'shock1', 'shock2'],
        'burst1': ['burst1', 'burst2', 'mystic1', 'mystic2', 'shock1', 'shock2', 'pierce1', 'pierce2'],
        'burst2': ['burst2', 'mystic1', 'mystic2', 'shock1', 'shock2', 'pierce1', 'pierce2'],
        'mystic1': ['mystic1', 'mystic2', 'shock1', 'shock2', 'burst1', 'burst2', 'pierce1', 'pierce2'],
        'mystic2': ['mystic2', 'burst1', 'shock1', 'shock2', 'burst2', 'pierce1', 'pierce2'],
        'shock1': ['shock1', 'shock2', 'pierce1', 'pierce2', 'mystic1', 'mystic2', 'burst1', 'burst2', ],
        'shock2': ['shock2', 'pierce1', 'pierce2', 'mystic1', 'mystic2', 'burst1', 'burst2', ]
    }
    length = len(current_task_stage_data['start'])
    used = {
        'pierce1': False,
        'pierce2': False,
        'burst1': False,
        'burst2': False,
        'mystic1': False,
        'mystic2': False,
        'shock1': False,
        'shock2': False,
    }
    keys = used.keys()
    last_chosen = 0
    res = []
    los = []
    for attr, position in current_task_stage_data['start'].items():
        if attr not in keys:
            res.append(attr)
            los.append(position)
            continue
        los.append(position)
        for i in range(0, len(priority[attr])):
            possible_attr = priority[attr][i]
            if (possible_attr == 'shock1' or possible_attr == 'shock2') and self.server == 'CN':
                continue
            possible_index = self.config[possible_attr]
            if not used[possible_attr] and 4 - possible_index >= length - len(
                    res) - 1 and last_chosen < possible_index:
                res.append(possible_index)
                used[possible_attr] = True
                last_chosen = self.config[possible_attr]
                break
    if len(res) != length:
        self.logger.warning("Insufficient forces are chosen")
        if length - len(res) <= 4 - last_chosen:
            for i in range(0, length - len(res)):
                res.append(last_chosen + i + 1)
        else:
            self.logger.warning("USE formations as the number increase")
            res.clear()
            for i in range(0, length):
                res.append(i + 1)
    self.logger.info("Choose formations : " + str(res))
    return res, los


def implement(self):
    """
    Implement the logic for exploring hard tasks.
    """

    tasklist: list[tuple[int, int, list[str], dict]] = []
    """
    Define tasklist as a list of tuple:
        - region (int): The region number.
        - submission (int): The submission ID or count.
        - stage_data (dict): The stage data.
    """
    for taskStr in str(self.config_set.config.explore_hard_task_list).split(','):
        result = validate_and_add_task(self, taskStr, tasklist)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (taskStr, result[1]))
            continue
    self.logger.info("VALID TASK LIST {")
    for task in tasklist:
        temp = "-".join(task[2])
        self.logger.info(f"\t- H{task[0]}-{task[1]}-{temp}")
    self.logger.info("}")
    if len(tasklist) == 0:
        return False

    mission_los = [249, 363, 476]
    self.quick_method_to_main_page()
    hard_task.to_hard_event(self, True)

    for task in tasklist:
        region = task[0]
        mission = task[1]
        check_data = task[2]
        self.logger.info(f"--- Start exploring H{region}-{mission} ---")
        to_region(self, region, False)
        to_mission_info(self, mission_los[mission - 1])
        if not need_fight(self, check_data):
            self.logger.warning(f"H{region}-{mission} is already finished,skip.")
            hard_task.to_hard_event(self, True)
            continue
        execute_grid_task(self, task[3])
        main_story.auto_fight(self)
        if self.config.manual_boss:
            self.click(1235, 41)

        # skip unlocking animation by switching
        normal_task.to_normal_event(self, True)
        hard_task.to_hard_event(self, True)
    return True
