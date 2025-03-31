import unittest
from main import Main
from module.ExploreTasks.TaskUtils import to_mission_info, to_region, execute_grid_task, employ_units, convert_team_config
from core import image, picture
from module.ExploreTasks.explore_task import validate_and_add_task
from module import normal_task, hard_task, main_story
from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet


# run command
# python -m unittest develop_tools/test/test_explore_normal_task.py

class TestExploreNormalTask(unittest.TestCase):
    def setUp(self):
        ocr_needed = ["Global", "NUM"]
        self.main = Main(ocr_needed=ocr_needed)
        conf = ConfigSet(config_dir="1708232489")
        self.baas_thread = Baas_thread(config=conf)
        self.baas_thread.init_all_data()
        self.baas_thread.ocr = self.main.ocr

        # revise the task list to test different tasks
        self.explore_normal_task_str = "5"

        self.logger = self.baas_thread.logger

    def test_explore_normal_task(self):
        tasklist = []
        for taskStr in self.explore_normal_task_str.split(","):
            result = validate_and_add_task(self.baas_thread, taskStr, tasklist, True)
            if not result[0]:
                self.logger.warning("Invalid task '%s',reason=%s" % (taskStr, result[1]))
                continue
        self.logger.info("VALID TASK LIST {")
        for task in tasklist:
            taskName = str(task[0]) + "-" + (str(task[1]) if task[1] != 6 else "A")
            for taskDataName, taskData in task[2].items():
                self.logger.info(f"\t - {taskName}({taskDataName})")
        self.logger.info("}")

        self.assertLess(0, len(tasklist)
                        , "No valid task found in the task list, please check the task list")
        teamConfig = convert_team_config(self.baas_thread)

        for task in tasklist:
            region = task[0]
            mission = task[1]

            # skip navigate to mission if previous task is already finished

            for taskDataName, taskData in task[2].items():
                taskName = str(region) + "-" + (str(mission) if mission != 6 else "A")
                self.logger.info(f"--- Start exploring {taskName}({taskDataName}) ---")

                normal_task.to_normal_event(self.baas_thread, True)
                if not to_region(self.baas_thread, region, True):
                    self.logger.error(f"Skipping task {taskName} since it's not available.")
                    continue
                fullMissionList = []
                for i in range(1, 6):
                    fullMissionList.append(f"{region}-{i}")
                if region % 3 == 0:
                    fullMissionList.append(f"{region}-A")
                missionButtonPos = image.swipe_search_target_str(
                    self.baas_thread,
                    "normal_task_enter-task-button",
                    (1055, 191, 1201, 632),
                    0.8,
                    fullMissionList,
                    mission - 1,
                    (917, 552, 917, 220, 0.2, 1.0),
                    'Global',
                    (-396, -7, 60, 33),
                    None,
                    3
                )
                if not to_mission_info(self.baas_thread, missionButtonPos[1]):
                    self.logger.error(f"Skipping task {taskName} since it's not available.")
                    continue

                # TODO: sub mission must be broken :D
                if mission == 6 or mission == 'sub':
                    # to formation menu
                    img_reactions = {
                        'normal_task_task-A-info': (946, 540)
                    }
                    img_ends = "normal_task_formation-menu"
                    picture.co_detect(self.baas_thread, img_ends=img_ends, img_reactions=img_reactions, skip_first_screenshot=True)

                    # get preset unit
                    if not employ_units(self.baas_thread, taskData, teamConfig):
                        self.logger.error(f"Skipping task {taskName} due to error.")
                        continue

                    main_story.auto_fight(self.baas_thread)
                else:
                    if not execute_grid_task(self.baas_thread, taskData):
                        self.logger.error(f"Skipping task {taskName} due to error.")
                        continue

                    main_story.auto_fight(self.baas_thread)
                # skip unlocking animation by switching
                hard_task.to_hard_event(self.baas_thread, True)
                normal_task.to_normal_event(self.baas_thread, True)
        return True


