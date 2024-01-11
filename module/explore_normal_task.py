import importlib
import time

from core import color, image
from module import main_story, normal_task


def implement(self):
    self.scheduler.change_display("普通关推图")
    self.quick_method_to_main_page()
    # test_(self)
    normal_task.to_normal_event(self, True)
    for i in range(0, len(self.config['explore_normal_task_regions'])):
        region = self.config['explore_normal_task_regions'][i]
        if not 4 <= region <= 16:
            self.logger.warning("Region not support")
            return True
        choose_region(self, region)
        self.stage_data = get_stage_data(region)
        start_fight(self, region)
    return True


def start_fight(self, region):
    mission = calc_need_fight_stage(self, region)
    if mission == "ALL MISSION SWEEP AVAILABLE":
        self.logger.critical("ALL MISSION AVAILABLE TO SWEEP")
        normal_task.to_normal_event(self, True)
        return "ALL MISSION SSS"
    if mission == 'SUB':
        self.click(645, 511, wait_over=True)
        start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
        time.sleep(1)
        self.click(1171, 670, wait_over=True)
        self.set_screenshot_interval(1)
    else:
        possibles = {
            'normal_task_help': (1017, 131),
            'normal_task_task-info': (946, 540)
        }
        if self.server == 'CN':
            image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time,
                         pre_argv=(self, [], [], ['normal_task_wait_to_begin_page']), skip_first_screenshot=True)
        elif self.server == 'Global':
            image.detect(self, end='normal_task_mission-wait-to-begin-feature', possibles=possibles,
                         skip_first_screenshot=True)
        prev_index = 0
        for n, p in self.stage_data[mission]['start'].items():
            cu_index = choose_team(self, mission, n)
            if cu_index < prev_index:
                self.logger.critical("please set the first formation number smaller than the second one")
                return False
            prev_index = cu_index
        start_mission(self)
        if self.server == 'CN':
            if not image.compare_image(self, 'normal_task_fight-skip', threshold=3, image=self.latest_img_array):
                self.click(1194, 547)
            if not image.compare_image(self, 'normal_task_auto-over', threshold=3, image=self.latest_img_array):
                self.click(1194, 600)
        elif self.server == 'Global':
            if not color.judge_rgb_range(self.latest_img_array, 1096, 550, 65, 105, 213, 255, 235, 255):
                self.click(1194, 547)
            if not color.judge_rgb_range(self.latest_img_array, 1048, 604, 65, 105, 213, 255, 235, 255):
                self.click(1194, 601)
        self.set_screenshot_interval(1)
        start_action(self, mission, self.stage_data)
    main_story.auto_fight(self)
    self.set_screenshot_interval(self.config['screenshot_interval'])
    if self.config['manual_boss'] and mission != 'SUB':
        self.click(1235, 41)

    normal_task.to_normal_event(self)
    choose_region(self, region - 1)
    choose_region(self, region)
    return start_fight(self, region)


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
    to_mission_info(self)
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
    self.latest_img_array = self.get_screenshot_array()
    img = self.latest_img_array[542:570, 116:131]
    ocr_res = self.ocrNUM.ocr_for_single_line(img)["text"]
    if ocr_res == "":
        return get_force(self)
    if ocr_res == "7":
        return 1
    return int(ocr_res)


def end_round(self):
    if self.server == 'CN':
        click_pos1 = [
            [1170, 670],
        ]
        lo1 = [
            "normal_task_mission_operating",
        ]
        end1 = ["round_over_notice"]
        color.common_rgb_detect_method(self, click_pos1, lo1, end1, skip_first_screenshot=True)
        click_pos2 = [[767, 501]]
        lo2 = ["round_over_notice"]
        end2 = ["normal_task_mission_operating"]
        color.common_rgb_detect_method(self, click_pos2, lo2, end2, skip_first_screenshot=True)
    elif self.server == 'Global':
        possibles = {
            'normal_task_mission-operating-feature': (1170, 670),
        }
        end = 'normal_task_end-phase-notice'
        image.detect(self, end, possibles, skip_first_screenshot=True)
        possibles = {
            'normal_task_end-phase-notice': (767, 501),
        }
        end = 'normal_task_mission-operating-feature'
        image.detect(self, end, possibles, skip_first_screenshot=True)


