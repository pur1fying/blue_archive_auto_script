import importlib
import time

from core import color, picture
from module import main_story, normal_task, hard_task
from module.ExploreTasks.explore_normal_task import common_gird_method

tasklist: list[tuple[int, int, bool, bool, bool]] = []
"""
Define tasklist as a list of tuple:
    - region (int): The region number.
    - submission (int): The submission ID or count.
    - need_sss (bool): Whether a certain validation is required (True or False).
    - need_task (bool): Whether task-related processing is required (True or False).
    - need_present (bool): Whether presentation-related actions are required (True or False).
"""


def verify_and_add(self, task: str) -> tuple[bool, str]:
    """
    Verifies the task information and returns the results.

    Args:
        self:
        task: Task information. Example:16-2-sss

    Returns:
        Tuple[bool, str]:
            - The first element (bool): The verification result. Returns True if verification passes; otherwise, False.
            - The second element (str): The error message. Returns a detailed error message if verification fails; otherwise, an empty string.
    """
    global tasklist
    need_sss = bool(self.config['explore_hard_task_need_sss'])
    need_task = bool(self.config['explore_hard_task_need_task'])
    need_present = bool(self.config['explore_hard_task_need_present'])
    valid_chapter_range = self.static_config['explore_hard_task_region_range']
    info = task.split('-')
    if (not info[0].isdigit()) or int(info[0]) < valid_chapter_range[0] or int(info[0]) > valid_chapter_range[1]:
        return False, "Invalid chapter or unsupported chapter"
    if len(info) > 5:
        return False, "The length of info should not exceed 5"
    if info.count('sss') > 1 or info.count('present') > 1 or info.count('task') > 1:
        return False, "Duplicate task type: 'sss', 'present', or 'task' appears more than once"
    region = int(info[0])
    submission = -1
    for t in info[1:]:
        if t.isdigit():
            if submission != -1:
                return False, "Duplicated submission number"
            submission = int(t)
        if t == "sss":
            need_sss = True
        if t == "task":
            need_task = True
        if t == "present":
            need_present = True
    if submission == -1:
        for i in range(1, 4):
            tasklist.append((region, i, need_sss, need_task, need_present))
    else:
        tasklist.append((region, submission, need_sss, need_task, need_present))
    return True, ""


def task_to_string(task: tuple[int, int, bool, bool, bool]):
    taskStr = str(task[0]) + "-" + str(task[1])
    if task[2]:
        taskStr += "-sss"
    if task[3]:
        taskStr += "-task"
    if task[4]:
        taskStr += "-present"
    return taskStr


def get_stage_data(region):
    module_path = 'src.explore_task_data.hard_task.hard_task_' + str(region)
    stage_module = importlib.import_module(module_path)
    stage_data = getattr(stage_module, 'stage_data', None)
    return stage_data


def judge_need_fight(self, task):
    if task[2]:  # need_sss
        res = color.check_sweep_availability(self, True)
        if res == 'no-pass' or res == 'pass':
            return True
    if task[3]:  # need_task
        # TODO task verify
        return True
    if task[4]:  # need_present
        if color.judgeRGBFeature(self, 'hardTaskHasPresent'):
            return True
    return False


def choose_region(self, region):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
    self.logger.info("Current Region : " + str(cu_region))
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360, count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        hard_task.to_hard_event(self)
        cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
        self.logger.info("Current Region : " + str(cu_region))


def to_mission_info(self, y):
    rgb_possibles = {"event_hard": (1114, y)}
    img_ends = "normal_task_task-info"
    img_possibles = {'normal_task_select-area': (1114, y)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def calc_team_number(self, current_task_stage_data):
    pri = {
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
        for i in range(0, len(pri[attr])):
            possible_attr = pri[attr][i]
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
    tasklist.clear()
    self.logger.info("VALID TASK LIST [")
    for taskStr in str(self.config['explore_hard_task_list']).split(','):
        result = verify_and_add(self, taskStr)
        if not result[0]:
            self.logger.warning("Invalid task '%s',reason=%s" % (taskStr, result[1]))
            continue
    for task in tasklist:
        self.logger.info(task_to_string(task) + ",")
    self.logger.info("]")

    mission_los = [249, 363, 476]
    self.quick_method_to_main_page()
    hard_task.to_hard_event(self, False)

    for task in tasklist:
        region = task[0]
        mission = task[1]
        self.stage_data = get_stage_data(region)
        for key in self.stage_data:
            if key.startswith(str(region) + '-' + str(mission)):
                if task[2] and "sss" not in key:
                    continue
                if task[3] and "task" not in key:
                    continue
                if task[4] and "present" not in key:
                    continue
                current_task_stage_data = self.stage_data[key]
                if current_task_stage_data == "":
                    self.logger.warning("task '%s' not support" % (task_to_string(task)))
                    continue
                choose_region(self, region)
                to_mission_info(self, mission_los[mission - 1])
                if not judge_need_fight(self, task):
                    self.logger.warning("According to the mission info current mission no need fight")
                    hard_task.to_hard_event(self, False)
                else:
                    common_gird_method(self, current_task_stage_data)
                    main_story.auto_fight(self)
                    if self.config['manual_boss']:
                        self.click(1235, 41)
                    normal_task.to_normal_event(self)
                    hard_task.to_hard_event(self, False)
    return True
