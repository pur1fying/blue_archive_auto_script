from copy import deepcopy

from core import picture, Baas_thread
from core.color import check_sweep_availability
from core.staticUtils import isInt
from module.ExploreTasks.TaskUtils import to_hard_event, to_mission_info, to_region, to_normal_event


def printTaskList(self: Baas_thread, tasklist: list[list], title: str, isNormal: bool) -> None:
    current_ap = self.get_ap(True)
    self.logger.info(title + " {")
    ap_required = 0
    for task in tasklist:
        if isNormal:
            base_ap = 10 if task[0] != "tutorial" else 1
        else:
            base_ap = 20

        taskName = f"{task[0]}-{task[1]}" if isNormal else f"H{task[0]}-{task[1]}"
        required_count = task[2]
        if required_count == "max":
            required_count = current_ap // base_ap if isNormal else min(3, current_ap // base_ap)
        ap_required += required_count * base_ap
        self.logger.info(f"\t - {taskName} * {task[2]} time(s),using {required_count * base_ap} AP.")
    self.logger.info("},requiring " + str(ap_required) + " AP.")


def sweepHardTask(self):
    tasklist = deepcopy(self.config.unfinished_hard_tasks)
    base_ap = 20
    printTaskList(self, tasklist, "SWEEPING TASKS LIST", False)

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
        if current_ap < base_ap or (type(required_counts) == int and required_counts * base_ap > current_ap):
            self.logger.warning(f"Exiting sweeping since AP is insufficient.")
            printTaskList(self, tasklist[i:], "REMAIN TASKS LIST", False)
            return True

        # Check if the task is available for sweeping
        to_hard_event(self, True)
        mission_los = [249, 363, 476]
        if not (to_region(self, region, False) and to_mission_info(self, mission_los[mission - 1])
                and check_sweep_availability(self, True) == "sss"):
            self.logger.error(f"Skipping task {region}-{mission} since it's not available.")
            continue

        botton_y_coord = 300 if self.server == "CN" else 328
        if required_counts == "max":
            self.click(1085, botton_y_coord, rate=1, wait_over=True)
        else:
            duration = 0 if required_counts <= 4 else 1
            self.click(1014, botton_y_coord, count=required_counts - 1, duration=duration, wait_over=True)
        result = start_sweep(self, True)
        if result == "charge_challenge_counts":
            self.logger.warning("Current Task Challenge Counts Insufficient")
        to_hard_event(self, True)

    return True


def sweepNormalTask(self):
    tasklist = deepcopy(self.config.unfinished_normal_tasks)
    printTaskList(self, tasklist, "SWEEPING TASKS LIST", True)

    for i in range(len(tasklist)):
        task = tasklist[i]
        # task[0] : target region
        # task[1] : target mission
        # task[2] : sweep times (if it's "max",it means maximum possible,which is 3 for hard task)

        region, mission, required_counts = task[0], task[1], task[2]
        current_ap = self.get_ap(True)
        base_ap = 10 if region != "tutorial" else 1
        self.logger.info(f"--- Start sweeping {region}-{mission} * {required_counts} time(s)---")

        # Check if the AP is enough for sweeping
        # As for "max" task, it will always bypass check
        if current_ap < base_ap or (type(required_counts) == int and required_counts * base_ap > current_ap):
            self.logger.warning(f"Exiting sweeping since AP is insufficient.")
            printTaskList(self, tasklist[i:], "REMAIN TASKS LIST", False)
            return True

        # Check if the task is available for sweeping
        to_normal_event(self, True)

        # if the task is a tutorial, we transfer the task to the corresponding module
        if region == "tutorial":
            tutorial_region = [0, 1, 1, 1, 2, 3, 3]
            to_region(self, tutorial_region[mission], True)
            import importlib
            module_name = "module.mainline.tutorial" + str(mission)
            module = importlib.import_module(module_name)
            module.sweep(self, required_counts)
            continue

        if not to_region(self, region, True):
            self.logger.error(f"Skipping task {region}-{mission} since it's not available.")
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
            self.logger.error(f"Skipping task {region}-{mission} since it's not available.")
            continue

        botton_y_coord = 300 if self.server == "CN" else 328
        if required_counts == "max":
            self.click(1085, botton_y_coord, rate=1, wait_over=True)
        else:
            duration = 0 if required_counts <= 4 else 1
            self.click(1014, botton_y_coord, count=required_counts - 1, duration=duration, wait_over=True)
        result = start_sweep(self, True)
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


def readOneHardTask(task_string, region):
    if task_string.count('-') != 2:
        raise ValueError("[ " + task_string + " ] format error.")
    mainline_available_missions = list(range(1, 4))
    mainline_available_regions = list(range(region[0], region[1] + 1))
    temp = task_string.split('-')
    region = temp[0]
    mission = temp[1]
    counts = temp[2]
    if not isInt(region):
        raise ValueError("[ " + task_string + " ] region : " + str(region) + " unavailable")
    region = int(region)
    if region not in mainline_available_regions:
        raise ValueError("[ " + task_string + " ] region : " + str(region) + " not support")
    if not isInt(mission):
        raise ValueError("[ " + task_string + " ] mission : " + str(mission) + " unavailable")
    mission = int(mission)
    if mission not in mainline_available_missions:
        raise ValueError("[ " + task_string + " ] mission : " + str(mission) + " not support")
    if not isInt(counts):
        if counts != "max":
            raise ValueError("[ " + task_string + " ] count : " + str(counts) + " unavailable")
    else:
        counts = int(counts)
    return region, mission, counts


def readOneNormalTask(task_string, region):
    if task_string.count('-') != 2:
        raise ValueError("[ " + task_string + " ] format error.")
    mainline_available_missions = list(range(1, 6))
    mainline_available_regions = list(range(5, region[1] + 1))
    mainline_available_regions.append("tutorial")
    temp = task_string.split('-')
    region = temp[0]
    mission = temp[1]
    counts = temp[2]
    if not isInt(region):
        if region != "tutorial":
            raise ValueError("[ " + task_string + " ] region : " + str(region) + " unavailable")
    else:
        region = int(region)
    if region not in mainline_available_regions:
        raise ValueError("[ " + task_string + " ] region : " + str(region) + " not support")
    if not isInt(mission):
        raise ValueError("[ " + task_string + " ] mission : " + str(mission) + " unavailable")
    mission = int(mission)
    if mission not in mainline_available_missions:
        raise ValueError("[ " + task_string + " ] mission : " + str(mission) + " not support")
    if not isInt(counts):
        if counts != "max":
            raise ValueError("[ " + task_string + " ] count : " + str(counts) + " unavailable")
    else:
        counts = int(counts)
    return region, mission, counts
