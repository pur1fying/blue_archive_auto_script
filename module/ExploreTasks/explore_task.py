from core import color, image, picture
from module import main_story, normal_task, hard_task
from module.ExploreTasks.TaskUtils import to_mission_info, execute_grid_task, get_challenge_state, \
    employ_units, get_stage_data, convert_team_config, to_region


def validate_and_add_task(self, task: str, tasklist: list[tuple[int, int, dict]],
                          isNormal: bool) -> tuple[bool, str]:
    """
    Verifies the task information and returns the results.

    Args:
        self: The BAAS thread
        task: Task information. Example:16-2-sss
        tasklist: The list to contain tasks
        isNormal: Defines whether the task is a normal task or a hard task.

    Returns:
        Tuple[bool, str]:
            - The first element (bool): The verification result. Returns True if verification passes; otherwise, False.
            - The second element (str): The error message. Returns a detailed error message if verification fails; otherwise, an empty string.
    """
    task = task.strip() # Remove leading and trailing spaces, and whitespaces
    valid_chapter_range = self.static_config.explore_normal_task_region_range if isNormal \
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

    region_data = get_stage_data(region, isNormal)
    if isNormal:
        maxMission = 6 if region % 3 != 0 else 7
    else:
        maxMission = 4
    for i in range(1, maxMission) if mission == -1 else [mission]:
        # For normal tasks:
        # if mission is specified, then add mission only ,otherwise add 1~5,
        # if the region has -A mission, then add -6
        if not any(f"{region}-{i}" in key for key in region_data.keys()):
            return False, f"No task data found for mission {region}-{i}"
        tasklist.append((region, i, {taskDataName: taskData for taskDataName, taskData in region_data.items()
                                     if taskDataName.startswith(f"{region}-{i}")}))

    return True, ""


def need_fight(self, taskDataName: str, isNormal: bool):
    """
    Determines if a fight is needed based on the given task parameters.

    This function checks various conditions (SSS rank, present requirement, and task completion)
    to decide whether a fight is necessary for the current task.

    Args:
        self: The BAAS Thread
        taskDataName: The task data name.
        isNormal: Defines whether the task is a normal task or a hard task.

    Returns:
        bool: True if a fight is needed, False otherwise.
    """

    if isNormal:
        # sub mission check (now only available in CN servers)
        if self.server == "CN" and image.compare_image(self, 'normal_task_SUB'):
            return True
        if "-6" in taskDataName:  # mission A sss check
            return color.rgb_in_range(self, 768, 357, 60, 80, 60, 80, 60, 80)

    # sss check
    sss_check = color.check_sweep_availability(self, True)
    if sss_check == 'no-pass' or sss_check == 'pass':
        if not isNormal:
            return "sss" in taskDataName
        return True

    # present check of hard tasks
    if (not isNormal) and "present" in taskDataName and color.match_rgb_feature(self, 'hardTaskHasPresent'):
        return True

    # challenge check
    if isNormal or "task" in taskDataName:
        return get_challenge_state(self, 1)[0] != 1
    return False


def explore_normal_task(self):
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

    for taskStr in str(self.config_set.config.explore_normal_task_list).split(','):
        result = validate_and_add_task(self, taskStr, tasklist, True)
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

    teamConfig = convert_team_config(self)

    for task in tasklist:
        region = task[0]
        mission = task[1]

        # skip navigate to mission if previous task is already finished
        skip_navigate = False

        for taskDataName, taskData in task[2].items():
            taskName = str(region) + "-" + (str(mission) if mission != 6 else "A")
            self.logger.info(f"--- Start exploring {taskName}({taskDataName}) ---")

            if not skip_navigate:
                normal_task.to_normal_event(self, True)
                if not to_region(self, region, True):
                    self.logger.error(f"Skipping task {taskName} since it's not available.")
                    continue
                fullMissionList = []
                for i in range(1, 6):
                    fullMissionList.append(f"{region}-{i}")
                if region % 3 == 0:
                    fullMissionList.append(f"{region}-A")
                missionButtonPos = image.swipe_search_target_str(
                    self=self,
                    name="normal_task_enter-task-button",
                    search_area=(1055, 191, 1201, 632),
                    threshold=0.8,
                    possible_strs=fullMissionList,
                    target_str_index=mission - 1,
                    swipe_params=(917, 552, 917, 220, 0.2, 1.0),
                    ocr_language='en-us',
                    ocr_region_offsets=(-396, -7, 60, 33),
                    ocr_str_replace_func=None,
                    max_swipe_times=3,
                    ocr_candidates="0123456789-",
                    ocr_filter_score=0.2,
                )
                if not to_mission_info(self, missionButtonPos[1]):
                    self.logger.error(f"Skipping task {taskName} since it's not available.")
                    continue

            if not need_fight(self, taskDataName, True):
                self.logger.warning(f"{taskDataName} is already finished,skip.")
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
                if not employ_units(self, taskData, teamConfig):
                    self.logger.error(f"Skipping task {taskName} due to error.")
                    continue

                main_story.auto_fight(self)
            else:
                if not execute_grid_task(self, taskData):
                    self.logger.error(f"Skipping task {taskName} due to error.")
                    continue

                main_story.auto_fight(self)
                if self.config.manual_boss:
                    self.click(1235, 41)
            # skip unlocking animation by switching
            hard_task.to_hard_event(self, True)
            normal_task.to_normal_event(self, True)
    return True


def explore_hard_task(self):
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

    for taskStr in str(self.config_set.config.explore_hard_task_list).split(','):
        result = validate_and_add_task(self, taskStr, tasklist, False)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (taskStr, result[1]))
            continue
    self.logger.info("VALID TASK LIST {")
    for task in tasklist:
        taskName = str(task[0]) + "-" + (str(task[1]) if task[1] != 6 else "A")
        for taskDataName, taskData in task[2].items():
            self.logger.info(f"\t - {taskName}({taskDataName})")
    self.logger.info("}")

    for task in tasklist:
        region = task[0]
        mission = task[1]

        # skip navigate to mission if previous task is already finished
        skip_navigate = False
        for taskDataName, taskData in task[2].items():
            taskName = str(region) + "-" + (str(mission) if mission != 6 else "A")
            self.logger.info(f"--- Start exploring H{taskName}({taskDataName}) ---")

            mission_los = [249, 363, 476]
            if not skip_navigate:
                hard_task.to_hard_event(self, True)
                if not (to_region(self, region, False) and to_mission_info(self, mission_los[mission - 1])):
                    self.logger.error(f"Skipping task {taskName} since it's not available.")
                    continue

            if not need_fight(self, taskDataName, False):
                self.logger.warning(f"H{taskDataName} is already finished,skip.")
                skip_navigate = True
                continue
            skip_navigate = False

            if not execute_grid_task(self, taskData):
                self.logger.error(f"Skipping task {taskName} due to error.")
                continue

            main_story.auto_fight(self)
            if self.config.manual_boss:
                self.click(1235, 41)
            # skip unlocking animation by switching
            normal_task.to_normal_event(self, True)
            hard_task.to_hard_event(self, True)
    return True
