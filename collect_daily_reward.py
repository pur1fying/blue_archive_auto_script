import log
import time
from screen_operation import screen_operate


class collect_all(screen_operate):
    def __init__(self):
        super().__init__()
        log.o_p("BEGIN COLLECTING REWARDS ", 1)
        self.to_work_task()
        self.collect()
        self.exitt()
        log.o_p("COLLECTING REWARDS OVER", 1)

    def to_work_task(self):
        path1 = "src/home_page/daily_work.png"
        self.clicker(path1)

    def collect(self):
        path1 = "src/collect_all/collect_all.png"
        self.clicker(path1)
        self.device.click(1,1)
        time.sleep(2)

    def exitt(self):
        path1 = "src/collect_all/exit.png"
        self.clicker(path1)


if __name__ == '__main__':
    t = collect_all()
