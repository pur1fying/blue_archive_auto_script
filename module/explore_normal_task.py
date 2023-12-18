import importlib
import time

import cv2
import numpy as np

from core import color, image
from module import main_story, normal_task
from src import explore_task_data

x = {
}


def implement(self):
    if self.server == 'CN':
        possible = {
            'main_page_home-feature': (1195, 576, 3),
            'main_page_bus': (815, 285, 3),
        }
        image.detect(self, 'normal_task_menu', possible)
        choose_mode(self)

    elif self.server == "Global":
        normal_task.to_normal_event(self)
    for i in range(0, len(self.config['explore_normal_task_regions'])):
        region = self.config['explore_normal_task_regions'][i]
        if not 4 <= region <= 16:
            self.logger.warning("Region not support")
            return True
        choose_region(self, region)
        self.stage_data = get_stage_data(region)
        start_fight(self, region)


def choose_mode(self):
    while not color.judge_rgb_range(self.latest_img_array, 680, 138, 36, 56, 56, 76, 77, 97):
        self.click(927, 147)
        time.sleep(1)
        self.latest_img_array = self.get_screenshot_array()


def start_fight(self, region):
    mission = calc_need_fight_stage(self, region)
    if mission == "ALL MISSION SWEEP AVAILABLE":
        self.logger.critical("ALL MISSION AVAILABLE TO SWEEP")
        return "ALL MISSION SSS"
    if mission == 'SUB':
        self.click(645, 511)
        start_choose_side_team(self, self.config[self.stage_data[str(region)]['SUB']])
        time.sleep(1)
        self.click(1171, 670)
    else:
        prev_index = 0
        for n, p in self.stage_data[mission]['start'].items():
            cu_index = choose_team(self, mission, n)
            if cu_index < prev_index:
                self.exit("please set the first formation number smaller than the second one")
            prev_index = cu_index
        start_mission(self)
        image.compare_image(self, 'normal_task_fight-skip', threshold=3)
        image.compare_image(self, 'normal_task_auto-over', threshold=3)
        start_action(self, mission, self.stage_data)
    main_story.auto_fight(self)
    if self.config['manual_boss']:
        self.click(1235, 41)
    end = ('normal_task_menu', 3)
    possible = {
        'normal_task_auto-over': (1082, 599, 3),
        'normal_task_task-finish': (1038, 662, 3),
        'normal_task_prize-confirm': (776, 655, 3),
        'main_story_fight-confirm': (1168, 659, 3),
    }
    image.detect(self, end, possible)
    choose_region(self, region - 1)
    choose_region(self, region)
    return start_fight(self, region)


def get_stage_data(region):
    module_path = 'src.explore_task_data.normal_task_' + str(region)
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
    """
    结束回合
    """
    click_pos1 = [
        [1170, 670],
        [794, 207],
    ]
    lo1 = [
        "normal_task_mission_operating",
        "present",
    ]
    end1 = ["round_over_notice"]
    color.common_rgb_detect_method(self, click_pos1, lo1, end1)
    click_pos2 = [[767, 501]]
    lo2 = ["round_over_notice"]
    end2 = ["normal_task_mission_operating"]
    color.common_rgb_detect_method(self, click_pos2, lo2, end2)


def confirm_teleport(self):
    """
    确认传送并回到任务进行中界面
    """
    end1 = ["formation_teleport_notice"]
    color.common_rgb_detect_method(self, [], [], end1)
    click_pos2 = [[767, 501]]
    lo2 = ["formation_teleport_notice"]
    end2 = ["normal_task_mission_operating"]
    color.common_rgb_detect_method(self, click_pos2, lo2, end2)


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
            self.click(*act['p'])
        elif act['t'] == 'exchange':
            self.click(83, 557)
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
        if i != len(actions) - 1:
            to_normal_task_mission_operation_page(self)


def start_choose_side_team(self, index):
    if index not in [1, 2, 3, 4]:
        self.exit("No formation added into corresponding config")
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
    while cu_region != region:
        if cu_region > region:
            self.click(40, 360, wait=False, count=cu_region - region, rate=0.1)
        else:
            self.click(1245, 360, wait=False, count=region - cu_region, rate=0.1)
        self.latest_img_array = self.get_screenshot_array()
        cu_region = int(self.ocrNUM.ocr_for_single_line(self.latest_img_array[178:208, 122:163, :])['text'])


def choose_team(self, mission_num, force):
    index = self.config[self.stage_data[mission_num]['attr'][force]]
    self.logger.info("According to the config. Choose formation {0}".format(index))
    if index not in [1, 2, 3, 4]:
        self.exit("No formation added into corresponding config")
    to_formation_edit_i(self, index, self.stage_data[mission_num]['start'][force])
    if color.judge_rgb_range(self.latest_img_array, 1166, 684, 250, 255, 105, 125, 68, 88) \
        and color.judge_rgb_range(self.latest_img_array, 1156, 626, 250, 255, 105, 125, 68, 88):
        self.exit("please choose another formation")
    to_normal_task_wait_to_begin_page(self)
    return index


def to_normal_task_mission_operation_page(self):
    click_pos = [
        [886, 162],
        [890, 162],
        [995, 102],
        [794, 207],
    ]
    los = [
        "formation_teleport_notice",
        "round_over_notice",
        "normal_task_mission_info",
        "present",
    ]
    ends = ["normal_task_mission_operating"]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def to_normal_task_wait_to_begin_page(self):
    click_pos = [
        [995, 101],
        [1154, 659],
        [1154, 659],
        [1154, 659],
        [1154, 659],
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
    color.common_rgb_detect_method(self, click_pos, los, ends)


def wait_over(self):
    click_pos1 = [
        [998, 670],
        [886, 162],
        [794, 207],
    ]
    lo1 = [
        "normal_task_mission_operating",
        "formation_teleport_notice",
        "present",
    ]
    end1 = ["normal_task_mission_info"]
    color.common_rgb_detect_method(self, click_pos1, lo1, end1)


def start_mission(self):
    end = "normal_task_task-operating-feature"
    possible = {
        'normal_task_fight-task': (1171, 670, 3),
        'normal_task_task-begin-without-further-editing-notice': (768, 498, 3),
        'normal_task_task-operating-round-over-notice': (888, 163, 3)
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
