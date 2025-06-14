from copy import deepcopy

from core import picture, Baas_thread, image
from core.color import check_sweep_availability
from core.config.config_set import ConfigSet
from module.ExploreTasks.TaskUtils import to_hard_event, to_mission_info, to_region, to_normal_event


def print_task_list(self: Baas_thread, tasklist: list[list], title: str, isNormal: bool) -> None:
    current_ap = self.get_ap(True)
    self.logger.info(title + " {")
    ap_required = 0
    for task in tasklist:
        base_ap = 10 if isNormal else 20

        taskName = f"{task[0]}-{task[1]}" if isNormal else f"H{task[0]}-{task[1]}"
        required_count = task[2]
        if required_count == "max":
            required_count = (current_ap - ap_required) // base_ap if isNormal else (
                min(3, (current_ap - ap_required) // base_ap))
        ap_required += required_count * base_ap
        self.logger.info(f"\t - {taskName} * {task[2]} time(s),using {required_count * base_ap} AP.")
    self.logger.info("},requiring " + str(ap_required) + " AP.")


def sweep_hard_task(self: Baas_thread):
    self.to_main_page(skip_first_screenshot=True)
    tasklist = deepcopy(self.config.unfinished_hard_tasks)
    base_ap = 20
    print_task_list(self, tasklist, "Sweeping HARD task list", False)
    for i in range(len(tasklist)):
        task = tasklist[i]
        # task[0] : target region
        # task[1] : target mission
        # task[2] : sweep times (if it's "max",it means maximum possible,which is 3 for hard task)

        region, mission, required_counts = task[0], task[1], task[2]
        current_ap = self.get_ap(True)

        self.logger.info(f"--- Start sweeping H{region}-{mission} * {required_counts} time(s)---")

        # Check if the AP is enough for sweeping
        # As for "max" task, it will always bypass check
        if current_ap < base_ap or (required_counts is int and required_counts * base_ap > current_ap):
            self.logger.warning(f"Exiting sweeping since AP is insufficient.")
            print_task_list(self, tasklist[i:], "Remain HARD tasks list", False)
            return True

        # Check if the task is available for sweeping
        to_hard_event(self, True)
        mission_los = [249, 363, 476]
        if not (to_region(self, region, False) and to_mission_info(self, mission_los[mission - 1])
                and check_sweep_availability(self, True) == "sss"):
            self.logger.error(f"Skipping task {region}-{mission} since it's not available.")
            continue

        button_y_coord = 300 if self.server == "CN" else 328
        if required_counts == "max":
            self.click(1085, button_y_coord, rate=1, wait_over=True)
        else:
            duration = 0 if required_counts <= 4 else 1
            self.click(1014, button_y_coord, count=required_counts - 1, duration=duration, wait_over=True)
        result = start_sweep(self, True)
        if result == "inadequate_ap":
            self.logger.warning("Current AP Insufficient")
            return True
        if result == "charge_challenge_counts":
            self.logger.warning("Current Task Challenge Counts Insufficient")
        self.config.unfinished_hard_tasks.pop(0)
        self.config_set.set('unfinished_hard_tasks', self.config.unfinished_hard_tasks)
        if required_counts == "max":
            self.logger.info("Exit task sweep since \"max\" uses up all ap.")
            return True
        to_hard_event(self, True)
    return True


def sweep_normal_task(self):
    self.to_main_page(skip_first_screenshot=True)
    tasklist = deepcopy(self.config.unfinished_normal_tasks)

    print_task_list(self, tasklist, "Sweeping NORMAL task list", True)
    for i in range(len(tasklist)):
        task = tasklist[i]
        # task[0] : target region
        # task[1] : target mission
        # task[2] : sweep times (if it's "max",it means maximum possible,which is 3 for hard task)

        region, mission, required_counts = task[0], task[1], task[2]
        current_ap = self.get_ap()
        base_ap = 10
        self.logger.info(f"--- Start sweeping {region}-{mission} * {required_counts} time(s)---")

        # Check if the AP is enough for sweeping
        # As for "max" task, it will always bypass check
        if current_ap < base_ap or (required_counts is int and required_counts * base_ap > current_ap):
            self.logger.warning(f"Exiting sweeping since AP is insufficient.")
            print_task_list(self, tasklist[i:], "Remain NORMAL task list", False)
            return True

        # Check if the task is available for sweeping
        to_normal_event(self, True)

        if not to_region(self, region, True):
            self.logger.error(f"Skipping task {region}-{mission} since it's not available.")
            continue
        fullMissionList = []
        for j in range(1, 6):
            fullMissionList.append(f"{region}-{j}")
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
            self.logger.error(f"Skipping task {region}-{mission} since it's not available.")
            continue

        button_y_coord = 300 if self.server == "CN" else 328
        if required_counts == "max":
            self.click(1085, button_y_coord, rate=1, wait_over=True)
        else:
            duration = 0 if required_counts <= 4 else 1
            self.click(1014, button_y_coord, count=required_counts - 1, duration=duration, wait_over=True)
        result = start_sweep(self, True)
        if result == "inadequate_ap":
            self.logger.warning("Current AP Insufficient")
            return True
        self.config.unfinished_normal_tasks.pop(0)
        self.config_set.set('unfinished_normal_tasks', self.config.unfinished_normal_tasks)
        if required_counts == "max":
            self.logger.info("Exit task sweep since \"max\" uses up all ap.")
            return True
        to_normal_event(self, True)
    return True


def start_sweep(self: Baas_thread, skip_first_screenshot: bool = False) -> str:
    img_ends = [
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
        "normal_task_start-sweep-notice",
        "normal_task_charge-challenge-counts",
    ]
    img_possibles = {"normal_task_task-info": (941, 411)}
    res = picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
    if res == "purchase_ap_notice-localized" or res == "purchase_ap_notice":
        return "inadequate_ap"
    if res == "normal_task_charge-challenge-counts":
        return "charge_challenge_counts"
    rgb_possibles = {"level_up": (640, 200)}
    img_ends = [
        "normal_task_skip-sweep-complete",
        "normal_task_sweep-complete",
    ]
    img_possibles = {"normal_task_start-sweep-notice": (765, 501)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
    return "sweep_complete"


def read_task(task_string: str, is_normal: bool) -> tuple:
    type_str = "normal task" if is_normal else "hard task"
    if task_string.count('-') != 2:
        raise ValueError(f"[\"{task_string}\"] -{type_str} format error,"
                         f" expected format: region-mission-counts(int or \"max\")")
    available_missions = list(range(1, 6)) if is_normal else list(range(1, 4))
    maximum_region = ConfigSet.static_config.explore_normal_task_region_range[1] if is_normal else \
        ConfigSet.static_config.explore_hard_task_region_range[1]
    mainline_available_regions = list(range(1, maximum_region + 1))
    temp = task_string.split('-')
    try:
        region, mission, counts = int(temp[0]), int(temp[1]), temp[2]
        if counts != "max":
            # if the counts is not "max", it must be an integer.
            # so we parse it to an integer, otherwise it would raise a ValueError
            counts = int(counts)
    except ValueError:
        raise ValueError(f"[\"{task_string}\"] - arguments are not integer or \"max\"")

    if region not in mainline_available_regions:
        raise ValueError(f"[\"{task_string}\"] - {type_str} region {region} is not support")
    if mission not in available_missions:
        raise ValueError(f"[\"{task_string}\"] - {type_str} mission {mission} is not support")

    return region, mission, counts
