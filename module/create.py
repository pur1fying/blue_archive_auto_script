import time
from datetime import datetime
from core import color, image, picture


def implement(self):
    check_refresh_daily_create_times(self)
    use_acceleration_ticket = self.config['use_acceleration_ticket']
    left_create_times = self.config['createTime'] - self.config['alreadyCreateTime']
    self.logger.info("left create times: " + str(left_create_times) + " times")
    self.logger.info("use acceleration ticket : " + str(use_acceleration_ticket).upper())
    self.quick_method_to_main_page()
    res = to_manufacture_store(self, True)
    if res == "create_select-sub-node":
        common_create_judge(self)
        to_manufacture_store(self, True)
    status = receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket)
    y_position = {
        'CN': [312, 452, 594],
        'Global': [312, 452, 594],
        'JP': [288, 407, 534]
    }
    y_position = y_position[self.server]
    need_check_order_or_materials = True
    create_flag = True
    while self.flag_run and left_create_times > 0 and create_flag:
        if status == ["unfinished", "unfinished", "unfinished"] and (not use_acceleration_ticket):
            break
        need_acc_collect = False
        for i in range(0, len(status)):
            if status[i] == "empty":
                to_node1(self, y_position[i], True)
                if need_check_order_or_materials:
                    check_order_of_materials(self)
                    need_check_order_or_materials = False
                if not choose_materials(self):
                    create_flag = False
                    break
                need_acc_collect = True
                self.config['alreadyCreateTime'] += 1
                self.save_config()
                self.logger.info("today total create times: " + str(self.config['alreadyCreateTime']))
                if self.config['alreadyCreateTime'] >= self.config['createTime']:
                    create_flag = False
                    need_acc_collect = False
                self.click(1066, 664, wait=False, wait_over=True, duration=4)
                common_create_judge(self)
                to_manufacture_store(self)
        if need_acc_collect:
            status = receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket)
    get_next_execute_time(self, status)
    return True


def common_create_judge(self):
    # pri = ["花",
    #             "MomoFriends咖啡厅",
    #             "果冻游戏中心",
    #             "情人节",
    #             "夏日",
    #             "万圣节",
    #             "温泉浴场",
    #             "新年",
    #             "色彩",
    #             "灿烂",
    #             "武器部件",
    #             "铜",
    #             "光芒",
    #             "玲珑",
    #             "白金",
    #             "黄金",
    #             "白银",
    #             "金属",
    #             "隐然"]
    # pri = [
    #     "Flower",
    #     "Momo Friends Cafe Set",
    #     "Jellies Arcade Set",
    #     "Valentine's Set",
    #     "Summer Pool Party Set",
    #     "Jack-O-Lantern Cafe Set",
    #     "Hot Springs Resort Set",
    #     "New Year's House Set",
    #     "Military Campground Set",
    #     "Beachside Set",
    #     "Field Day Set",
    #     "Abydos Classroom Set",
    #     "Game Development Department Set",
    #     "Sunshine Resort Set",
    #     "Department Store Set",
    #     "Gehenna Party Set",
    #     "Colorful",
    #     "Radiant",
    #     "Platinum",
    #     "Weapon Parts",
    #     "Gold",
    #     "Silver",
    #     "Metal",
    #     "Copper",
    #     "Shiny",
    #     "Brilliant",
    #     "Subtle"
    # ],
    # pri = [
    #     "花弁",
    #     "モモフレンズのカフェシリーズ",
    #     "ゼリーズゲーセンシリーズ",
    #     "バレンタインシリーズ",
    #     "サマーリゾートシリーズ",
    #     "ハロウィーンカフェシリーズ",
    #     "伝統的な温泉郷シリーズ",
    #     "お正月シリーズ",
    #     "ミリタリーアウトドア",
    #     "ビーチサイドシリーズ",
    #     "大運動会シリーズ",
    #     "アビドス教室シリーズ",
    #     "ゲーム開発部シリーズ",
    #     "サンシャインリゾートシリーズ",
    #     "デパートシリーズ",
    #     "ゲヘナパーティーシリーズ",
    #     "色彩",
    #     "煌めき",
    #     "パーツ",
    #     "輝き",
    #     "铜",
    #     "金属",
    #     "銀",
    #     "金",
    #     "プラチナ",
    #     "明かり",
    #     "瞬き"
    # ]
    pri = self.config['createPriority']
    for i in range(0, len(pri)):
        pri[i] = preprocess_node_info(pri[i], self.server)
    node_x = [839, 508, 416, 302, 174]
    node_y = [277, 388, 471, 529, 555]
    node = []
    lo = []
    for i in range(0, 5):
        self.click(node_x[i], node_y[i], wait=False, wait_over=True)
        if i == 0:
            node_x[0] = 571
            node_y[0] = 278
        time.sleep(0.7 if i == 0 else 0.1)
        self.latest_img_array = self.get_screenshot_array()
        region = (815, 201, 1223, 275)
        node_info = preprocess_node_info(self.ocr.get_region_res(self.latest_img_array, region, self.server),
                                         self.server)
        for k in range(0, len(pri)):
            if pri[k] == node_info:
                if k == 0:
                    self.logger.info("choose node : " + pri[0])
                    return
                else:
                    node.append(pri[k])
                    lo.append(i)
    self.logger.info("detected nodes:" + str(node))
    for i in range(1, len(pri)):
        for j in range(0, len(node)):
            if node[j][0:len(pri[i])] == pri[i]:
                self.logger.info("choose node : " + pri[i])
                if lo[j] != 4:
                    self.click(node_x[lo[j]], node_y[lo[j]], wait=False, wait_over=True)
                    return


