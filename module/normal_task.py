import time

from core import color, stage, image
from core.color import check_sweep_availability

x = {
    'menu': (107, 9, 162, 36),
    'task-info': (578, 124, 702, 153),  # 任务信息弹窗
    'fight-task': (107, 9, 162, 36),  # 战斗任务弹窗
    'force-edit': (107, 9, 162, 36),  # 部队编辑界面
    'fight-skip': (1111, 531, 1136, 556),  # 跳过战斗
    'auto-over': (1072, 589, 1094, 611),  # 回合自动结束
    'force-1': (118, 548, 130, 564),
    'force-2': (118, 548, 130, 564),
    'force-3': (118, 548, 130, 564),
    'force-4': (118, 548, 130, 564),
    'box': (202, 531, 241, 570),  # 钻石宝箱
    'get-box': (614, 500, 666, 525),  # 获取宝箱
    'task-scan': (916, 218, 957, 237),  # 是否可以扫荡
    'side-quest': (360, 215, 401, 234),  # 支线任务
    'attack': (1126, 642, 1191, 670),  # 编队界面右下角出击
    'prize-confirm': (742, 642, 803, 668),  # 获得奖励确认按钮(支线通关)
    'task-finish': (1000, 648, 1063, 678),  # 任务完成确认按钮(主线通关)
    'no-pass': (198, 354, 220, 376),  # 未通关
    'move-force-confirm': (732, 483, 800, 516),  # 移动部队确认按钮
    'end-turn': (732, 483, 800, 516),  # 结束回合确认按钮
    'fight-task-info': (580, 83, 638, 113),  # 战斗过程中的任务信息弹窗
    'fail-confirm': (643, 637, 671, 676),  # 战斗失败确认按钮
    'mission-operating-task-info': (1000, 671, 1019, 679),  # 任务执行过程中任务信息(左下蓝色)
    'mission-operating-task-info-notice': (579, 81, 702, 116),  # 任务执行过程中任务信息(弹窗)
    'mission-pause': (583, 139, 707, 177),  # 中断任务
    'task-begin-without-further-editing-notice': (695, 334, 758, 365),  # 任务开始前不再编辑部队的提示
    'task-operating-round-over-notice': (598, 332, 708, 365),  # 任务执行过程中回合结束的提示
    'task-operating-feature': (13, 7, 67, 40),  # 任务执行过程中的特征（左上）
}


def implement(self):
    to_normal_event(self)
    if self.server == 'CN':
        cn_implement(self)
    elif self.server == 'Global':
        global_implement(self)


def cn_implement(self):
    if self.server == "CN":




def get_area_number(self):
    t1 = time.time()
    img = self.latest_img_array[182:213, 121:164, :]
    ocr_result = self.ocr.ocr_for_single_line(img)
    print(ocr_result)
    t2 = time.time()
    print("time2", t2 - t1)
    print("cur_num", ocr_result["text"])
    self.logger.info("cur_num" + ocr_result["text"])
    return int(ocr_result["text"])


def to_normal_event(self):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (1198, 580, 3),
            "main_page_bus": (823, 261, 3)
        }
        click_pos = [
            [805, 165],
        ]
        los = [
            "event_hard",
        ]
        image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time, pre_argv=(self, click_pos, los, ["event_normal"]))
    elif self.server == 'Global':
        click_pos = [
            [1077, 98],
            [805, 165],
            [1198, 580],
            [823, 261],
            [640, 116],
            [1129, 142],
            [919, 168],
            [887, 164],
            [887, 161],
            [887, 161],

        ]
        los = [
            "sweep_complete",
            "event_hard",
            "main_page",
            "campaign",
            "reward_acquired",
            "mission_info",
            "purchase_ap_notice",
            "start_sweep_notice",
            "charge_challenge_counts",
            "unlock_notice",
        ]
        ends = [
            "event_normal",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)


def to_hard_event(self):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (70, 232, 3),
            "main_page_bus": (823, 261, 3)
        }
        click_pos = [
            [1057, 165],
        ]
        los = [
            "event_normal",
        ]
        image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time(self, click_pos, los, ["event_hard"]))
    elif self.server == 'Global':
        click_pos = [
            [1077, 98],
            [1057, 165],
            [1198, 580],
            [823, 261],
            [640, 116],
            [1129, 142],
            [919, 168],
            [887, 164],
            [887, 161],
            [887, 161],
        ]
        los = [
            "sweep_complete",
            "event_normal",
            "main_page",
            "campaign",
            "reward_acquired",
            "mission_info",
            "purchase_ap_notice",
            "start_sweep_notice",
            "charge_challenge_counts",
            "unlock_notice",

        ]
        ends = [
            "event_hard",
        ]
        self.common_rgb_detect_method(click_pos, los, ends)


def to_mission_info(self, x, y):
    click_pos = [
        [x, y],
    ]
    los = [
        "event_normal"
    ]
    ends = [
        "mission_info",
        "unlock_notice"
    ]
    return self.common_rgb_detect_method(click_pos, los, ends)


def start_sweep(self):
    click_pos = [
        [941, 411],
        [765, 501]
    ]
    pd_los = [
        "mission_info",
        "start_sweep_notice"
    ]
    ends = [
        "skip_sweep_complete",
        "sweep_complete",
        "purchase_ap_notice",
        "charge_challenge_counts",
    ]
    return self.common_rgb_detect_method(click_pos, pd_los, ends)


