import log
from screen_operation import screen_operate


class schedule(screen_operate):
    def __init__(self):
        super().__init__()
        log.o_p("BEGIN COLLECTING REWARDS ", 1)
        self.__to_schedule__()

        log.o_p("COLLECTING REWARDS OVER", 1)

    def __to_schedule__(self):
        path1 = "src/home_page/schedule.png"
        self.clicker(path1)


if __name__ == '__main__':
    t = schedule()