import module.ExploreTasks.TaskUtils
from core import picture
from module.ExploreTasks import normal_task, sweep_task


def sweep(self, times):
    for i in range(0, times):
        self.logger.info("tutorial " + str(i + 1) + " begin")
        self.swipe(919, 294, 919, 720, duration=0.1, post_sleep_time=1)
        img_possibles = {
            "mainline_tutorial-task-info": (633, 508),
            "mainline_training-formation": (1153, 659),
            "mainline_tutorial": (640, 360)
        }
        rgb_reactions = {
            "fighting_feature": (-1, -1),
            "event_normal": (1117, 339)
        }
        picture.co_detect(self, None, rgb_reactions, "normal_task_fight-confirm", img_possibles, True, tentative_click=True,
                          tentative_x=640, tentative_y=360, max_fail_cnt=1)
        module.ExploreTasks.TaskUtils.to_hard_event(self, True)
        module.ExploreTasks.TaskUtils.to_normal_event(self, True)