def confirm_teleport(self):
    if self.server == 'CN':
        end1 = ["formation_teleport_notice"]
        color.common_rgb_detect_method(self, [], [], end1)
        click_pos2 = [[767, 501]]
        lo2 = ["formation_teleport_notice"]
        end2 = ["normal_task_mission_operating"]
        color.common_rgb_detect_method(self, click_pos2, lo2, end2, skip_first_screenshot=True)
    elif self.server == 'Global':
        image.detect(self, 'normal_task_formation-teleport-notice')
        possibles = {
            'normal_task_formation-teleport-notice': (767, 501),
        }
        end = 'normal_task_mission-operating-feature'
        image.detect(self, end, possibles, skip_first_screenshot=True)


def start_action(self, gk, stage_data):
    actions = stage_data[gk]['action']
    for i, act in enumerate(actions):
        if 'before' in act:
            self.logger.info("wait {0} seconds".format(act['before']))
            time.sleep(act['before'])
        time.sleep(1)
        msg = "start {0} operation".format(i + 1)
        if 'desc' in act:
            msg += ' desc:{0}'.format(act['desc'])
        self.logger.info(msg)
        force_index = get_force(self)
        if act['t'] == 'click':
            self.click(*act['p'], wait_over=True)
        elif act['t'] == 'exchange':
            self.click(83, 557, wait_over=True)
        elif act['t'] == 'move':
            confirm_teleport(self)
        elif act['t'] == 'end-turn':
            end_round(self)
        if 'ec' in act:
            self.logger.info("wait change formation.")
            origin = force_index
            while force_index == origin:
                force_index = get_force(self)
        if 'after' in act:
            self.logger.info("wait {0} seconds".format(act['after']))
            time.sleep(act['after'])

        if 'wait-over' in act:
            self.logger.info("wait move available")
            wait_over(self)
            time.sleep(2)
        if i != len(actions) - 1 and 'ensure-ui' not in act:
            to_normal_task_mission_operation_page(self)


def start_choose_side_team(self, index):
    self.logger.info("According to the config. Choose formation {0}".format(index))
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
    cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])
    while cu_region != region and self.flag_run:
        if cu_region > region:
            self.click(40, 360, wait=False, count=cu_region - region, rate=0.1)
        else:
            self.click(1245, 360, wait=False, count=region - cu_region, rate=0.1)
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()
        cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])


def choose_team(self, mission_num, force):
    index = self.config[self.stage_data[mission_num]['attr'][force]]
    self.logger.info("According to the config. Choose formation {0}".format(index))
    if index not in [1, 2, 3, 4]:
        exit("No formation added into corresponding config")
    to_formation_edit_i(self, index, self.stage_data[mission_num]['start'][force])
    if color.judge_rgb_range(self.latest_img_array, 1166, 684, 250, 255, 105, 125, 68, 88) \
        and color.judge_rgb_range(self.latest_img_array, 1156, 626, 250, 255, 105, 125, 68, 88):
        exit("please choose another formation")
    to_normal_task_wait_to_begin_page(self)
    return index


def to_normal_task_mission_operation_page(self):
    click_pos = [
        [886, 162],
        [890, 162],
        [995, 102],
    ]
    los = [
        "formation_teleport_notice",
        "round_over_notice",
        "normal_task_mission_info",
    ]
    ends = ["normal_task_mission_operating"]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def to_normal_task_wait_to_begin_page(self):
    click_pos = [
        [995, 101],
        [1154, 625],
        [1154, 625],
        [1154, 625],
        [1154, 625],
    ]
    los = [
        "mission_info",
        "formation_edit1",
        "formation_edit2",
        "formation_edit3",
        "formation_edit4",
    ]
    ends = [
        "normal_task_wait_to_begin_page"
    ]
    if self.server == 'Global':
        click_pos.pop(0)
        los.pop(0)
        possibles = {
            'normal_task_add-ally-notice': (888, 164)
        }
        ends = [
            'normal_task_mission-wait-to-begin-feature',
            'normal_task_mission-operating-feature'
        ]
        image.detect(self, possibles=possibles, end=ends, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, []))
    elif self.server == 'CN':
        color.common_rgb_detect_method(self, click_pos, los, ends)


