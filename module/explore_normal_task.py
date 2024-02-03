import importlib
import time
from core import color, image, picture
from module import main_story, normal_task, hard_task

def test(self):
    normal_task.to_normal_event(self)
    for i in range(4, 6):
        region = 7
        self.logger.info("-- Start Pushing Region " + str(region) + " --")
        choose_region(self, region)
        self.swipe(917, 220, 917, 552, duration=0.1)
        time.sleep(1)
        to_mission_info(self, 238, True)
        for j in range(0, i - 1):
            self.click(1172, 358, wait=False)
            time.sleep(1)
        to_mission_info(self, 238, True)
        self.stage_data = get_stage_data(region)
        mission = str(region) + "-" + str(i)
        if mission == "ALL MISSION SWEEP AVAILABLE":
            self.logger.critical("ALL MISSION AVAILABLE TO SWEEP")
            normal_task.to_normal_event(self, True)
            break
        if mission == 'SUB':
            self.click(645, 511, wait_over=True)
            start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
            time.sleep(1)
            self.click(1171, 670, wait_over=True)
        else:
            current_task_stage_data = self.stage_data[mission]
            img_possibles = {
                'normal_task_help': (1017, 131),
                'normal_task_task-info': (946, 540)
            }
            img_ends = "normal_task_task-wait-to-begin-feature"
            image.detect(self, img_ends, img_possibles)

            res, los = calc_team_number(self, current_task_stage_data)
            for j in range(0, len(res)):
                if res[j] == "swipe":
                    time.sleep(1)
                    self.swipe(los[j][0], los[j][1], los[j][2], los[j][3], duration=los[j][4])
                    time.sleep(1)
                else:
                    choose_team(self, res[j], los[j], True)
            start_mission(self)
            check_skip_fight_and_auto_over(self)
            start_action(self, current_task_stage_data['action'])
        main_story.auto_fight(self)
        if self.config['manual_boss'] and mission != 'SUB':
            self.click(1235, 41)
        hard_task.to_hard_event(self)
        normal_task.to_normal_event(self, True)


def implement(self):
    # test(self)
    self.scheduler.change_display("普通关推图")
    self.quick_method_to_main_page()
    if self.config['explore_normal_task_force_fight']:
        normal_task.to_normal_event(self)
        tasks = get_explore_normal_task_missions(self.config['explore_normal_task_missions'])
        self.logger.info("VALID TASKS : " + str(tasks))
        for i in range(0, len(tasks)):
            region = tasks[i][0]
            mission = tasks[i][1]
            self.logger.info("-- Start Pushing " + str(region) + "-" + str(mission) + " --")
            choose_region(self, region)
            self.swipe(917, 220, 917, 552, duration=0.1)
            time.sleep(1)
            normal_task_y_coordinates = [242, 341, 439, 537, 611]
            to_mission_info(self, normal_task_y_coordinates[mission-1], True)
            self.stage_data = get_stage_data(region)
            mission = str(region) + "-" + str(i)
            current_task_stage_data = self.stage_data[mission]
            img_possibles = {
                'normal_task_help': (1017, 131),
                'normal_task_task-info': (946, 540)
            }
            img_ends = "normal_task_task-wait-to-begin-feature"
            image.detect(self, img_ends, img_possibles)
            choose_team_according_to_stage_data_and_config(self, current_task_stage_data)
            check_skip_fight_and_auto_over(self)
            start_action(self, current_task_stage_data['action'])
            main_story.auto_fight(self)
            if self.config['manual_boss']:
                self.click(1235, 41)
            hard_task.to_hard_event(self)
            normal_task.to_normal_event(self, True)
    else:
        need_change_acc = True
        self.logger.info("VALID REGIONS : " + str(self.config['explore_normal_task_regions']))
        self.quick_method_to_main_page()
        normal_task.to_normal_event(self, True)
        for i in range(0, len(self.config['explore_normal_task_regions'])):
            region = self.config['explore_normal_task_regions'][i]
            self.logger.info("-- Start Pushing Region " + str(region) + " --")
            if not 4 <= region <= 24:
                self.logger.warning("Region not support")
                continue
            choose_region(self, region)
            self.stage_data = get_stage_data(region)
            for k in range(0, 5):
                mission = calc_need_fight_stage(self, region, self.config['explore_norma_task_force_sss'])
                if mission == "ALL MISSION SWEEP AVAILABLE":
                    self.logger.critical("ALL MISSION AVAILABLE TO SWEEP")
                    normal_task.to_normal_event(self, True)
                    break
                if mission == 'SUB':
                    self.click(645, 511, wait_over=True)
                    start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
                    time.sleep(1)
                    self.click(1171, 670, wait_over=True)
                else:
                    current_task_stage_data = self.stage_data[mission]
                    img_possibles = {
                        'normal_task_help': (1017, 131),
                        'normal_task_task-info': (946, 540)
                    }
                    img_ends = "normal_task_task-wait-to-begin-feature"
                    image.detect(self, img_ends, img_possibles)
                    choose_team_according_to_stage_data_and_config(self, current_task_stage_data)
                    start_mission(self)
                    check_skip_fight_and_auto_over(self)
                    start_action(self, current_task_stage_data['action'])
                main_story.auto_fight(self, need_change_acc)
                need_change_acc = False
                if self.config['manual_boss']:
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
    if image.compare_image(self, 'normal_task_SUB', 3, image=self.latest_img_array):
        return 'SUB'
    return color.check_sweep_availability(self.latest_img_array, self.server)


