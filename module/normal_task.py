import time

from core import color, stage, image
from core.color import check_sweep_availability

x = {
    'charge-challenge-counts': (495, 348, 599, 381),  # 购买挑战次数
    'unlock-notice': (607, 144, 676, 176),  # 解锁提示
    'start-sweep-notice': (607, 144, 676, 176),  # 开始扫荡提示
    'sweep-complete': (601, 561, 682, 604),  # 扫荡完成
    'skip-sweep-complete': (597, 488, 684, 531),  # 跳过扫荡完成
    'menu': (107, 9, 162, 36),
    'task-info': (578, 124, 702, 153),  # 任务信息弹窗
    'fight-task': (107, 9, 162, 36),  # 战斗任务弹窗
    'force-edit': (107, 9, 162, 36),  # 部队编辑界面
    'fight-skip': (1111, 531, 1136, 556),  # 跳过战斗
    'auto-over': (1072, 589, 1094, 611),  # 回合自动结束
    'side-quest': (360, 215, 401, 234),  # 支线任务
    'attack': (1126, 642, 1191, 670),  # 编队界面右下角出击
    'prize-confirm': (742, 642, 803, 668),  # 获得奖励确认按钮(支线通关)
    'task-finish': (1000, 648, 1063, 678),  # 任务完成确认按钮(主线通关)
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
    'help': (597, 111, 675, 150)
}


def read_task(self, task_string):
    try:
        region = 0
        mainline_available_missions = [1, 2, 3, 4, 5]
        mainline_available_regions = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
        for i in range(0, len(task_string)):
            if task_string[i].isdigit():
                region = region * 10 + int(task_string[i])
            else:
                if region not in mainline_available_regions:
                    self.logger.info("detected region " + str(region) + " unavailable")
                    return False
                mission = 0
                for j in range(i, len(task_string)):
                    if task_string[j].isdigit():
                        mission = int(task_string[j])
                        if mission not in mainline_available_missions:
                            self.logger.info("detected mission " + str(mission) + " unavailable")
                            return False
                        else:
                            counts = task_string[j + 2:]
                            if counts == "max":
                                return region, mission, "max"
                            else:
                                if int(counts) <= 0:
                                    self.logger.info("detected counts " + str(counts) + " unavailable")
                                    return False
                                return region, mission, int(counts)

                if mission == 0:
                    self.logger.info("no mission detected")
                    return False
    except Exception as e:
        self.logger.info("task string format error")
        return False


def implement(self):
    self.normal_task_count = []
    temp = self.config['mainlinePriority']
    if type(temp) == str:
        temp = temp.split(',')
    for i in range(0, len(temp)):
        if read_task(self, temp[i]):
            self.normal_task_count.append(read_task(self, temp[i]))
    self.logger.info("detected normal task list: " + str(self.normal_task_count))
    all_task_x_coordinate = 1118
    if len(self.normal_task_count) != 0:
        normal_task_y_coordinates = [242, 341, 439, 537, 611]
        for i in range(0, len(self.normal_task_count)):
            to_normal_event(self)
            ap = self.get_ap()
            if ap == "UNKNOWN":
                self.logger.info("UNKNOWN AP")
                ap = 999
            else:
                ap = ap[0]
            self.logger.info("normal task " + str(self.normal_task_count[i]) + " begin")
            tar_region = self.normal_task_count[i][0]
            tar_mission = self.normal_task_count[i][1]
            tar_times = self.normal_task_count[i][2]
            if tar_times == "max":
                ap_needed = int(ap / 10) * 10
            else:
                ap_needed = tar_times * 10
            self.logger.info("ap_needed : " + str(ap_needed))
            if ap_needed > ap:
                self.logger.info("INADEQUATE AP for task")
                return True
            choose_region(self, tar_region)
            self.swipe(917, 220, 917, 552, duration=0.1)
            time.sleep(1)
            if to_task_info(self, all_task_x_coordinate, normal_task_y_coordinates[tar_mission - 1]) == "unlock_notice":
                self.logger.info("task unlocked")
                continue
            t = check_sweep_availability(self.latest_img_array, server=self.server)
            if t == "sss":
                if tar_times == "max":
                    self.click(1085, 300, rate=1, wait=False)
                else:
                    self.click(1014, 300, count=tar_times - 1, wait=False, duration=1)
                res = start_sweep(self)
                if res == "sweep_complete" or res == "skip_sweep_complete":
                    self.logger.info("common task " + str(self.normal_task_count[i]) + " finished")
                    if tar_times == "max":
                        return True
                elif res == "purchase_ap_notice":
                    self.logger.info("INADEQUATE AP")
                    return True
            elif t == "pass" or t == "no-pass":
                self.logger.info("AUTO SWEEP UNAVAILABLE")

            to_normal_event(self)
        self.logger.info("common task finished")

    return True


def to_normal_event(self):
    if self.server == 'CN':
        possibles = {
            "main_page_home-feature": (1198, 580),
            "main_page_bus": (823, 261),
            "normal_task_sweep-complete": (643, 585),
            "normal_task_start-sweep-notice": (887, 164),
            "normal_task_unlock-notice": (887, 164),
            "normal_task_task-info": (1087, 140),
            'normal_task_skip-sweep-complete': (643, 506),
            "buy_ap_notice": (919, 165),
            'normal_task_auto-over': (1082, 599),
            'normal_task_task-finish': (1038, 662),
            'normal_task_prize-confirm': (776, 655),
            'main_story_fight-confirm': (1168, 659),
        }
        click_pos = [
            [805, 165],
        ]
        los = [
            "event_hard",
        ]
        image.detect(self, end=None, possibles=possibles, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, ["event_normal"]))
    elif self.server == 'Global':
        possibles = {
            'normal_task_fight-complete-confirm': (1160, 666),
            'normal_task_reward-acquired-confirm': (800, 660),
            'normal_task_mission-conclude-confirm': (1042, 671),
        }
        end = [
            "normal_task_select-area",
        ]
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
        image.detect(self, end=end, possibles=possibles, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, ends))


def to_task_info(self, x, y):
    if self.server == 'CN':
        possibles = {
            "normal_task_menu": (x, y, 3),
        }
        ends = [
            "normal_task_unlock-notice",
            "normal_task_task-info"
        ]
        res = image.detect(self, end=ends, possibles=possibles)
        if res == "normal_task_task-info":
            return "mission_info"
        else:
            return "unlock_notice"
    elif self.server == 'Global':
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
        return color.common_rgb_detect_method(self, click_pos, los, ends)


def start_sweep(self):
    if self.server == 'CN':
        possibles = {
            "normal_task_task-info": (941, 411),
            "normal_task_start-sweep-notice": (765, 501)
        }
        ends = [
            "normal_task_skip-sweep-complete",
            "normal_task_sweep-complete",
            "buy_ap_notice",
        ]
        res = image.detect(self, end=ends, possibles=possibles)
        if res == "normal_task_sweep-complete":
            return "sweep_complete"
        elif res == "normal_task_skip-sweep-complete":
            return "skip_sweep_complete"
        elif res == "buy_ap_notice":
            return "purchase_ap_notice"
    elif self.server == 'Global':
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
        return color.common_rgb_detect_method(self, click_pos, pd_los, ends)


def choose_region(self, region):
    cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])
    while cu_region != region:
        if cu_region > region:
            self.click(40, 360, wait=False, count=cu_region - region, rate=0.1)
        else:
            self.click(1245, 360, wait=False, count=region - cu_region, rate=0.1)
        time.sleep(0.5)
        self.latest_img_array = self.get_screenshot_array()
        cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])
