import importlib
import time

from core import color, picture
from module import main_story, normal_task, hard_task
from module.explore_normal_task import common_gird_method


def implement(self):
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
            if not judge_need_fight(self, current_task):
                self.logger.warning("According to the mission info current mission no need fight")
                hard_task.to_hard_event(self, True)
            else:
                common_gird_method(self, current_task_stage_data)
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




def judge_need_fight(self, current_task):
    if 'task' in current_task:
        return True
    if 'sss' in current_task:
        res = color.check_sweep_availability(self, True)
        if res == 'no-pass' or res == 'pass':
            return True
    if 'present' in current_task:
        if color.judgeRGBFeature(self, 'hardTaskHasPresent'):
            return True
    return False


def choose_region(self, region):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
    self.logger.info("Current Region : " + str(cu_region))
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360, count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        hard_task.to_hard_event(self)
        cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
        self.logger.info("Current Region : " + str(cu_region))


def to_mission_info(self, y):
    rgb_possibles = {"event_hard": (1114, y)}
    img_ends = "normal_task_task-info"
    img_possibles = {'normal_task_select-area': (1114, y)}
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def get_explore_hard_task_data(st, need_sss=True, need_task=True, need_present=True):
    if type(st) is not str:
        st = str(st)
    st = st.split(',')
    tasks = []
    for i in range(0, len(st)):
        if '-' in st[i]:
            temp = st[i].split('-')
            if len(temp) > 5 or not temp[0].isdigit():
                continue
            if temp.count('sss') > 1 or temp.count('present') > 1 or temp.count('task') > 1 or not temp[0].isdigit():
                continue
            if int(temp[0]) < 0 or int(temp[0]) > 27:
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


def calc_team_number(self, current_task_stage_data):
    pri = {
        'pierce1': ['pierce1', 'pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2', 'shock1', 'shock2'],
        'pierce2': ['pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2', 'shock1', 'shock2'],
        'burst1': ['burst1', 'burst2', 'mystic1', 'mystic2', 'shock1', 'shock2', 'pierce1', 'pierce2'],
        'burst2': ['burst2', 'mystic1', 'mystic2', 'shock1', 'shock2', 'pierce1', 'pierce2'],
        'mystic1': ['mystic1', 'mystic2', 'shock1', 'shock2', 'burst1', 'burst2', 'pierce1', 'pierce2'],
        'mystic2': ['mystic2', 'burst1', 'shock1', 'shock2', 'burst2', 'pierce1', 'pierce2'],
        'shock1': ['shock1', 'shock2', 'pierce1', 'pierce2', 'mystic1', 'mystic2', 'burst1', 'burst2', ],
        'shock2': ['shock2', 'pierce1', 'pierce2', 'mystic1', 'mystic2', 'burst1', 'burst2', ]
    }
    length = len(current_task_stage_data['start'])
    used = {
        'pierce1': False,
        'pierce2': False,
        'burst1': False,
        'burst2': False,
        'mystic1': False,
        'mystic2': False,
        'shock1': False,
        'shock2': False,
    }
    keys = used.keys()
    last_chosen = 0
    res = []
    los = []
    for attr, position in current_task_stage_data['start'].items():
        if attr not in keys:
            res.append(attr)
            los.append(position)
            continue
        los.append(position)
        for i in range(0, len(pri[attr])):
            possible_attr = pri[attr][i]
            if (possible_attr == 'shock1' or possible_attr == 'shock2') and self.server == 'CN':
                continue
            possible_index = self.config[possible_attr]
            if not used[possible_attr] and 4 - possible_index >= length - len(res) - 1 and last_chosen < possible_index:
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