def to_manufacture_store(self, skip_first_screenshot=False):
    crafting_x = {
        'CN': 680,
        'Global': 680,
        'JP': 642,
    }
    rgb_possibles = {
        "main_page": (crafting_x[self.server], 650),
        'reward_acquired': (640, 100),
    }
    img_ends = [
        "create_crafting-list",
        "create_select-sub-node"
    ]
    img_possibles = {
        "create_start-crafting": (1115, 657),
        "create_start-crafting-notice": (769, 501),
        "create_select-node": (1115, 657),
    }
    return picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def check_crafting_list_status(self):
    y_position = {
        'CN': [312, 452, 594],
        'Global': [312, 452, 594],
        'JP': [288, 407, 534]
    }
    y_position = y_position[self.server]
    status = [None, None, None]
    for j in range(0, 3):
        if color.judge_rgb_range(self.latest_img_array, 1126, y_position[j], 90, 130, 200, 230, 245, 255):
            status[j] = "unfinished"
        elif color.judge_rgb_range(self.latest_img_array, 1126, y_position[j], 235, 255, 222, 255, 53, 93):
            status[j] = "finished"
        elif color.judge_rgb_range(self.latest_img_array, 1126, y_position[j], 222, 255, 222, 255, 222, 255):
            status[j] = "empty"
    return status


def receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket):
    while self.flag_run:
        status = check_crafting_list_status(self)
        self.logger.info("crafting list status: " + str(status))
        if ("unfinished" in status and use_acceleration_ticket) or "finished" in status:
            collect(self, status, use_acceleration_ticket)
        else:
            return status
        self.latest_img_array = self.get_screenshot_array()


def collect(self, status, use_acceleration_ticket):
    if self.server == 'JP':
        if "finished" in status:
            self.click(1126, 617, wait=False, wait_over=True, duration=1.5)
            self.click(640, 100, wait=False, wait_over=True, count=2)
            to_manufacture_store(self)
        if ("unfinished" in status) and use_acceleration_ticket:
            img_possibles = {"create_crafting-list": (1126, 617)}
            img_ends = "create_complete-instantly"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            img_possibles = {"create_complete-instantly": (766, 516)}
            img_ends = "create_crafting-list"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
        return
    y_position = {
        'CN': [312, 452, 594],
        'Global': [312, 452, 594],
    }
    y_position = y_position[self.server]
    for i in range(0, 3):
        if status[i] == "unfinished" and use_acceleration_ticket:
            img_possibles = {"create_crafting-list": (1126, y_position[i])}
            img_ends = "create_complete-instantly"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            img_possibles = {"create_complete-instantly": (766, 516)}
            img_ends = "create_crafting-list"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            status[i] = "finished"
        if status[i] == "finished":
            self.click(1126, y_position[i], wait=False, wait_over=True, duration=1.5)
            self.click(640, 100, wait=False, wait_over=True, count=2)
            to_manufacture_store(self)


