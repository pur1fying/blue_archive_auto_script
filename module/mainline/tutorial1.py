from core import picture
from module import hard_task, normal_task


def sweep(self, times):
    for i in range(0, times):
        self.logger.info("tutorial " + str(i + 1) + " begin")
        self.swipe(919, 294, 919, 720, duration=0.1, post_sleep_time=1)
        img_possibles = {
            "normal_task_select-area": (1117, 339),
            "mainline_tutorial-task-info": (633, 508),
            "mainline_training-formation": (1153, 659),
            "mainline_tutorial": (640, 360)
        }
        picture.co_detect(self, None, {"fighting_feature": (-1, -1)}, "normal_task_fight-confirm", img_possibles, True, tentitive_click=True,
                          tentitivex=640, tentitivey=360, max_fail_cnt=1)
        hard_task.to_hard_event(self, True)
        normal_task.to_normal_event(self, True)

