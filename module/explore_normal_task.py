import importlib
import time
from core import color, image, picture
from module import main_story, normal_task, hard_task


def implement(self):
    temp = get_explore_normal_task_missions(self, self.config['explore_normal_task_regions'], self.config['explore_normal_task_force_each_fight'])
    self.quick_method_to_main_page()
    if self.config['explore_normal_task_force_each_fight']:
        temp = get_explore_normal_task_missions(self, self.config['explore_normal_task_regions'])
        self.logger.info("VALID TASKS : " + str(temp))
        normal_task.to_normal_event(self)
        for i in range(0, len(temp)):
            region = temp[i][0]
            mission = temp[i][1]
            self.logger.info("-- Start Pushing " + str(region) + "-" + str(mission) + " --")
            choose_region(self, region)
            self.swipe(917, 220, 917, 552, duration=0.1, post_sleep_time=1)
            normal_task_y_coordinates = [242, 341, 439, 537, 611]
            res = to_mission_info(self, normal_task_y_coordinates[mission - 1], True)
            self.stage_data = get_stage_data(region)
            mission = str(region) + "-" + str(mission)
            current_task_stage_data = self.stage_data[mission]
            common_gird_method(self, current_task_stage_data)
            main_story.auto_fight(self)
            if self.config['manual_boss']:
                self.click(1235, 41)
            hard_task.to_hard_event(self)
            normal_task.to_normal_event(self, True)
    else:
        need_change_acc = True
        self.logger.info("VALID REGIONS : " + str(temp))
        self.quick_method_to_main_page()
        normal_task.to_normal_event(self, True)
        for i in range(0, len(temp)):
            region = temp[i]
            self.logger.info("-- Start Pushing Region " + str(region) + " --")
            if not 4 <= region <= 27:
                self.logger.warning("Region not support")
                continue
            choose_region(self, region)
            self.stage_data = get_stage_data(region)
            for k in range(0, 13):  # 5 grid to walk and 8 sub task
                mission = calc_need_fight_stage(self, region, self.config['explore_normal_task_force_sss'])
                if mission == "ALL MISSION SWEEP AVAILABLE":
                    self.logger.critical("ALL MISSION AVAILABLE TO SWEEP")
                    normal_task.to_normal_event(self, True)
                    break
                if mission == 'SUB':
                    start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
                    rgb_possibles = {
                        "formation_edit" + str(self.config[self.stage_data[str(region)]['SUB']]): (1171, 670),
                    }
                    rgb_ends = "fighting_feature"
                    picture.co_detect(self, rgb_ends, rgb_possibles, None, None, True)
                else:
                    current_task_stage_data = self.stage_data[mission]
                    common_gird_method(self, current_task_stage_data)
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
    if image.compare_image(self, 'normal_task_SUB'):
        return 'SUB'
    return color.check_sweep_availability(self, True)


def calc_need_fight_stage(self, region, force_sss):
    self.swipe(917, 220, 917, 552, duration=0.1, post_sleep_time=1)
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
        if task_state == 'pass' and not force_sss:
            self.logger.info("Current task not sss. Start main line fight")
            return str(region) + "-" + str(i)
        if task_state == 'sss':
            self.logger.info("CURRENT MISSION SSS")
        if i == 5:
            return "ALL MISSION SWEEP AVAILABLE"
        self.logger.info("Check next mission")
        self.click(1172, 358, wait_over=True, duration=1)
        self.latest_img_array = self.get_screenshot_array()


def get_force(self):
    region = {
        'CN': (116, 542, 131, 570),
        'Global': (116, 542, 131, 570),
        'JP': (116, 542, 131, 570)
    }
    to_normal_task_mission_operating_page(self)
    ocr_res = self.ocr.get_region_num(self.latest_img_array, region[self.server], int, self.ratio)
    if ocr_res == "UNKNOWN":
        return get_force(self)
    if ocr_res == 7:
        ocr_res = 1
    if ocr_res not in [1, 2, 3, 4]:
        return get_force(self)
    self.logger.info("Current force : " + str(ocr_res))
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
    rgb_end = "fighting_feature"
    picture.co_detect(self, rgb_end, None, img_end, img_possibles, True)


def confirm_teleport(self):
    self.logger.info("Wait Teleport Notice")
    picture.co_detect(self, None, None, "normal_task_teleport-notice", None)
    self.logger.info("Confirm Teleport")
    img_end = 'normal_task_task-operating-feature'
    img_possibles = {'normal_task_teleport-notice': (767, 501), }
    picture.co_detect(self, None, None, img_end, img_possibles, True)


