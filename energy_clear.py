from screen_operation import Operation, get_x_y
import log


class clear_energy(Operation):
    def __init__(self, road=None, railway=None, church=None):
        super().__init__()
        log.o_p("BEGIN CLEARING ENERGY")
        self.to_main_event()
        self.to_rewarded_task()
        self.solve_rewarded_task(road, railway, church)
        log.o_p("CLEARING ENERGY DONE")

    def to_main_event(self):
        path = "src/home_page/main_event.png"
        self.clicker(path, 0, 0)  # 意外实参：5

    def to_rewarded_task(self):
        path = "src/clear_energy/rewarded task/rewarded_task.png"
        self.clicker(path, 0, 0)  # 意外实参：2

    def common_rewarded_task_click(self, difficulty=None, task=None):
        if (difficulty is not None) and (task is not None):
            path1 = "src/clear_energy/rewarded task/" + task + ".png"
            self.clicker(path1, 0, 0)  # 意外实参：3
            path2 = "src/clear_energy/rewarded task/" + difficulty + ".png"
            self.clicker(path2, 352, 0)
            shot_path = self.get_screen_shot_path()
            path3 = "src/clear_energy/rewarded task/add_button.png"
            lo = get_x_y(shot_path, path3)
            for i in range(0, 5):
                self.device.click(lo[0], lo[1])

    def solve_rewarded_task(self, road, railway, church):
        if road is not None:
            self.common_rewarded_task_click(road, "road")
        if railway is not None:
            self.common_rewarded_task_click(railway, "railway")
        if church is not None:
            self.common_rewarded_task_click(church, "church")


if __name__ == '__main__':
    t = clear_energy("A", "A", "A")
