from core.utils import pd_rgb
import time

from gui.util import log


def implement(self):
    region_name = ["沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区"]
    self.schedule_pri = [1, 2, 3, 4, 5]
    self.schedule_times = self.config.get('schedulePriority')
    lo = [[307, 257], [652, 257], [995, 257],
          [307, 408], [652, 408], [995, 408],
          [307, 560], [652, 560], [985, 560]]
    cur_num = self.schedule_pri[0]
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360

    for i in range(0, len(self.schedule_pri)):
        tar_num = self.schedule_pri[i]
        log.d("begin schedule in [" + region_name[tar_num - 1] + "]", level=1, logger_box=self.loggerBox)
        while cur_num != tar_num:
            if cur_num > tar_num:
                self.operation("click@change_to_left", (left_change_page_x, change_page_y))
            else:
                self.operation("click@change_to_right", (right_change_page_x, change_page_y))
            cur_lo = self.operation("get_current_position", )
            if cur_lo[0:8] != "schedule":
                log.d("unexpected page :" + cur_lo, level=3, logger_box=self.loggerBox)
                return False
            cur_num = int(cur_lo[8:])
            log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
        self.operation("click", (1160, 664))
        if not self.common_positional_bug_detect_method("all_schedule", 1160, 664, 2):
            log.d("not in page all schedule , return", level=3, logger_box=self.loggerBox)
            return False

        self.operation("stop_getting_screenshot_for_location")
        for j in range(0, self.schedule_times[i]):
            shot = self.operation("get_screenshot_array")
            return_data1 = self.get_x_y(shot, "src/schedule/zero_ticket.png")
            print(return_data1)
            if return_data1[1][0] <= 1e-03:
                log.d("zero ticket", level=1, logger_box=self.loggerBox)
                self.operation("click", (1240, 39), duration=0.1)
                self.operation("click", (1240, 39), duration=0.1)
                self.operation("start_getting_screenshot_for_location")
                return True

            tmp = len(lo)
            res = []
            last_available = -1
            for i in range(0, tmp):
                if pd_rgb(shot, lo[i][0], lo[i][1], 250, 255, 250, 255, 250, 255):
                    res.append("available")
                    last_available = i
                elif pd_rgb(shot, lo[i][0], lo[i][1], 230, 249, 230, 249, 230, 249):
                    res.append("done")
                elif pd_rgb(shot, lo[i][0], lo[i][1], 140, 160, 140, 160, 140, 160):
                    res.append("lock")
                elif pd_rgb(shot, lo[i][0], lo[i][1], 190, 210, 190, 210, 190, 210):
                    res.append("no activity")

            log.d("schedule status: " + str(res), level=1, logger_box=self.loggerBox)

            if last_available == -1:
                break

            self.operation("click", (lo[last_available][0], lo[last_available][1]), duration=0.5)
            self.operation("click", (640, 556), 1)

            img_shot = self.operation("get_screenshot_array")
            return_data1 = self.get_x_y(img_shot, "src/schedule/zero_ticket_flag.png")
            print(return_data1)

            if return_data1[1][0] <= 1e-03:
                self.main_activity[7][1] = 1
                log.d("task schedule finished", level=1, logger_box=self.loggerBox)
                self.operation("click", (1240, 39), duration=0.1)
                self.operation("click", (1240, 39), duration=0.1)
                self.operation("click", (1240, 39), duration=0.1)
                self.operation("click", (1240, 39), duration=0.1)
                self.operation("start_getting_screenshot_for_location")
                return True

            time.sleep(4)
            self.operation("click", (1090, 170), duration=0.8)
            self.common_icon_bug_detect_method("src/schedule/all_schedule.png", 1090, 170, "all schedule", times=10,
                                               interval=1)
        self.operation("click", (680, 680))
        self.operation("start_getting_screenshot_for_location")