def start_action(self, actions):
    self.set_screenshot_interval(1)
    self.logger.info("Start Actions total : " + str(len(actions)))
    for i, act in enumerate(actions):
        if not self.flag_run:
            return
        desc = "start " + str(i + 1) + " operation : "
        if 'desc' in act:
             desc += act['desc']
        self.logger.info(desc)
        force_index = get_force(self)
        op = act['t']
        if 'pre-wait' in act:
            time.sleep(act['pre-wait'])
        if 'retreat' in act:
            turn_off_skip_fight(self)
        if type(op) is str:
            op = [op]
        if 'p' in act:
            if type(act['p']) is tuple or (len(act['p']) == 2 and type(act['p'][0]) is int):
                act['p'] = [act['p']]
        skip_first_screenshot = False
        for j in range(0, len(op)):
            time.sleep(1)
            if op[j] == 'click':
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait_over=True)
            elif op[j] == 'teleport':
                confirm_teleport(self)
            elif op[j] == 'exchange':
                self.click(83, 557, wait_over=True)
                force_index = wait_formation_change(self, force_index)
            elif op[j] == 'exchange_twice':
                self.click(83, 557, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                self.click(83, 557, wait_over=True)
                force_index = wait_formation_change(self, force_index)
            elif op[j] == 'end-turn':
                end_turn(self)
                if i != len(actions) - 1:
                    if 'end-turn-wait-over' in act and act['end-turn-wait-over'] is False:  # not every end turn need to wait
                        self.logger.info("End Turn without wait over")
                    else:
                        wait_over(self)
                        skip_first_screenshot = True
            elif op[j] == 'click_and_teleport':
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait_over=True)
                confirm_teleport(self)
            elif op[j] == 'choose_and_change':
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait_over=True, duration=0.3)
                self.click(pos[0] - 100, pos[1], wait_over=True, duration=1)
            elif op[j] == 'exchange_and_click':
                self.click(83, 557, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                time.sleep(0.5)
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait_over=True)
            elif op[j] == 'exchange_twice_and_click':
                self.click(83, 557, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                self.click(83, 557, wait_over=True)
                force_index = wait_formation_change(self, force_index)
                time.sleep(0.5)
                pos = act['p'][0]
                self.click(pos[0], pos[1], wait_over=True)
        if 'retreat' in act:
            for fight in range(1, act['retreat'][0] + 1):
                main_story.auto_fight(self)
                for retreatNum in act['retreat'][1:]:
                    if retreatNum == fight:
                        self.logger.info("retreat at fight" + str(retreatNum))
                        retreat(self)
                        break
                to_normal_task_mission_operating_page(self, True)
            check_skip_fight_and_auto_over(self)
        if 'ec' in act:
            wait_formation_change(self, force_index)
        if 'wait-over' in act:
            wait_over(self)
            skip_first_screenshot = True
            time.sleep(2)
        if 'post-wait' in act:
            time.sleep(act['post-wait'])
        if i != len(actions) - 1:
            to_normal_task_mission_operating_page(self, skip_first_screenshot=skip_first_screenshot)
    self.set_screenshot_interval(self.config['screenshot_interval'])


def start_choose_side_team(self, index):
    self.logger.info("According to the config. Choose formation " + str(index))
    loy = [195, 275, 354, 423]
    y = loy[index - 1]
    img_possibles = {
        'normal_task_SUB': (637, 508),
        'normal_task_task-info': (946, 540)
    }
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_ends = "formation_edit" + str(index)
    rgb_possibles.pop("formation_edit" + str(index))
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)


def choose_region(self, region):
    square = {
        'CN': [122, 178, 163, 208],
        'Global': [122, 178, 163, 208],
        'JP': [122, 178, 163, 208]
    }
    cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, count=cu_region - region, rate=0.1, wait_over=True)
        else:
            self.click(1245, 360, count=region - cu_region, rate=0.1, wait_over=True)
        time.sleep(0.5)
        normal_task.to_normal_event(self)
        cu_region = self.ocr.get_region_num(self.latest_img_array, square[self.server], int, self.ratio)


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
    img_possibles = {"normal_task_task-wait-to-begin-feature": lo}
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, skip_first_screenshot)


