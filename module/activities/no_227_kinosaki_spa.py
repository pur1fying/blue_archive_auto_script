import importlib
import time

from core import color, image
from module import main_story

x = {
    'enter1': (1180, 180, 1202, 200),
    'enter2': (96, 140, 116, 150),
    'menu': (103, 7, 167, 38),
    'play-guide': (535, 132, 656, 171),
    'story-fight-success-confirm': (602, 644, 677, 689)
}


def implement(self):
    self.stage_data = get_stage_data()
    self.quick_method_to_main_page()
    # explore_story(self)
    explore_mission(self)
    # explore_challenge(self)
    return True


def check_sweep_availability(img):
    if color.judge_rgb_range(img, 211, 369, 192, 212, 192, 212, 192, 212) and \
        color.judge_rgb_range(img, 211, 402, 192, 212, 192, 212, 192, 212) and \
        color.judge_rgb_range(img, 211, 436, 192, 212, 192, 212, 192, 212):
        return "no-pass"
    if color.judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) and \
        color.judge_rgb_range(img, 211, 404, 225, 255, 200, 255, 20, 60) and \
        color.judge_rgb_range(img, 211, 434, 225, 255, 200, 255, 20, 60):
        return "sss"
    if color.judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) or \
        color.judge_rgb_range(img, 211, 404, 225, 255, 200, 255, 20, 60) or \
        color.judge_rgb_range(img, 211, 434, 225, 255, 200, 255, 20, 60):
        return "pass"


def explore_story(self):
    for counts in range(0, 7):
        to_no_227_kinosaki_spa(self, 'story', True)
        line = self.latest_img_array[:, 1086, :]
        los = []
        possibles = {
            "activity_menu": (1086, 0)
        }
        ends = "normal_task_task-info"
        i = 590
        while i > 196:
            if 131 <= line[i][2] <= 151 and 218 <= line[i][1] <= 238 and 245 <= line[i][0] <= 255 and \
                131 <= line[i - 30][2] <= 151 and 218 <= line[i - 30][1] <= 238 and 245 <= line[i - 30][0] <= 255:
                los.append(i - 35)
                i -= 100
            else:
                i -= 1
        print(los)
        for i in range(0, len(los)):
            possibles["activity_menu"] = (1086, los[i])
            image.detect(self, ends, possibles)
            res = check_sweep_availability(self.latest_img_array)
            if res == "pass" or res == "no-pass":
                start_story(self)
                break
            elif res == "sss":
                to_no_227_kinosaki_spa(self, 'story')


def start_story(self):
    possibles = {
        "normal_task_task-info": (942, 543),
        "normal_task-force-edit": (1154, 657),
        'normal_task_task-finish': (1038, 662),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fail-confirm': (643, 658),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
        'activity_story-fight-success-confirm': (638, 674)
    }
    ends = "activity_menu"
    image.detect(self, ends, possibles)


def calc_task_state(self):
    for i in range(0, 12):
        res = check_sweep_availability(self.latest_img_array)
        if res == "pass" or res == "no-pass":
            return i
        elif res == "sss":
            self.click(1171, 346, wait_over=True)
            time.sleep(0.5)
            self.latest_img_array = self.get_screenshot_array()
    return "ALL-COMPLETE"


def explore_mission(self):
    while True:
        to_no_227_kinosaki_spa(self, 'mission', True)
        self.swipe(914, 151, 921, 584, 0.1)
        time.sleep(1)
        possibles = {
            "activity_menu": (1123, 203)
        }
        ends = "normal_task_task-info"
        image.detect(self, ends, possibles, skip_first_screenshot=True)
        id = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        work = ['sub', 'sub', 'sub', 'gird', 'sub', 'sub', 'sub', 'gird', 'sub', 'sub', 'sub', 'gird']
        task_state = calc_task_state(self)
        if task_state == "ALL-COMPLETE":
            return True
        else:
            current_task_stage = self.stage_data[id[task_state]]
            if work[task_state] == 'sub':
                self.click(933, 536, wait_over=True)
                start_choose_side_team(self, self.config[current_task_stage['attr']])
                time.sleep(1)
                self.click(1171, 670, wait_over=True)
            elif work[task_state] == 'gird':
                possibles = {
                    'normal_task_help': (1017, 131),
                    'normal_task_task-info': (946, 540)
                }
                image.detect(self, possibles=possibles, pre_func=color.detect_rgb_one_time,
                             pre_argv=(self, [], [], ['normal_task_wait_to_begin_page']), skip_first_screenshot=True)
                prev_index = 0
                for n, p in current_task_stage['start'].items():
                    cu_index = choose_team(self, self.config[current_task_stage['attr'][n]], p)
                    if cu_index < prev_index:
                        self.logger.critical("please set the first formation number smaller than the second one")
                        return False
                    prev_index = cu_index
                start_mission(self)
                if not image.compare_image(self, 'normal_task_fight-skip', threshold=3,
                                           image=self.latest_img_array):
                    self.click(1194, 547)
                if not image.compare_image(self, 'normal_task_auto-over', threshold=3, image=self.latest_img_array):
                    self.click(1194, 600)
                self.set_screenshot_interval(1)
                start_action(self, self.stage_data[id[task_state]]['action'])
                self.set_screenshot_interval(self.config['screenshot_interval'])
            main_story.auto_fight(self)
            if self.config['manual_boss'] and work[task_state] == 'gird':
                self.logger.info("Manual Boss Fight, Wait human take over")
                self.click(1235, 41)
            to_no_227_kinosaki_spa(self, 'story')
            to_no_227_kinosaki_spa(self, 'mission', True)