def calc_need_fight_stage(self, region, force_sss):
    self.swipe(917, 220, 917, 552, duration=0.1)
    time.sleep(1)
    to_mission_info(self, 238, True)
    for i in range(1, 6):
        task_state = check_task_state(self)
        self.logger.info("Current mission status : {0}".format(task_state))
        if task_state == 'SUB':
            self.logger.info("Start SUB Fight")
            return task_state
        if task_state == 'no-pass':
            self.logger.info("Current task not pass. Start main line fight")
            return str(region) + "-" + str(i)
        if task_state == 'pass' and force_sss:
            self.logger.info("Current task not sss. Start main line fight")
            return str(region) + "-" + str(i)
        if task_state == 'sss':
            self.logger.info("CURRENT MISSION SSS")
        if i == 5:
            return "ALL MISSION SWEEP AVAILABLE"
        self.logger.info("Check next mission")
        self.click(1172, 358, wait=False, wait_over=True)
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()


def get_force(self):
    region = {
        'CN': (116, 542, 131, 570),
        'Global': (116, 542, 131, 570),
        'JP': (116, 542, 131, 570)
    }
    to_normal_task_mission_operating_page(self)
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


def start_action(self, actions, will_fight=False):
    self.set_screenshot_interval(1)
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
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait=False, wait_over=True)
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
                    wait_over(self, will_fight)
                    skip_first_screenshot = True
            elif op[j] == 'click_and_teleport':
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait=False, wait_over=True)
                confirm_teleport(self)
            elif op[j] == 'choose_and_change':
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait=False, wait_over=True, duration=0.3)
                self.click(pos[0] - 100, pos[1], wait=False, wait_over=True, duration=1)
            elif op[j] == 'exchange_and_click':
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                time.sleep(0.5)
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait=False, wait_over=True)
            elif op[j] == 'exchange_twice_and_click':
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                self.click(83, 557, wait=False, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                time.sleep(0.5)
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait=False, wait_over=True)

        if 'ec' in act:
            wait_formation_change(self, force_index)
        if 'wait-over' in act:
            wait_over(self, will_fight)
            skip_first_screenshot = True
            time.sleep(2)
        if i != len(actions) - 1:
            to_normal_task_mission_operating_page(self, skip_first_screenshot=skip_first_screenshot)
    self.set_screenshot_interval(self.config['screenshot_interval'])


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
        normal_task.to_normal_event(self)
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