def global_implement(self):
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    all_task_x_coordinate = 1118
    self.normal_task_count = self.config["normal_task_sweep_list"]
    self.hard_task_count = self.config["hard_task_sweep_list"]

    if len(self.normal_task_count) != 0:
        normal_task_y_coordinates = [0, 207, 283, 381, 477, 569]
        for i in range(0, len(self.normal_task_count)):
            to_normal_event(self)
            ap = self.get_ap()
            if ap == "UNKNOWN":
                self.logger.info("UNKNOWN AP")
                ap = 999
            else:
                ap = ap[0]
            self.logger.info("normal task" + str(self.normal_task_count[i]) + " begin")
            tar_mission = self.normal_task_count[i][0]
            tar_level = self.normal_task_count[i][1]
            tar_times = self.normal_task_count[i][2]
            if tar_times == "max":
                ap_needed = int(ap / 10) * 10
            else:
                ap_needed = tar_times * 10
            self.logger.info("ap_needed" + str(ap_needed))
            if ap_needed > ap:
                self.logger.info("INADEQUATE AP for task")
                return True

            cur_mission = get_area_number(self)
            while cur_mission != tar_mission:
                if cur_mission > tar_mission:
                    self.click(left_change_page_x, change_page_y, count=cur_mission - tar_mission, wait=False, rate=0.1)
                else:
                    self.click(right_change_page_x, change_page_y, count=tar_mission - cur_mission, wait=False,
                               rate=0.1)
                self.latest_img_array = self.get_screenshot_array()
                cur_mission = get_area_number(self)
                self.logger.info("now in mission " + str(cur_mission))

            self.logger.info("find target mission " + str(cur_mission))
            self.operation("click", (all_task_x_coordinate, normal_task_y_coordinates[tar_level]), duration=0.5)
            if to_mission_info(self, all_task_x_coordinate, normal_task_y_coordinates[tar_level]) == "unlock_notice":
                self.logger.info("task unlocked")
                continue
            t = check_sweep_availability(self.latest_img_array, server=self.server)
            if t == "AVAILABLE":
                if tar_times == "max":
                    if tar_times == "max":
                        self.click(1085, 300, rate=1, wait=False)
                    else:
                        self.click(1014, 300, count=tar_times - 1, wait=False, rate=1)
                res = start_sweep(self)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info(
                        "common task " + str(tar_times) + "-" + str(tar_level) + ": " + str(tar_times) + " finished",
                    )
                    if tar_times == "max":
                        return True
                if res == "purchase_ap_notice":
                    self.logger.info("INADEQUATE AP")
                    return True
            elif t == "UNAVAILABLE":
                self.logger.info("AUTO SWEEP UNAVAILABLE")
            to_normal_event(self)
        self.logger.info("common task finished")

    if len(self.hard_task_count) != 0:
        hard_task_y_coordinates = [0, 250, 360, 470]
        for i in range(0, len(self.hard_task_count)):
            self.logger.info("hard task" + str(self.hard_task_count[i]) + " begin")
            tar_mission = self.hard_task_count[i][0]
            tar_level = self.hard_task_count[i][1]
            tar_times = self.hard_task_count[i][2]
            to_hard_event(self)
            ap = self.get_ap()
            if ap == "UNKNOWN":
                self.logger.info("UNKNOWN AP")
                ap = 999
            else:
                ap = ap[0]
            if tar_times == "max":
                ap_needed = 60
            else:
                ap_needed = tar_times * 20
            self.logger.info("ap_needed" + str(ap_needed))
            if ap_needed > ap:
                self.logger.info("INADEQUATE AP for task")
                return True

            cur_mission = get_area_number(self)
            while cur_mission != tar_mission:
                if cur_mission > tar_mission:
                    self.click(left_change_page_x, change_page_y, count=cur_mission - tar_mission, wait=False, rate=0.1)
                else:
                    self.click(right_change_page_x, change_page_y, count=tar_mission - cur_mission, wait=False,
                               rate=0.1)
                self.latest_img_array = self.get_screenshot_array()
                cur_mission = get_area_number(self)
                self.logger.info("now in mission " + str(cur_mission))

            self.logger.info("find target mission " + str(cur_mission))
            self.click(all_task_x_coordinate, hard_task_y_coordinates[tar_level], wait=False)
            time.sleep(0.5)
            if to_mission_info(self, all_task_x_coordinate, hard_task_y_coordinates[tar_level]) == "unlock_notice":
                self.logger.info("task unlocked")
                continue
            t = check_sweep_availability(self.latest_img_array, server=self.server)
            if t == "sss":
                if tar_times == "max":
                    self.click(1085, 300, wait=False)
                    time.sleep(1)
                else:
                    self.click(1014, 300, count=tar_times - 1, wait=False)
                res = start_sweep(self)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info("hard task " + str(tar_times) + "-" + str(tar_level) +
                                     ": " + str(tar_times) + " finished")
                if res == "purchase_ap_notice":
                    self.logger.info("INADEQUATE AP")
                    return True
                if res == "charge_challenge_counts":
                    self.logger.info("INADEQUATE CHALLENGE COUNTS")
            elif t == "UNAVAILABLE":
                self.logger.info("AUTO SWEEP UNAVAILABLE")
        self.logger.info("hard task finished")

    self.logger.info("clear event power task finished")
    return True
