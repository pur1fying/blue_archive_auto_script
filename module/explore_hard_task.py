import importlib
import time

from core import color, image, picture
from module import main_story, normal_task, hard_task


def implement(self):
    # self.scheduler.change_display("困难关推图")
    t = self.config['explore_hard_task_list']
    if type(t) is int:
        t = str(t)
    elif type(t) is list:
        temp = ''
        for i in range(0, len(t)):
            temp = temp + str(t[i]) + ','
        t = temp
    need_sss = self.config['explore_hard_task_need_sss']
    need_task = self.config['explore_hard_task_need_task']
    need_present = self.config['explore_hard_task_need_present']
    tasks = get_explore_hard_task_data(t, need_sss, need_task, need_present)
    mission_los = [249, 363, 476]
    self.logger.info("VALID TASK LIST " + str(tasks))
    self.quick_method_to_main_page()
    # test_(self)
    hard_task.to_hard_event(self, True)
    for i in range(0, len(tasks)):
        data = tasks[i].split('-')
        region = int(data[0])
        mission = int(data[1])
        unfinished_tasks = data[2:]
        if not 6 <= region <= 16:
            self.logger.warning("Region not support")
            return True
        self.stage_data = get_stage_data(region)
        while len(unfinished_tasks) != 0:
            current_task = [unfinished_tasks.pop(0)]
            current_task_stage_data = ""
            for key in self.stage_data:
                if key.startswith(str(region) + '-' + str(mission)):
                    tt = key.split('-')[2:]
                    if current_task[0] in key:
                        temp = 0
                        current_task_stage_data = self.stage_data[key]
                        while len(unfinished_tasks) != 0 and temp < len(unfinished_tasks):
                            if unfinished_tasks[temp] in tt:
                                current_task.append(unfinished_tasks.pop(temp))
                            else:
                                temp += 1

                        break
            if current_task_stage_data == "":
                self.logger.warning("Task not support")
                continue
            choose_region(self, region)
            to_mission_info(self, mission_los[mission - 1])
            status = judge_need_fight(self, current_task)
            if status == "no-need-fight":
                self.logger.warning("according to the mission info current mission no need fight")
                hard_task.to_hard_event(self, True)
            elif status == 'need-fight':
                img_possibles = {
                    'normal_task_help': (1017, 131),
                    'normal_task_task-info': (946, 540)
                }
                img_ends = "normal_task_task-wait-to-begin-feature"
                image.detect(self, img_ends, img_possibles)
                res, los = cacl_team_number(self, current_task_stage_data)
                for j in range(0, len(res)):
                    choose_team(self, res[j], los[j], True)
                start_mission(self)
                check_skip_fight_and_auto_over(self)
                self.set_screenshot_interval(1)
                start_action(self, current_task_stage_data['action'])
                self.set_screenshot_interval(self.config['screenshot_interval'])
                main_story.auto_fight(self)
                if self.config['manual_boss']:
                    self.click(1235, 41)
                normal_task.to_normal_event(self)
                hard_task.to_hard_event(self, True)
    return True


def get_stage_data(region):
    module_path = 'src.explore_task_data.hard_task.hard_task_' + str(region)
    stage_module = importlib.import_module(module_path)
    stage_data = getattr(stage_module, 'stage_data', None)
    return stage_data


def check_present(self):
    if color.judge_rgb_range(self.latest_img_array, 226, 511, 103, 123, 227, 247, 245, 255) \
        and color.judge_rgb_range(self.latest_img_array, 190, 526, 103, 123, 227, 247, 245, 255) \
        and color.judge_rgb_range(self.latest_img_array, 216, 540, 245, 255, 180, 210, 220, 255):
        return 'find-present'
    else:
        return 'no-present'


def judge_need_fight(self, current_task):
    if 'task' in current_task:
        return 'need-fight'
    if 'sss' in current_task:
        res = color.check_sweep_availability(self.latest_img_array, self.server)
        if res == 'no-pass' or res == 'pass':
            return 'need-fight'
    if 'present' in current_task:
        res = check_present(self)
        if res == 'find-present':
            return 'need-fight'
    return 'no-need-fight'


def get_force(self):
    region = {
        'CN': (116, 542, 131, 570),
        'Global': (116, 542, 131, 570),
        'JP': (116, 542, 131, 570)
    }
    self.latest_img_array = self.get_screenshot_array()
    ocr_res = self.ocr.get_region_num(self.latest_img_array, region[self.server])
    if ocr_res == "UNKNOWN":
        return get_force(self)
    if ocr_res == 7:
        return 1
    if ocr_res not in [1, 2, 3, 4]:
        return get_force(self)
    return ocr_res