def wait_over(self):
    self.logger.info("Wait until move available")
    img_ends = "normal_task_mission-operating-task-info-notice"
    img_possibles = {
        'normal_task_task-operating-feature': (997, 670),
        'normal_task_teleport-notice': (885, 164),
        "normal_task_fight-confirm": (1171, 670),
        'normal_task_present': (640, 519),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True, rgb_pop_ups={"fighting_feature": (-1, -1)},
                      img_pop_ups={"activity_choose-buff": (644, 570)})


def start_mission(self):
    img_ends = "normal_task_task-operating-feature"
    img_possibles = {
        'normal_task_task-begin-without-further-editing-notice': (768, 498),
        'normal_task_task-operating-round-over-notice': (888, 163),
        'normal_task_task-wait-to-begin-feature': (1171, 670),
        'normal_task_end-turn': (888, 163),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_mission_info(self, y, skip_first_screenshot=False):
    rgb_possibles = {"event_normal": (1114, y), }
    img_possible = {'normal_task_select-area': (1114, y)}
    img_end = [
        "normal_task_task-info",
        "normal_task_SUB",
    ]
    return picture.co_detect(self, None, rgb_possibles, img_end, img_possible, skip_first_screenshot)


def wait_formation_change(self, force_index):
    self.logger.info("Wait formation change")
    origin = force_index
    while force_index == origin and self.flag_run:
        force_index = get_force(self)
        time.sleep(self.screenshot_interval)
    return force_index


def check_skip_fight_and_auto_over(self):
    while self.flag_run:
        f = 1
        if not image.compare_image(self, 'normal_task_fight-skip'):
            f = 0
            self.click(1194, 547, wait_over=True, duration=0.5)
        if not image.compare_image(self, 'normal_task_auto-over'):
            f = 0
            self.click(1194, 600, wait_over=True, duration=0.5)
        if f:
            return
        to_normal_task_mission_operating_page(self, False)


def turn_off_skip_fight(self):
    while self.flag_run:
        to_normal_task_mission_operating_page(self, False)
        if image.compare_image(self, 'normal_task_fight-skip'):
            self.click(1194, 547, wait_over=True, duration=0.5)
        else:
            return


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
    total_teams = 0
    for i in range(0, len(current_task_stage_data['start'])):
        if current_task_stage_data['start'][i][0] in keys:
            total_teams += 1
    last_chosen = 0
    team_res = []
    team_attr = []
    los = []
    for i in range(0, len(current_task_stage_data['start'])):
        attr, position = current_task_stage_data['start'][i][0], current_task_stage_data['start'][i][1]
        los.append(position)
        if attr not in keys:
            continue
        for j in range(0, len(pri[attr])):
            possible_attr = pri[attr][j]
            if (possible_attr == 'shock1' or possible_attr == 'shock2') and self.server == 'CN':
                continue
            possible_index = self.config[possible_attr]
            if not used[possible_attr] and 4 - possible_index >= total_teams - len(
                team_res) - 1 and last_chosen < possible_index:
                team_res.append(possible_index)
                team_attr.append(possible_attr)
                used[possible_attr] = True
                last_chosen = self.config[possible_attr]
                break
    if len(team_res) != total_teams:
        self.logger.warning("Insufficient forces are chosen")
        if total_teams - len(team_res) <= 4 - last_chosen:
            for i in range(0, total_teams - len(team_res)):
                team_res.append(last_chosen + i + 1)
                team_attr.append("auto-choose")
        else:
            self.logger.warning("USE formations as the number increase")
            team_res.clear()
            team_attr = ["auto-choose"]
            cnt = 1
            for i in range(0, len(current_task_stage_data['start'])):
                if current_task_stage_data['start'][i][0] in keys:
                    team_res.append(cnt)
                    los.append(current_task_stage_data['start'][i][1])
                    cnt += 1
    self.logger.info("Choose formations : " + str(team_res))
    self.logger.info("attr : " + str(team_attr))
    action_res = []
    temp = 0
    for i in range(0, len(current_task_stage_data['start'])):
        if current_task_stage_data['start'][i][0] not in keys:
            action_res.append(current_task_stage_data['start'][i][0])
        else:
            action_res.append(team_res[temp])
            temp += 1
    self.logger.info("actions : " + str(action_res))
    self.logger.info("position : " + str(los))
    return action_res, los


def to_normal_task_mission_operating_page(self, skip_first_screenshot=False):
    img_possibles = {
        "normal_task_mission-operating-task-info-notice": (995, 101),
        "normal_task_end-turn": (890, 162),
        "normal_task_teleport-notice": (886, 162),
        'normal_task_present': (640, 519),
        "normal_task_fight-confirm": (1171, 670),
        'normal_task_fail-confirm': (640, 670),
    }
    img_ends = "normal_task_task-operating-feature"
    img_pop_ups = {"activity_choose-buff": (644, 570)}
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot, img_pop_ups=img_pop_ups)