def explore_challenge(self):
    to_no_227_kinosaki_spa(self, 'challenge',True)


def to_no_227_kinosaki_spa(self, region, skip_first_screenshot=False):
    possibles = {
        "activity_enter1": (1196, 195),
        "activity_enter2": (100, 149),
        "main_page_home-feature": (1198, 580),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "plot_skip-plot-notice": (766, 520),
        "normal_task_help": (1017, 131),
        "activity_play-guide": (1184, 152),
        'main_story_fight-confirm': (1168, 659),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fail-confirm': (643, 658),
        'normal_task_task-finish': (1038, 662),
        'activity_story-fight-success-confirm': (638, 674)
    }
    ends = "activity_menu"
    image.detect(self, ends, possibles, skip_first_screenshot=skip_first_screenshot)
    if region == 'mission':
        rgb_lo = 863
        click_lo = 1027
    elif region == 'story':
        rgb_lo = 688
        click_lo = 848
    elif region == 'challenge':
        rgb_lo = 1046
        click_lo = 1196
    while True:
        if not self.flag_run:
            return False
        if not color.judge_rgb_range(self.latest_img_array, rgb_lo, 134, 20, 60, 40, 70, 70, 100):
            self.click(click_lo, 90)
            time.sleep(self.screenshot_interval)
            self.latest_img_array = self.get_screenshot_array()
        else:
            return True


def explore_no_227_kinosaki(self):
    pass


def get_stage_data():
    module_path = 'src.explore_task_data.activities.no_227_kinosaki_spa'
    stage_module = importlib.import_module(module_path)
    stage_data = getattr(stage_module, 'stage_data', None)
    return stage_data


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


def start_mission(self):
    possible = {
        'normal_task_fight-task': (1171, 670, 3),
        'normal_task_task-begin-without-further-editing-notice': (768, 498, 3),
        'normal_task_task-operating-round-over-notice': (888, 163, 3)
    }
    end = "normal_task_task-operating-feature"
    image.detect(self, end, possible)


def start_action(self, actions):
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


def choose_team(self, i, lo):
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
    to_normal_task_wait_to_begin_page(self)
    return i


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


def confirm_teleport(self):
    if self.server == 'CN':
        end1 = ["formation_teleport_notice"]
        color.common_rgb_detect_method(self, [], [], end1)
        click_pos2 = [[767, 501]]
        lo2 = ["formation_teleport_notice"]
        end2 = ["normal_task_mission_operating"]
        color.common_rgb_detect_method(self, click_pos2, lo2, end2)
    elif self.server == 'Global':
        image.detect(self, 'normal_task_formation-teleport-notice')
        possibles = {
            'normal_task_formation-teleport-notice': (767, 501),
        }
        end = 'normal_task_mission-operating-feature'
        image.detect(self, end, possibles)


def end_round(self):
    if self.server == 'CN':
        click_pos1 = [
            [1170, 670],
        ]
        lo1 = [
            "normal_task_mission_operating",
        ]
        end1 = ["round_over_notice"]
        color.common_rgb_detect_method(self, click_pos1, lo1, end1)
        click_pos2 = [[767, 501]]
        lo2 = ["round_over_notice"]
        end2 = ["normal_task_mission_operating"]
        color.common_rgb_detect_method(self, click_pos2, lo2, end2)
    elif self.server == 'Global':
        possibles = {
            'normal_task_mission-operating-feature': (1170, 670),
        }
        end = 'normal_task_end-phase-notice'
        image.detect(self, end, possibles)
        possibles = {
            'normal_task_end-phase-notice': (767, 501),
        }
        end = 'normal_task_mission-operating-feature'
        image.detect(self, end, possibles)


def get_force(self):
    self.latest_img_array = self.get_screenshot_array()
    img = self.latest_img_array[542:570, 116:131]
    ocr_res = self.ocrNUM.ocr_for_single_line(img)["text"]
    if ocr_res == "":
        return get_force(self)
    if ocr_res == "7":
        return 1
    return int(ocr_res)


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