def to_formation_edit_i(self, i, lo):
    loy = [195, 275, 354, 423]
    y = loy[i - 1]
    click_pos = [
        [lo[0], lo[1]],
        [74, y],
        [74, y],
        [74, y],
        [74, y],
    ]
    los = [
        "normal_task_wait_to_begin_page",
        "formation_edit1",
        "formation_edit2",
        "formation_edit3",
        "formation_edit4",
    ]
    ends = [
        "formation_edit" + str(i)
    ]
    los.pop(i)
    click_pos.pop(i)
    if self.server == 'Global':
        click_pos.pop(0)
        los.pop(0)
        possibles = {
            'normal_task_mission-wait-to-begin-feature': (lo[0], lo[1]),
        }
        image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time,
                     pre_argv=(self, click_pos, los, ends))
    elif self.server == 'CN':
        color.common_rgb_detect_method(self, click_pos, los, ends)


def wait_over(self):
    click_pos1 = [
        [998, 670],
        [886, 162],
    ]
    lo1 = [
        "normal_task_mission_operating",
        "formation_teleport_notice",
    ]
    end1 = ["normal_task_mission_info"]
    color.common_rgb_detect_method(self, click_pos1, lo1, end1)


def start_mission(self):
    if self.server == 'CN':
        end = "normal_task_task-operating-feature"
        possible = {
            'normal_task_fight-task': (1171, 670, 3),
            'normal_task_task-begin-without-further-editing-notice': (768, 498, 3),
            'normal_task_task-operating-round-over-notice': (888, 163, 3)
        }
    elif self.server == 'Global':
        end = "normal_task_mission-operating-feature"
        possible = {
            'normal_task_mission-wait-to-begin-feature': (1171, 670),
            'normal_task_end-phase-notice': (888, 163),
            'normal_task_add-ally-notice': (768, 498)
        }
    image.detect(self, end, possible)


def to_mission_info(self):
    if self.server == 'CN':
        end = "normal_task_task-info"
        possible = {
            'normal_task_menu': (1106, 249, 3),
        }
        image.detect(self, end, possible)
    elif self.server == 'Global':
        end = "normal_task_Main-mission-info"
        possible = {
            'normal_task_select-area': (1114, 240, 3),
        }
        image.detect(self, end, possible)


def test_(self):
    region = 16
    normal_task.to_normal_event(self)
    choose_region(self, region)
    self.stage_data = get_stage_data(region)
    for i in range(1, 6):
        self.swipe(917, 220, 917, 552, duration=0.1)
        time.sleep(1)
        to_mission_info(self)
        for j in range(1, i):
            self.click(1172, 358, wait=False)
            time.sleep(1)
        mission = str(region) + '-' + str(i)
        possibles = {
            'normal_task_help': (1017, 131),
            'normal_task_task-info': (946, 540)
        }
        if self.server == 'CN':
            image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time,
                         pre_argv=(self, [], [], ['normal_task_wait_to_begin_page']))
        elif self.server == 'Global':
            image.detect(self, end='normal_task_mission-wait-to-begin-feature', possibles=possibles)
        prev_index = 0
        for n, p in self.stage_data[mission]['start'].items():
            cu_index = choose_team(self, mission, n)
            if cu_index < prev_index:
                exit("please set the first formation number smaller than the second one")
            prev_index = cu_index
        start_mission(self)
        if self.server == 'CN':
            if not image.compare_image(self, 'normal_task_fight-skip', threshold=3, image=self.latest_img_array):
                self.click(1194, 547)
            if not image.compare_image(self, 'normal_task_auto-over', threshold=3, image=self.latest_img_array):
                self.click(1194, 600)
        elif self.server == 'Global':
            if not color.judge_rgb_range(self.latest_img_array, 1096, 550, 65, 105, 213, 255, 235, 255):
                self.click(1194, 547)
            if not color.judge_rgb_range(self.latest_img_array, 1048, 604, 65, 105, 213, 255, 235, 255):
                self.click(1194, 601)
        start_action(self, mission, self.stage_data)
        main_story.auto_fight(self)
        if self.config['manual_boss']:
            self.click(1235, 41)

        normal_task.to_normal_event(self)
        choose_region(self, region - 1)
        choose_region(self, region)
