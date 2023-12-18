import time

from core.utils import get_x_y, kmp,img_crop
from gui.util import log
from datetime import datetime


x = {
    'menu': (107, 9, 162, 36),
    'workshop': (418, 100, 436, 117),
    'view-all': (98, 103, 181, 122),
    'start-make2': (1054, 640, 1182, 669),
    'choose-node': (1054, 638, 1182, 669),
    'confirm-acc': (740, 466, 800, 493),

    'receive': (1102, 267, 1150, 290),
    'immediately': (1076, 267, 1124, 290),
    'start-make': (931, 303, 1015, 323)
}

def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    next_time = datetime(year, month, day+1, 4)
    return next_time.timestamp()


def common_create_collect_operation(self):
    self.operation("stop_getting_screenshot_for_location")

    self.latest_img_array = self.operation("get_screenshot_array")
    path2 = "./src/create/collect.png"
    path3 = "./src/create/finish_instantly.png"
    return_data1 = get_x_y(self.latest_img_array, path2)
    return_data2 = get_x_y(self.latest_img_array, path3)
    print(return_data1)
    print(return_data2)
    while return_data1[1][0] < 1e-02 or return_data2[1][0] < 1e-02:
        if return_data1[1][0] < 0.01:
            log.d("collect finished creature", level=1, logger_box=self.loggerBox)
            self.operation("click@collect", (return_data1[0][0], return_data1[0][1]), duration=2)
            self.operation("click@anywhere", (628, 665), duration=0.5)
        if return_data2[1][0] < 0.01:
            log.d("accelerate unfinished creature", level=1, logger_box=self.loggerBox)
            self.operation("click@accelerate", (return_data2[0][0], return_data2[0][1]), duration=0.5)
            self.operation("click@confirm", (755, 477), duration=0.5)
            self.operation("click@collect", (return_data2[0][0], return_data2[0][1]), duration=2)
            self.operation("click@anywhere", (628, 665), duration=0.5)
        self.latest_img_array = self.operation("get_screenshot_array")
        return_data1 = get_x_y(self.latest_img_array, path2)
        return_data2 = get_x_y(self.latest_img_array, path3)

    self.operation("start_getting_screenshot_for_location")


def common_create_judge(self):
    pri = ["花","Mo","桃桃","万圣节","情人节","果冻","色彩","灿烂","光芒","玲珑","白金","黄金","铜","白银","金属","隐然"]  # 可设置参数，越靠前的节点在制造时越优先选择
    node_x = [839, 508, 416, 302, 174]
    node_y = [277, 388, 471, 529, 555]
    # 572 278
    node = []
    lo = []
    for i in range(0, 5):
        self.operation("click", (node_x[i], node_y[i]))
        time.sleep(0.5 if i == 0 else 0.1)
        node_info = self.img_ocr(img_crop(self.operation("get_screenshot_array"),734,1123,207,277))
        for k in range(0, len(pri)):
            if kmp(pri[k], node_info) > 0:
                if k == 0:
                    log.d("choose node :" + pri[0], level=1, logger_box=self.loggerBox)
                    return i
                else:
                    node.append(pri[k])
                    lo.append(i)
    log.d("detected nodes:" + str(node), 1, logger_box=self.loggerBox)
    for i in range(1, len(pri)):
        for j in range(0, len(node)):
            if node[j][0:len(pri[i])] == pri[i]:
                log.d("choose node :" + pri[i], level=1, logger_box=self.loggerBox)
                return lo[j]


def implement(self):
    path5 = "../src/create/start_button_bright.png"
    path6 = "../src/create/start_button_grey.png"
    create_times = int(self.config.get('createTime')) #** 制造次数 请确保有加速券
    create_stop = False
    common_create_collect_operation(self)
    log.d("all creature collected", level=1, logger_box=self.loggerBox)
    while not create_stop:
        log.d("left create times: " + str(create_times), level=1, logger_box=self.loggerBox)
        lox = 1109
        loy = [273, 411, 548]
        collect = False
        tmp = min(create_times, 3)
        for i in range(0, tmp):
            log.d("begin create, time: " + str(i + 1), level=1, logger_box=self.loggerBox)
            self.operation("click", (lox, loy[i]))
            if not self.common_positional_bug_detect_method("create", lox, loy[i], 2):
                return False
            self.operation("click@material 2", (920, 206), duration=0.3)
            self.latest_img_array = self.operation("get_screenshot_array")
            return_data1 = get_x_y(self.latest_img_array, path5)
            return_data2 = get_x_y(self.latest_img_array, path6)
            print(return_data1)
            print(return_data2)
            if return_data2[1][0] < 1e-03:
                log.d("material 2 INADEQUATE,try material 1", level=1, logger_box=self.loggerBox)
                for x in range(0, 10):
                    self.operation("click@material 1", (755, 206))

                self.latest_img_array = self.operation("get_screenshot_array")
                return_data1 = get_x_y(self.latest_img_array, path5)
                return_data2 = get_x_y(self.latest_img_array, path6)
                print(return_data1)
                print(return_data2)
                if return_data2[1][0] < 1e-03:
                    log.d("material 1 INADEQUATE,EXIT create task", level=2, logger_box=self.loggerBox)
                    self.next_execute_time_queue.put(["create", get_next_execute_tick()])
                    return True
            if return_data1[1][0] < 1e-03:
                collect = True
                self.operation("click@start_create", (return_data1[0][0], return_data1[0][1]))
                time.sleep(3.5)
                node_x = [572, 508, 416, 302, 174]
                node_y = [278, 388, 471, 529, 555]
                choice = common_create_judge(self)
                if choice is not None:
                    self.operation("click", (node_x[choice], node_y[choice]), duration=0.5)
                    self.operation("click", (1123, 650), duration=3)
                    self.operation("click", (1123, 650), duration=4)
                    if not self.common_positional_bug_detect_method("manufacture_store", 1123, 650):
                        return False
            else:
                log.d("Can't detect start button,exit create task", level=2, logger_box=self.loggerBox)
                return
        create_times -= 3
        if create_times <= 0:
            create_stop = True
        if collect:
            self.main_to_page(12)
            common_create_collect_operation(self)
            log.d("all creature collected", level=1, logger_box=self.loggerBox)

    self.next_execute_time_queue.put(["create", get_next_execute_tick()])
    return True