def end_turn(self):
    self.logger.info("--End Turn--")
    img_end = 'normal_task_end-turn'
    img_possibles = {
        'normal_task_task-operating-feature': (1170, 670),
        'normal_task_present': (640, 519),
    }
    picture.co_detect(self, None, None, img_end, img_possibles)
    self.logger.info("Confirm End Turn")
    img_end = 'normal_task_task-operating-feature'
    img_possibles = {'normal_task_end-turn': (767, 501)}
    picture.co_detect(self, None, None, img_end, img_possibles, True)


def confirm_teleport(self):
    self.logger.info("Wait Teleport Notice")
    picture.co_detect(self, None, None, "normal_task_teleport-notice", None)
    self.logger.info("Confirm Teleport")
    img_end = 'normal_task_task-operating-feature'
    img_possibles = {'normal_task_teleport-notice': (767, 501), }
    picture.co_detect(self, None, None, img_end, img_possibles, True)


def start_action(self, actions):
    self.logger.info("Start Actions total : " + str(len(actions)))
    for i, act in enumerate(actions):
        desc = "start " + str(i + 1) + " operation : "
        if 'desc' in act:
            desc += act['desc']
        self.logger.info(desc)
        force_index = get_force(self)
        op = act['t']
        if type(op) is str:
            op = [op]
        if 'p' in act:
            if type(act['p']) is tuple:
                act['p'] = [act['p']]
        skip_first_screenshot = False
        for j in range(0, len(op)):
            time.sleep(1)
            if op[j] == 'click':
                self.click(act['p'][0][0], act['p'][0][1], wait=False, wait_over=True)
                act['p'].pop(0)
            elif op[j] == 'teleport':
                confirm_teleport(self)
            elif op[j] == 'exchange':
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
            elif op[j] == 'exchange_twice':
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
            elif op[j] == 'end-turn':
                end_turn(self)
                if i != len(actions) - 1:
                    wait_over(self)
                    skip_first_screenshot = True
            elif op[j] == 'click_and_teleport':
                self.click(act['p'][0][0], act['p'][0][1], wait=False, wait_over=True)
                act['p'].pop(0)
                confirm_teleport(self)
            elif op[j] == 'choose_and_change':
                self.click(act['p'][0][0], act['p'][0][1], wait=False, wait_over=True, duration=0.3)
                self.click(act['p'][0][0] - 100, act['p'][0][1], wait=False, wait_over=True)
                act['p'].pop(0)
            elif op[j] == 'exchange_and_click':
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                time.sleep(0.5)
                self.click(act['p'][0][0], act['p'][0][1], wait=False, wait_over=True)
                act['p'].pop(0)
            elif op[j] == 'exchange_twice_and_click':
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                time.sleep(0.5)
                self.click(act['p'][0], act['p'][1], wait=False, wait_over=True)
                act['p'].pop(0)

        if 'ec' in act:
            wait_formation_change(self, force_index)
        if 'wait-over' in act:
            wait_over(self)
            skip_first_screenshot = True
            time.sleep(2)
        if i != len(actions) - 1:
            to_normal_task_mission_operating_page(self, skip_first_screenshot=skip_first_screenshot)


def wait_formation_change(self, force_index):
    self.logger.info("Wait formation change")
    origin = force_index
    while force_index == origin and self.flag_run:
        force_index = get_force(self)
        time.sleep(self.screenshot_interval)
    return force_index


def choose_region(self, region):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server])
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, wait=False, count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360, wait=False, count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        self.latest_img_array = self.get_screenshot_array()
        cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server])


def choose_team(self, number, position, skip_first_screenshot=True):
    self.logger.info("According to the config. Choose formation " + str(number))
    to_formation_edit_i(self, number, position, skip_first_screenshot)
    to_normal_task_wait_to_begin_page(self, skip_first_screenshot)


