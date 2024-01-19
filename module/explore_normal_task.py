import importlib
import time

from core import color, image, picture
from module import main_story, normal_task, hard_task


def implement(self):
    self.scheduler.change_display("普通关推图")
    self.logger.info("Start Normal Task valid tasks : " + str(self.config['explore_normal_task_regions']))
    self.quick_method_to_main_page()
    normal_task.to_normal_event(self, True)
    for i in range(0, len(self.config['explore_normal_task_regions'])):
        region = self.config['explore_normal_task_regions'][i]
        if not 4 <= region <= 16:
            self.logger.warning("Region not support")
            return True
        choose_region(self, region)
        self.stage_data = get_stage_data(region)
        for k in range(0, 5):
            mission = calc_need_fight_stage(self, region)
            if mission == "ALL MISSION SWEEP AVAILABLE":
                self.logger.critical("ALL MISSION AVAILABLE TO SWEEP")
                normal_task.to_normal_event(self, True)
                break
            if mission == 'SUB':
                self.click(645, 511, wait_over=True)
                start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
                time.sleep(1)
                self.click(1171, 670, wait_over=True)
                self.set_screenshot_interval(1)
            else:
                current_task_stage_data = self.stage_data[mission]
                img_possibles = {
                    'normal_task_help': (1017, 131),
                    'normal_task_task-info': (946, 540)
                }
                img_ends = "normal_task_task-wait-to-begin-feature"
                image.detect(self, img_ends, img_possibles)
                res,los = cacl_team_number(self, current_task_stage_data)
                for j in range(0, len(res)):
                    choose_team(self, res[j], los[j], True)
                start_mission(self)
                check_skip_fight_and_auto_over(self)
                self.set_screenshot_interval(1)
                start_action(self, current_task_stage_data['action'])
            self.set_screenshot_interval(self.config['screenshot_interval'])
            main_story.auto_fight(self)
            if self.config['manual_boss'] and mission != 'SUB':
                self.click(1235, 41)
            hard_task.to_hard_event(self)
            normal_task.to_normal_event(self, True)
    return True


def get_stage_data(region):
    module_path = 'src.explore_task_data.normal_task.normal_task_' + str(region)
    stage_module = importlib.import_module(module_path)
    stage_data = getattr(stage_module, 'stage_data', None)
    return stage_data


def check_task_state(self):
    if self.server == 'CN':
        if image.compare_image(self, 'normal_task_side-quest', 3, image=self.latest_img_array):
            return 'SUB'
    elif self.server == 'Global':
        if image.compare_image(self, 'normal_task_SUB-mission-info', 3, image=self.latest_img_array):
            return 'SUB'
    return color.check_sweep_availability(self.latest_img_array, self.server)


def calc_need_fight_stage(self, region):
    self.swipe(917, 220, 917, 552, duration=0.1)
    time.sleep(1)
    to_mission_info(self, 238)
    for i in range(1, 6):
        task_state = check_task_state(self)
        self.logger.info("Current mission status : {0}".format(task_state))
        if task_state == 'SUB':
            self.logger.info("Start SUB Fight")
            return task_state
        if task_state == 'no-pass' or task_state == 'pass':
            self.logger.info("Start main line fight")
            return str(region) + "-" + str(i)
        if task_state == 'sss':
            self.logger.info("CURRENT MISSION SSS")
        if i == 5:
            return "ALL MISSION SWEEP AVAILABLE"
        self.logger.info("Check next mission")
        self.click(1172, 358, wait=False)
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()


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


def start_choose_side_team(self, index):
    self.logger.info("According to the config. Choose formation " + str(index))
    loy = [195, 275, 354, 423]
    y = loy[index - 1]
    click_pos = [
        [74, y],
        [74, y],
        [74, y],
        [74, y],
    ]
    los = [
        "formation_edit1",
        "formation_edit2",
        "formation_edit3",
        "formation_edit4",
    ]
    ends = [
        "formation_edit" + str(index)
    ]
    los.pop(index - 1)
    click_pos.pop(index - 1)
    color.common_rgb_detect_method(self, click_pos, los, ends)


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


def choose_team(self, number, position, skip_first_screenshot=False):
    self.logger.info("According to the config. Choose formation " + str(number))
    to_formation_edit_i(self, number, position, skip_first_screenshot)
    to_normal_task_wait_to_begin_page(self, skip_first_screenshot)


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


def wait_formation_change(self, force_index):
    self.logger.info("Wait formation change")
    origin = force_index
    while force_index == origin and self.flag_run:
        force_index = get_force(self)
        time.sleep(self.screenshot_interval)
    return force_index


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


def to_normal_task_mission_operating_page(self, skip_first_screenshot=False):
    img_possibles = {
        "normal_task_mission-operating-task-info-notice": (995, 101),
        "normal_task_end-turn": (890, 162),
        "normal_task_teleport-notice": (886, 162),
    }
    img_ends = "normal_task_task-operating-feature"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)