def wait_over(self, will_fight=False):
    self.logger.info("Wait until move available")
    img_ends = "normal_task_mission-operating-task-info-notice"
    rgb_possibles = {"fighting_feature": (0, 0)}
    img_possibles = {
        'normal_task_task-operating-feature': (997, 670),
        'normal_task_teleport-notice': (885, 164),
        "normal_task_fight-confirm": (1171, 670),
    }
    while True:
        if not self.flag_run:
            return False
        color.wait_loading(self)
        if image.compare_image(self, img_ends, 3, image=self.latest_img_array, need_log=False):
            self.logger.info('end : ' + img_ends)
            return
        f = 0
        if will_fight:
            for position, click in rgb_possibles.items():
                for j in range(0, len(self.rgb_feature[position][0])):
                    if not color.judge_rgb_range(self.latest_img_array,
                                                 self.rgb_feature[position][0][j][0],
                                                 self.rgb_feature[position][0][j][1],
                                                 self.rgb_feature[position][1][j][0],
                                                 self.rgb_feature[position][1][j][1],
                                                 self.rgb_feature[position][1][j][2],
                                                 self.rgb_feature[position][1][j][3],
                                                 self.rgb_feature[position][1][j][4],
                                                 self.rgb_feature[position][1][j][5]):
                        break
                else:
                    self.logger.info("find : " + position)
                    f = 1
                    if position == "fighting_feature":
                        self.set_screenshot_interval(0.3)
                        main_story.auto_fight(self)
                        to_normal_task_mission_operating_page(self)
                        self.set_screenshot_interval(1)
                    self.latest_screenshot_time = time.time()
                    break
        if f == 0:
            if img_possibles is not None:
                for position, click in img_possibles.items():
                    if image.compare_image(self, position, 3, need_loading=False, image=self.latest_img_array,
                                           need_log=False):
                        self.logger.info("find " + position)
                        self.click(click[0], click[1], False)
                        self.latest_screenshot_time = time.time()
                        break


def start_mission(self):
    img_ends = "normal_task_task-operating-feature"
    img_possibles = {
        'normal_task_task-begin-without-further-editing-notice': (768, 498),
        'normal_task_task-operating-round-over-notice': (888, 163),
        'normal_task_task-wait-to-begin-feature': (1171, 670),
        'normal_task_end-turn': (888, 163),
    }
    image.detect(self, img_ends, img_possibles)


def to_mission_info(self, y, skip_first_screenshot=False):
    img_end = "normal_task_task-info"
    img_possible = {'normal_task_select-area': (1114, y, 3)}
    image.detect(self, img_end, img_possible, skip_first_screenshot=skip_first_screenshot)


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
        "normal_task_fight-confirm": (1171, 670),
    }
    img_ends = "normal_task_task-operating-feature"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def get_explore_normal_task_missions(self, st):
    try:
        st = st.split(',')
        tasks = []
        for i in range(0, len(st)):
            if '-' in st[i]:
                temp = st[i].split('-')
                region = int(temp[0])
                if region < 4 or region > 24:
                    self.logger.error("region" + temp[0] + "not support")
                    continue
                if len(temp) != 2:
                    continue
                tasks.append([int(temp[0]), int(temp[1])])
            else:
                region = int(st[i])
                if region < 4 or region > 24:
                    self.logger.error("region" + st[i] + "not support")
                    continue
                for j in range(1, 6):
                    tasks.append([int(st[i]), j])
        return tasks
    except Exception as e:
        self.logger.error(e)
        self.logger.error("explore_normal_task_missions config error")
        return False


def choose_team_according_to_stage_data_and_config(self, current_task_stage_data):
    res, los = calc_team_number(self, current_task_stage_data)
    for j in range(0, len(res)):
        if res[j] == "swipe":
            time.sleep(1)
            self.swipe(los[j][0], los[j][1], los[j][2], los[j][3], duration=los[j][4])
            time.sleep(1)
        else:
            choose_team(self, res[j], los[j], True)
    start_mission(self)