def to_normal_task_mission_operating_page(self, skip_first_screenshot=False):
    img_possibles = {
        "normal_task-present": (794, 207),
        "normal_task_mission-operating-task-info-notice": (995, 101),
        "normal_task_end-turn": (890, 162),
        "normal_task_teleport-notice": (886, 162),
    }
    img_ends = "normal_task_task-operating-feature"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_normal_task_wait_to_begin_page(self, skip_first_screenshot=False):
    rgb_possibles = {
        "formation_edit1": (1154, 625),
        "formation_edit2": (1154, 625),
        "formation_edit3": (1154, 625),
        "formation_edit4": (1154, 625),
    }
    img_ends = [
        'normal_task_task-wait-to-begin-feature',
        'normal_task_task-operating-feature'
    ]
    img_possibles = {
        'task-begin-without-further-editing-notice': (888, 164)
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_formation_edit_i(self, i, lo, skip_first_screenshot=False):
    loy = [195, 275, 354, 423]
    y = loy[i - 1]
    rgb_ends = "formation_edit" + str(i)
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_possibles.pop("formation_edit" + str(i))
    img_possibles = {"normal_task_task-wait-to-begin-feature": (lo[0], lo[1])}
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def wait_over(self):
    self.logger.info("Wait until move available")
    img_ends = "normal_task_mission-operating-task-info-notice"
    img_possibles = {
        'normal_task_task-operating-feature': (997, 670),
        'normal_task_present': (794, 207),
        'normal_task_teleport-notice': (885, 164),
    }
    image.detect(self, img_ends, img_possibles)


def start_mission(self):
    img_ends = "normal_task_task-operating-feature"
    img_possibles = {
        'normal_task_fight-task': (1171, 670),
        'normal_task_task-begin-without-further-editing-notice': (768, 498),
        'normal_task_task-operating-round-over-notice': (888, 163),
        'normal_task_task-wait-to-begin-feature': (1171, 670),
        'normal_task_end-turn': (888, 163),
    }
    image.detect(self, img_ends, img_possibles)


def to_mission_info(self, y):
    img_end = "normal_task_task-info"
    img_possible = {'normal_task_select-area': (1114, y, 3)}
    image.detect(self, img_end, img_possible)


def get_explore_hard_task_data(st, need_sss=True, need_task=True, need_present=True):
    st = st.split(',')
    tasks = []
    for i in range(0, len(st)):
        if '-' in st[i]:
            temp = st[i].split('-')
            if len(temp) > 5 or not temp[0].isdigit():
                continue
            if temp.count('sss') > 1 or temp.count('present') > 1 or temp.count('task') > 1 or not temp[0].isdigit():
                continue
            if int(temp[0]) < 6 or int(temp[0]) > 16:
                continue
            if temp[0].isdigit() and temp[1].isdigit():  # 指定关卡
                tt = ''
                if len(temp) == 2:
                    if need_sss:
                        tt = tt + '-sss'
                    if need_present:
                        tt = tt + '-present'
                    if need_task:
                        tt = tt + '-task'
                else:
                    if 'sss' in temp:
                        tt = tt + '-sss'
                    if 'present' in temp:
                        tt = tt + '-present'
                    if 'task' in temp:
                        tt = tt + '-task'
                tasks.append(temp[0] + '-' + temp[1] + tt)
            elif temp[0].isdigit() and not temp[1].isdigit():
                tt = ''
                if 'sss' in temp:
                    tt = tt + '-sss'
                if 'present' in temp:
                    tt = tt + '-present'
                if 'task' in temp:
                    tt = tt + '-task'
                for j in range(1, 4):
                    tasks.append(temp[0] + '-' + str(j) + tt)
        elif st[i].isdigit():
            tt = ''
            if need_sss:
                tt = tt + '-sss'
            if need_present:
                tt = tt + '-present'
            if need_task:
                tt = tt + '-task'
            for j in range(1, 4):
                tasks.append(st[i] + '-' + str(j) + tt)
    return tasks


def check_skip_fight_and_auto_over(self):
    if not image.compare_image(self, 'normal_task_fight-skip', threshold=3, image=self.latest_img_array):
        self.click(1194, 547)
    if not image.compare_image(self, 'normal_task_auto-over', threshold=3, image=self.latest_img_array):
        self.click(1194, 600)


def cacl_team_number(self, current_task_stage_data):
    pri = {
        'pierce1': ['pierce1', 'pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2'],
        'pierce2': ['pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2'],
        'burst1': ['burst1', 'burst2', 'pierce1', 'pierce2', 'mystic1', 'mystic2'],
        'burst2': ['burst2', 'pierce1', 'pierce2', 'mystic1', 'mystic2'],
        'mystic1': ['mystic1', 'mystic2', 'burst1', 'burst2', 'pierce1', 'pierce2'],
        'mystic2': ['mystic2', 'burst1', 'burst2', 'pierce1', 'pierce2'],
    }
    length = len(current_task_stage_data['start'])
    used = {
        'pierce1': False,
        'pierce2': False,
        'burst1': False,
        'burst2': False,
        'mystic1': False,
        'mystic2': False
    }
    last_chosen = 0
    res = []
    los = []
    for attr, position in current_task_stage_data['start'].items():
        los.append(position)
        for i in range(0, len(pri[attr])):
            possible_attr = pri[attr][i]
            possible_index = self.config[possible_attr]
            if not used[possible_attr] and 4 - possible_index >= length - i - 1 and last_chosen < possible_index:
                res.append(possible_index)
                used[possible_attr] = True
                last_chosen = self.config[possible_attr]
                break
    if len(res) != length:
        self.logger.warning("Insufficient forces are chosen")
        if length - len(res) <= 4 - last_chosen:
            for i in range(0, length - len(res)):
                res.append(last_chosen + i + 1)
        else:
            self.logger.warning("USE formations as the number increase")
            res.clear()
            for i in range(0, length):
                res.append(i + 1)
    self.logger.info("Choose formations : " + str(res))
    return res, los
