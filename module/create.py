import time

from core.utils import get_x_y, get_screen_shot_array
from gui.util import log


def implement(self):
    path5 = "./src/create/start_button_bright.png"
    path6 = "./src/create/start_button_grey.png"
    create_times = 3
    create_stop = False
    self.common_create_collect_operation()
    log.d("all creature collected", level=1, logger_box=self.loggerBox)
    while not create_stop:
        lox = 967
        loy = [273, 411, 548]
        collect = False
        tmp = min(create_times, 3)
        for i in range(0, tmp):
            self.click(lox, loy[i])
            if self.pd_pos() == "create":
                self.click(907, 206)
                time.sleep(0.2)
                img_shot = get_screen_shot_array()
                return_data1 = get_x_y(img_shot, path5)
                return_data2 = get_x_y(img_shot, path6)
                if return_data2[1][0] < 1e-03:
                    log.d("material inadequate", level=2, logger_box=self.loggerBox)
                    create_stop = True
                    break
                elif return_data1[1][0] < 1e-03:
                    log.d("create start", level=2, logger_box=self.loggerBox)
                    collect = True
                    self.click(return_data1[0][0], return_data1[0][1])
                    time.sleep(3.5)
                    node_x = [572, 508, 416, 302, 174]
                    node_y = [278, 388, 471, 529, 555]
                    choice = self.common_create_judge()
                    if choice is not None:
                        self.click(node_x[choice], node_y[choice])
                        time.sleep(0.5)
                        self.click(1123, 650)
                        time.sleep(3)
                        self.click(1123, 650)
                        time.sleep(8)
        create_times -= 3
        if create_times <= 0:
            create_stop = True
        self.to_main_page()
        self.main_to_page(12)
        if collect:
            self.common_create_collect_operation()
            log.d("all creature collected", level=1, logger_box=self.loggerBox)
