import unittest
from main import Main
from module.ExploreTasks.TaskUtils import to_mission_info, to_region, execute_grid_task, employ_units, \
    convert_team_config
from core import image, picture
from module.ExploreTasks.explore_task import validate_and_add_task
from module import normal_task, hard_task, main_story
from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet


# run command
# python -m unittest develop_tools/test/test_explore_hard_task.py

class TestExploreNormalTask(unittest.TestCase):
    def setUp(self):
        ocr_needed = ["Global", "NUM"]
        self.main = Main(ocr_needed=ocr_needed)

        # revise config dir to test different device
        conf = ConfigSet(config_dir="1708232489")

        self.baas_thread = Baas_thread(config=conf)
        self.baas_thread.init_all_data()
        self.baas_thread.ocr = self.main.ocr

        # revise the task list to test different tasks
        self.explore_hard_task_str = "1,2,3"
        self.logger = self.baas_thread.logger

    def test_explore_normal_task(self):
        tasklist = []

        for taskStr in str(self.explore_hard_task_str).split(","):
            result = validate_and_add_task(self.baas_thread, taskStr, tasklist, False)
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
            for taskDataName, taskData in task[2].items():
                taskName = str(region) + "-" + (str(mission) if mission != 6 else "A")
                self.logger.info(f"--- Start exploring H{taskName}({taskDataName}) ---")

                mission_los = [249, 363, 476]
                hard_task.to_hard_event(self.baas_thread, True)
                if not (to_region(self.baas_thread, region, False) and
                        to_mission_info(self.baas_thread, mission_los[mission - 1])):
                    self.logger.error(f"Skipping task {taskName} since it's not available.")
                    continue

                if not execute_grid_task(self.baas_thread, taskData):
                    self.logger.error(f"Skipping task {taskName} due to error.")
                    continue

                main_story.auto_fight(self.baas_thread)

                # skip unlocking animation by switching
                normal_task.to_normal_event(self.baas_thread, True)
                hard_task.to_hard_event(self.baas_thread, True)
        return True