def get_explore_normal_task_missions(self, st, force_each_fight=False):
    lg = "Tasks"
    if not force_each_fight:
        lg = "Regions"
    self.logger.info("Get Explore Normal Task Valid " + lg)
    region_range = self.static_config['explore_normal_task_region_range']
    ret = []
    if not force_each_fight:
        if type(st) is int:
            st = str(st)
        if type(st) is str:
            st = st.replace(' ', '')
            st = st.replace('，', ',')
            st = st.split(',')
        if type(st) is list:
            for t in st:
                if type(t) is str:
                    try:
                        t = int(t)
                    except ValueError:
                        self.logger.warning("[ " + t + " ] is not a number.Skip")
                        continue
                if type(t) is int:
                    if t < region_range[0] or t > region_range[1]:
                        self.logger.warning("Region [ " + str(t) + " ] not support")
                        continue
                    ret.append(t)

    else:
        try:
            if type(st) is list:
                for i in range(0, len(st)):
                    st[i] = str(st[i])
            elif type(st) is not str:
                st = str(st)
            if type(st) is str:
                st = st.replace(' ', '')
                st = st.replace('，', ',')
                st = st.split(',')
            for t in st:
                if '-' in t:
                    temp = t.split('-')
                    if len(temp) != 2:
                        self.logger.error("[ " + t + " ] format error. Expected : 'region-mission'")
                        continue
                    try:
                        region = int(temp[0])
                    except ValueError:
                        self.logger.warning("Region [ " + t + " ] is not a number.Skip")
                        continue
                    try:
                        mission = int(temp[1])
                    except ValueError:
                        self.logger.warning("Mission [ " + t + " ] is not a number.Skip")
                        continue
                    if region < region_range[0] or region > region_range[1]:
                        self.logger.error("Region [ " + temp[0] + " ] not support")
                        continue
                    ret.append([region, mission])
                else:
                    try:
                        region = int(t)
                    except ValueError:
                        self.logger.warning("Region [ " + t + " ] is not a number.Skip")
                        continue
                    if region < region_range[0] or region > region_range[1]:
                        self.logger.error("Region [ " + t + " ] not support")
                        continue
                    for j in range(1, 6):
                        ret.append([int(t), j])
        except Exception as e:
            self.logger.error(e.__str__())
            self.logger.error("explore_normal_task_missions config error")
            return False
    self.logger.info("Valid " + lg + " : " + str(ret))
    return ret


def choose_team_according_to_stage_data_and_config(self, current_task_stage_data):
    res, los = calc_team_number(self, current_task_stage_data)
    for j in range(0, len(res)):
        if res[j] == "swipe":
            time.sleep(1)
            self.swipe(los[j][0], los[j][1], los[j][2], los[j][3], duration=los[j][4])
            time.sleep(1)
        else:
            choose_team(self, res[j], los[j], True)


def common_gird_method(self, current_task_stage_data):
    img_possibles = {
        'normal_task_help': (1017, 131),
        'normal_task_task-info': (946, 540),
        'activity_task-info': (946, 540),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
    }
    img_ends = "normal_task_task-wait-to-begin-feature"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    choose_team_according_to_stage_data_and_config(self, current_task_stage_data)
    start_mission(self)
    check_skip_fight_and_auto_over(self)
    start_action(self, current_task_stage_data['action'])


def retreat(self):
    rgb_possibles = {"fighting_feature": (1226, 51)}
    img_possible = {
        'normal_task_fight-pause': (908, 508),
        'normal_task_retreat-notice': (768, 507)
    }
    img_ends = 'normal_task_fail-confirm'
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possible, True)


def formation_attr_to_cn(attr):
    if attr.startswith('pierce'):
        return '贯穿'
    elif attr.startswith('burst'):
        return '爆发'
    elif attr.startswith('mystic'):
        return '神秘'
    elif attr.startswith('shock'):
        return '振动'
    return None