def check_create_availability(img):
    if color.judge_rgb_range(img, 1112, 681, 210, 230, 210, 230, 210, 230):
        return "grey"
    elif color.judge_rgb_range(img, 1112, 681, 235, 255, 233, 253, 65, 85):
        return "bright"
    else:
        return "unknown"


def to_node1(self, y, skip_first_screenshot=False):
    img_possibles = {"create_crafting-list": (1153, y)}
    img_ends = "create_unlock-no1-grey"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def check_refresh_daily_create_times(self):
    now = datetime.now()
    day = now.day
    hour = now.hour
    last_refresh = datetime.fromtimestamp(self.config['createTimeLastRefreshTime'])
    last_refresh_day = last_refresh.day
    last_refresh_hour = last_refresh.hour
    if day == last_refresh_day and (hour < 4 and last_refresh_hour < 4) or (hour >= 4 and last_refresh_hour >= 4):
        return
    else:
        self.config['alreadyCreateTimes'] = 0
        self.config['createTimeLastRefreshTime'] = time.time()
        self.logger.info("refresh daily create times")
        self.save_config()


def check_order_of_materials(self):
    if not image.compare_image(self, "create_basic", 3, need_log=False, image=self.latest_img_array):
        self.logger.info("CHANGE SORT TO BASIC")
        img_possibles = {"create_unlock-no1-grey": (1109, 106)}
        img_ends = "create_sort"
        picture.co_detect(self, None, None, img_ends, img_possibles, True)
        if self.server == 'JP':
            self.click(138, 217, wait=False, wait_over=True, duration=0.3)
            self.click(299, 186, wait=False, wait_over=True, duration=0.3)
        else:
            self.click(168, 168, wait=False, wait_over=True, duration=0.3)
        img_possibles = {"create_sort": (766, 576)}
        img_ends = "create_unlock-no1-grey"
        picture.co_detect(self, None, None, img_ends, img_possibles, True)
    if image.compare_image(self, "create_point-down", 3, need_log=False, image=self.latest_img_array):
        self.logger.info("CHANGE order arrow from DOWN TO UP")
        self.click(1213, 104, wait=False, wait_over=True, duration=0.3)
    if image.compare_image(self, "create_point-up", 3, need_log=False, image=self.latest_img_array):
        self.logger.info("order arrow UP")


def choose_materials(self):
    self.click(907, 204, wait=False, wait_over=True, duration=0.3)
    self.latest_img_array = self.get_screenshot_array()
    res = check_create_availability(self.latest_img_array)
    if res == "bright":
        return True
    self.logger.info("material 1 inadequate check material 2")
    self.click(772, 304, wait=False, wait_over=True, count=10, duration=0.1)
    self.latest_img_array = self.get_screenshot_array()
    res = check_create_availability(self.latest_img_array)
    if res == "bright":
        return True
    self.logger.info("material 2 inadequate")
    return False


def preprocess_node_info(st, server):
    st = st.replace(" ", "")
    st = st.replace("・", "")
    if server == 'Global':
        st = st.lower()
        st = st.replace("’", "")
    return st


def get_next_execute_time(self, status):
    regions = {
        'CN': [(686, 278, 883, 327), (686, 419, 883, 469), (686, 561, 883, 614)],
        'Global': [(686, 278, 883, 327), (686, 419, 883, 469), (686, 561, 883, 614)],
        'JP': [(686, 252, 883, 302), (686, 374, 883, 422), (686, 498, 883, 547)]
    }
    regions = regions[self.server]
    time_deltas = []
    for i in range(0, 3):
        if status[i] == "unfinished":
            res = self.ocr.get_region_res(self.latest_img_array, regions[i], 'Global')
            if res.count(":") != 2:
                continue
            res = res.split(":")
            for j in range(0, len(res)):
                if res[i][0] == "0":
                    res[i] = res[i][1:]
            time_deltas.append(int(res[0]) * 3600 + int(res[1]) * 60 + int(res[2]))
    if time_deltas:
        self.next_time = min(time_deltas)
