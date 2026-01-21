import time
import numpy as np
from math import floor
from datetime import datetime

from core.image import search_in_area, resize_ss_image, check_geometry_pixels, swipe_search_target_str
from core.color import rgb_in_range
from core.geometry.parallelogram import Parallelogram
from core.picture import GAME_ONE_TIME_POP_UPS, co_detect
from module.main_story import set_acc_and_auto

FINAL_RESTRICTION_RLS_CLEAR_UNIT_ROW_COUNT = 4
FINAL_RESTRICTION_RLS_FRONT_STUDENT_CNT = 6
FINAL_RESTRICTION_RLS_BACK_STUDENT_CNT = 4
FINAL_RESTRICTION_RLS_MAX_CHARACTER_COUNT = FINAL_RESTRICTION_RLS_FRONT_STUDENT_CNT + FINAL_RESTRICTION_RLS_BACK_STUDENT_CNT
FINAL_RESTRICTION_RLS_MAX_STAGE = 124
FINAL_RESTRICTION_RLS_MAX_STAGE_LIST = [24, 49, 74, 99, 124]
FINAL_RESTRICTION_RLS_PIXEL_STAGE_NOT_SELECTED = [66, 126, 60, 146, 128, 188]
FINAL_RESTRICTION_RLS_PIXEL_STAGE_SELECTED = [184, 224, 178, 218, 204, 255]

def implement(self):
    self.to_main_page()
    to_page_select_stage_menu(self)
    open_ = True if get_open_state(self) == "Open" else False
    curr_stage = get_highest_passed_stage(self)
    if open_ :
        detect_battle_open_time(self)
        if curr_stage == FINAL_RESTRICTION_RLS_MAX_STAGE:
            self.logger.info("Already Passed Highest Stage, Quit")
        else:
            push_stage(self, curr_stage)
    else:
        detect_battle_next_open_time(self)
    return True

def detect_battle_next_open_time(self):
    self.logger.info("Detect Battle Next Open Time")
    ocr_region = (221, 653, 274, 680)
    text = self.ocr.get_region_res(
        self,
        ocr_region,
        "en-us",
        "Final Restriction Rls Battle Next Open Time",
        "0123456789/"
    )
    fmt = {
        "CN": "%Y/%m/%d",
        "Global_zh-tw": "%Y/%m-%d",
        "Global_en-us": "%Y/%m/%d",
        "Global_ko-kr": "%Y/%m-%d",
        "JP": "%Y/%m/%d"
    }[self.identifier]
    now = datetime.now()
    year = now.year
    next_open = datetime.strptime(f"{year}/{text.strip()}", fmt)
    next_open = next_open.replace(hour=10 if self.server in ["JP", "Global"] else 11)
    if next_open < now:
        next_open = next_open.replace(year=year + 1)
    self.logger.info(f"Next Open Time : {next_open}")
    set_final_restriction_rls_config_info(self, "next_open_time", next_open.timestamp())

def detect_battle_open_time(self):
    self.logger.info("Detect Battle Open Time")

    ocr_region = (138, 653, 410, 680)
    text = self.ocr.get_region_res(
        self,
        ocr_region,
        "en-us",
        "Final Restriction Rls Battle Open Time",
        "0123456789/:~- "
    )

    fmt = {
        "CN": "%Y/%m/%d %H:%M",
        "Global_en-us": "%Y/%m/%d %H:%M",
        "Global_ko-kr": "%Y/%m-%d %H:%M",
        "Global_zh-tw": "%Y/%m-%d %H:%M",
        "JP": "%Y/%m/%d %H:%M"
    }[self.identifier]

    now = datetime.now()
    year = now.year

    pos = text.find('~')
    if pos == -1:
        pos = text.find('-')
    if pos == -1:
        self.logger.info(f"Failed to detect battle open time from text [{text}], quit")
        return
    start_str, end_str= text[:pos], text[pos+1:]
    start_str = start_str.strip()
    end_str = end_str.strip()

    start = datetime.strptime(f"{year}/{start_str}", fmt)
    end   = datetime.strptime(f"{year}/{end_str}", fmt)

    if end < start:
        if now >= start:
            end = end.replace(year=year + 1)
        else:
            start = start.replace(year=year - 1)

    self.logger.info(f"Start : {start}")
    self.logger.info(f"End   : {end}")

    set_final_restriction_rls_config_info(self, "start_time", start.timestamp())
    set_final_restriction_rls_config_info(self, "end_time", end.timestamp())

def push_stage(self, start):
    """
        Push final restriction rls to the highest stage
    """
    index = get_next_max_stage_index(start)
    _need_select_stage = True
    while index is not None:
        stage_index = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[index]
        self.logger.info(f"<<< Stage {stage_index} >>>")
        if _need_select_stage:
            to_page_select_stage(self, True)
            select_stage(self, index)
            _need_select_stage = False
        else:
            to_page_select_stage(self, False)
            to_page_select_accurate_stage(self)
        if not select_accurate_stage(self, stage_index, index):
            return
        if complete_battle(self):
            set_final_restriction_rls_config_info(self, "passed_stage", stage_index)
            index = get_next_max_stage_index(stage_index)
            start = stage_index
            if index is None:
                self.logger.info("Passed Highest Stage, Quit")
                return
        else:
            break

    l = start + 1
    r = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[index]
    while l + 1 <= r:
        mid = floor((l + r) / 2)
        self.logger.info(f"<<< Stage {mid} >>>")
        if not select_accurate_stage(self, mid, index):
            return False
        if complete_battle(self):
            set_final_restriction_rls_config_info(self, "passed_stage", True)
            l = mid + 1
        else:
            r = mid
    return l

def set_final_restriction_rls_config_info(self, key, value):
    data = self.config.final_restriction_rls
    data[key] = value
    self.config_set.set("final_restriction_rls", data)

def complete_battle(self):
    """
        Returns:
            True if battle succeeded else False
    """
    self.logger.info("Start Battle")
    method = self.config.final_restriction_rls_employ_formation_method
    self.logger.info(f"Employ Formation Method : [ {method} ]")
    if method == "copy_clear_unit":
        ret = select_and_copy_clear_unit(self)
        if ret == 0:
            employ_team_from_preset(self, 1, 1)
        elif ret in [-1, 1]: # empty unit or failed to find a unit available
            return False
    elif method == "default":
        pass
    enter_battle(self)
    set_acc_and_auto(self)
    ret = wait_battle_result(self)
    log = "Battle " + ("SUCCEEDED" if ret else "FAILED")
    self.logger.info(log)

    self.logger.info("Return to page Select Accurate Stage.")
    to_page_select_accurate_stage(self)
    return ret


def enter_battle(self):
    img_possibles = {
        "final_restriction_rls_button-enter-stage": (1134, 650),
        "final_restriction_rls_formation-menu": (1175, 665),
        "main_page_skip-notice": (769, 503),
        'plot_menu': (1202, 37),
        'plot_skip-plot-button': (1208, 116),
        'plot_skip-plot-notice': (770, 519)
    }
    img_ends = [
        "normal_task_fail-confirm",
        "normal_task_fight-confirm"
    ]
    rgb_end = "final-restriction-rls-fighting_feature"
    co_detect(self, rgb_end, None, img_ends, img_possibles, tentative_click=True, tentative_x=640, tentative_y=360, max_fail_cnt=5)

def wait_battle_result(self):
    self.logger.info("Wait Battle Result")
    rgb_possibles = {
        "final-restriction-rls-fighting_feature": (-1, -1)
    }
    img_possibles = {
        "main_page_skip-notice": (769, 503)
    }
    img_ends = [
        "normal_task_fail-confirm",
        "normal_task_fight-confirm"
    ]
    if "normal_task_fail-confirm" == co_detect(self, None, rgb_possibles, img_ends, img_possibles,  tentative_click=True, tentative_x=640, tentative_y=360, max_fail_cnt=5)  :
        return False
    return True

def select_and_copy_clear_unit(self):
    """
        Returns:
            0  : Successfully choose a team
            1  : Failed to choose a team with passed characters
            -1 : All team empty, skip this fight
    """
    self.logger.info("Select Clear Unit")
    _max_absent = self.config.final_restriction_rls_employ_formation_copy_clear_unit_max_unavailable_student_count
    _max_refresh = self.config.final_restriction_rls_employ_formation_copy_clear_unit_max_refresh_count
    self.logger.info(f"Max Absent Character : {_max_absent}")
    self.logger.info(f"Max Refresh Time     : {_max_refresh}")

    to_page_clear_unit(self)

    _refresh_cnt = 0
    _ret = 1
    while _refresh_cnt < _max_refresh:
        _t_start = time.time()
        state = get_clear_unit_state(self)
        _t_end = time.time()
        ret = log_clear_unit_info(self, state, _max_absent, _t_end - _t_start)
        if ret == -1:
            self.logger.info("Empty unit detected assume no one ever passed this stage, Skip")
            _ret =  -1
            break
        if ret is not None:
            copy_clear_unit(self, ret)
            _ret = 0
            break
        _refresh_cnt += 1
        self.logger.info(f"Refresh Clear Unit List : {_refresh_cnt}")
        self.click(248, 133, duration=1.0, wait_over=True)
        self.update_screenshot_array()

    if _ret == 1:
        self.logger.info("Failed to choose a clear unit with available characters, use default team")

    to_page_select_accurate_stage(self)
    return _ret

def copy_clear_unit(self, index):
    # Copy clear unit to preset col 1 row 1
    button_copy_y = [228, 333, 442, 547][index]
    img_possibles = {
        "final_restriction_rls_clear-unit-menu": (1064, button_copy_y),
        "final_restriction_rls_copy-clear-unit-student-unavailable-notice": (763, 498)
    }
    img_end = "final_restriction_rls_formation-overwrite-menu"
    co_detect(self, None, None, img_end, img_possibles, skip_first_screenshot=True)
    img_possibles = {
        "final_restriction_rls_formation-overwrite-menu": (1123, 359),
        "final_restriction_rls_formation-overwrite-notice": (763, 574),
        "final_restriction_rls_formation-overwrite-success-notice": (640, 503),
        "final_restriction_rls_clear-unit-menu": (1103, 135)
    }
    img_end = "final_restriction_rls_button-enter-stage"
    co_detect(self, None, None, img_end, img_possibles, skip_first_screenshot=True)

def employ_team_from_preset(self, col=1, row=1):
    img_possibles = {
        "final_restriction_rls_button-enter-stage" : (1143, 660)
    }
    img_ends = "final_restriction_rls_formation-menu"
    co_detect(self, img_reactions=img_possibles, img_ends=img_ends, skip_first_screenshot=True)

    img_possibles = {
        "final_restriction_rls_formation-menu": (1204, 486),
        "normal_task_formation-preset": (178 + (col - 1) * 156, 153)
    }
    rgb_ends = "preset_choose" + str(col)
    co_detect(self, img_reactions=img_possibles, rgb_ends=rgb_ends, skip_first_screenshot=True)

    offsets = {
        'CN': (-1103, 0, 16, 33),
        'Global_en-us': (-1048, -4, 20, 36),
        'Global_ko-kr': (-1105, -4, 20, 36),
        'Global_zh-tw': (-1105, -4, 20, 36),
        'JP': (-1103, 0, 16, 33)
    }

    presetButtonPos = swipe_search_target_str(
        self,
        "normal_task_formation-edit-preset-name",
        search_area=(1156, 201, 1229, 553),
        threshold=0.8,
        possible_strs=["1", "2", "3", "4", "5"],
        target_str_index=row - 1,
        swipe_params=(145, 578, 145, 273, 1.0, 0.5),
        ocr_language="en-us",
        ocr_region_offsets=offsets[self.identifier],
        ocr_str_replace_func=None,
        max_swipe_times=5,
        ocr_candidates="12345",
        ocr_filter_score=0.2
    )
    preset_y = presetButtonPos[1] + 144

    img_possibles = {
        "normal_task_formation-preset": (1151, preset_y),
        "normal_task_formation-set-confirm": (761, 574),
    }

    img_end = "final_restriction_rls_formation-menu"
    co_detect(self, None, None, img_end, img_possibles, skip_first_screenshot=True)

def log_clear_unit_info(self, state, _max_absent, _t):
    ret = None
    ms = int(_t * 1000)
    self.logger.info(f"Clear Unit State | {ms}ms")
    self.logger.info("Row Front    Back      State")
    for i in range(FINAL_RESTRICTION_RLS_CLEAR_UNIT_ROW_COUNT):
        st = str(i+1) + " : "
        temp = ''.join(["EXO"[x] for x in state[i]])
        temp = temp[:FINAL_RESTRICTION_RLS_FRONT_STUDENT_CNT] + " | " + temp[FINAL_RESTRICTION_RLS_BACK_STUDENT_CNT*(-1):]
        st += temp
        if np.count_nonzero(state[i] == 1) <= _max_absent and \
                np.count_nonzero(state[i] == 0) < FINAL_RESTRICTION_RLS_MAX_CHARACTER_COUNT:  # ensure not all empty
            st += "  <-- Valid"
            if ret is None:
                ret = i
        else:
            if np.count_nonzero(state[i] == 0) == FINAL_RESTRICTION_RLS_MAX_CHARACTER_COUNT:  # all empty
                st += "  <-- Empty"
                ret = -1
            else:
                st += "  <-- Invalid"
        self.logger.info(st)
    return ret

def to_page_clear_unit(self):
    img_possibles = {
        "final_restriction_rls_menu": (923, 670)
    }
    img_end = "final_restriction_rls_clear-unit-menu"
    co_detect(self, None, None, img_end, img_possibles, skip_first_screenshot=True)

def get_stage_index_boxes(self):
    ret = []
    colors = [
        FINAL_RESTRICTION_RLS_PIXEL_STAGE_NOT_SELECTED,
        FINAL_RESTRICTION_RLS_PIXEL_STAGE_SELECTED
    ]
    start_x = 574
    end_x = 1223
    y = 480
    i = start_x
    cnt = 0
    max_pixel_cnt = 100
    last_valid_type = 0
    while i <= end_x:
        temp = colors[last_valid_type]
        if rgb_in_range(self, i, y, temp[0], temp[1], temp[2], temp[3], temp[4], temp[5]):
            # match last color
            cnt += 1
            if cnt == max_pixel_cnt:
                ret.append((i-max_pixel_cnt, last_valid_type))
        else:
            temp = colors[last_valid_type ^ 1]
            if rgb_in_range(self, i, y, temp[0], temp[1], temp[2], temp[3], temp[4], temp[5]):
                # match another color
                cnt = 1
                last_valid_type ^= 1
            else:
                # do not match any color
                cnt = 0
        i += 1
    return ret

def select_accurate_stage(self, target_stage_index, stage_region_index):
    """
        Detect stage numbers and find target_stage_index
    """
    _min = (FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[stage_region_index-1] + 1)if stage_region_index >= 1 else 1
    _max = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[stage_region_index]
    assert(_min <= target_stage_index <= _max)

    self.logger.info(f"Select Accurate Stage [ {target_stage_index} ], in Range [{_min}, {_max}]")

    _retry_cnt = 7
    target_p = None
    # Search and Swipe loop
    for i in range(_retry_cnt):
        boxes = get_stage_index_boxes(self)
        if len(boxes) == 0:
            self.logger.info("Failed to detect any stage number box")
            self.update_screenshot_array()
            continue
        indexes = []
        for box in boxes:
            number = self.ocr.recognize_int(self, (box[0], 476, box[0] + 80, 504), "Final Restriction Rls Stage Index")
            if _min <= number <= _max:
                indexes.append(number)

        self.logger.info("Detected Stage Indexes : ")

        for box, index in zip(boxes, indexes):
            self.logger.info(f"Index [ {index} ], Type {box[1]}, X = {box[0]}")

        _d_min, _d_max = indexes[0], indexes[0]  # detect minimum and maximum
        for box, index in zip(boxes, indexes):
            if index == target_stage_index:
                self.logger.info(f"Find Target Index [ {index} ]")
                target_p = box[0] + 50
                break
            if index < _d_min:
                _d_min = index
            if index > _d_max:
                _d_max = index

        if target_p is not None:
            break
        self.logger.info("Didn't find target stage index")
        _s_x_st, _s_x_ed = 679, 1080  # swipe x start, x end
        _s_y = 438
        if _d_min > target_stage_index:
            pass
        elif _d_max < target_stage_index:
            _s_x_st, _s_x_ed = _s_x_ed, _s_x_st
        else:
            self.logger.info(f"Target Index [{target_stage_index}] should be in the range of [{_d_min}, {_d_max}], but not detected, retry")
            self.update_screenshot_array()
            continue

        self.swipe(_s_x_st, _s_y, _s_x_ed, _s_y, 1.0, 0.5)
        self.update_screenshot_array()

    if target_p is None:
        self.logger.info(f"Failed to find target stage index [{target_stage_index}] after {_retry_cnt} retries, quit")
        return False
    self.rgb_feature["final-restriction-rls-target-stage-not-selected"] = [[[target_p, 476]], [FINAL_RESTRICTION_RLS_PIXEL_STAGE_NOT_SELECTED]]
    self.rgb_feature["final-restriction-rls-target-stage-selected"] = [[[target_p, 476]], [FINAL_RESTRICTION_RLS_PIXEL_STAGE_SELECTED]]

    rgb_possibles = {
        "final-restriction-rls-target-stage-not-selected": (target_p, 476)
    }
    rgb_end = "final-restriction-rls-target-stage-selected"
    co_detect(self, rgb_end, rgb_possibles, skip_first_screenshot=True)
    return True

def to_page_select_stage(self, click=True):
    img_possibles = {
        "final_restriction_rls_button-return-to-select-stage": (123, 123) if click else (-1, -1),
        "final_restriction_rls_state-open": (981, 578),
        "final_restriction_rls_best-record": (640, 537)
    }

    rgb_end = "final-restriction-rls-select-stage"
    co_detect(self, rgb_end, None, None,img_possibles, skip_first_screenshot=True)

def select_stage(self, index):
    def replace_100(text):
        if text == "100":
            text.replace(" ", "")
            return "100-"
        return text

    ret = swipe_search_target_str(
        self,
        name="final_restriction_rls_button-select-stage",
        search_area=(0, 493, 1237, 600),
        possible_strs=["01-24", "25-49", "50-74", "75-99", "100-"],
        target_str_index=index,
        swipe_params=(1035, 240, 525, 240, 1.0, 0.5),
        ocr_language="en-us",
        ocr_region_offsets=(-42, -151, 141, 39),
        ocr_candidates="0123456789-",
        ocr_str_replace_func=replace_100,
        max_swipe_times=5
    )
    to_page_select_accurate_stage(self, ret[0])

def to_page_select_accurate_stage(self, x=None):
    img_end = "final_restriction_rls_button-enter-stage"
    rgb_possibles = {
        "final-restriction-rls-select-stage": (x, 527) if x is not None else (-1, -1)
    }
    img_possibles = {
        "final_restriction_rls_clear-unit-menu": (1104, 135),
        "normal_task_fail-confirm": (640, 654),
        "normal_task_fight-confirm": (1168, 659),
        "final_restriction_rls_best-record": (640, 537),
    }
    co_detect(self, None, rgb_possibles, img_end, img_possibles, skip_first_screenshot=True)


def get_next_max_stage_index(integer):
    for i in range(len(FINAL_RESTRICTION_RLS_MAX_STAGE_LIST)):
        if integer < FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[i]:
            return i
    return None

def to_page_select_stage_menu(self):
    img_possibles = {
        "main_page_bus": (1118, 589),
        "final_restriction_rls_reward-details": (1126, 109)
    }
    rgb_possibles = {
        "main_page": (1190, 552)
    }

    img_end = "final_restriction_rls_menu"

    img_possibles.update(GAME_ONE_TIME_POP_UPS[self.server])
    co_detect(self, None, rgb_possibles, img_end, img_possibles, skip_first_screenshot=True)


def get_open_state(self):
    img_ends = [
        "final_restriction_rls_state-open",
        "final_restriction_rls_state-close"
    ]

    ret = co_detect(self, None, None, img_ends, None, skip_first_screenshot=True)
    state = "Open" if ret == img_ends[0] else "Close"
    self.logger.info(f"Final Restriction Rls State [ {state} ]")
    set_final_restriction_rls_config_info(self,"open", state)
    return state

def to_page_reward_details(self):
    img_possibles = {
        "final_restriction_rls_menu": (500, 657)
    }
    img_end = "final_restriction_rls_reward-details"
    co_detect(self, None, None, img_end, img_possibles, skip_first_screenshot=True)

def get_highest_passed_stage(self):
    to_page_reward_details(self)
    region = {
        "CN": (535, 549, 725, 575),
        "Global_en-us": (559, 549, 805, 575),
        "Global_ko-kr": (535, 549, 725, 575),
        "Global_zh-tw": (538, 549, 725, 575),
        "JP": (535, 549, 725, 575),
    }[self.identifier]
    text = self.ocr.get_region_res(self, region, "en-us", "Final Restriction Rls Highest Passed Stage", "0123456789():.")
    ret = 0
    if text.find('(') != -1:
        text = text.split('(')[0].strip()
    try:
        ret = min(int(text), FINAL_RESTRICTION_RLS_MAX_STAGE)
    except:
        pass
    self.logger.info(f"Passed Highest Stage : [ {ret} ]")
    set_final_restriction_rls_config_info(self, "passed_stage", ret)
    to_page_select_stage_menu(self)
    return ret


def get_clear_unit_state(self):
    """
        Returns:
            4 * 10 array recording the 4 clear formation character available state.
            Element :
                0 : empty
                1 : character unavailable
                2 : character available
    """
    ret = get_empty_position_in_clear_formation(self)
    start_x = 179
    start_y = 212
    dx = 81.5
    dy = 107

    img_resized = resize_ss_image(self, (0, 0, 1280, 720))

    # front
    for i in range(4):
        curr_y = start_y + i * dy
        for j in range(FINAL_RESTRICTION_RLS_FRONT_STUDENT_CNT):
            if ret[i][j] == 0: # empty
                continue
            curr_x = int(start_x + j * dx)
            ret[i][j] = region_student_is_available(img_resized, curr_x, curr_y)
    # back
    start_x = 673
    for i in range(4):
        curr_y = start_y + i * dy
        for j in range(FINAL_RESTRICTION_RLS_BACK_STUDENT_CNT):
            if ret[i][j+6] == 0: # empty
                continue
            curr_x = int(start_x + j * dx)
            ret[i][j+6] = region_student_is_available(img_resized, curr_x, curr_y)

    return ret

def get_empty_position_in_clear_formation(self):
    """
        Returns:
            4 * 10 array recording if the position in clear formation is empty.
            Element :
                0 : empty
                1 : not empty
    """
    ret = np.ones((4, 10), dtype=int)
    start_x = 179
    start_y = 212

    dx = 81.5
    dy = 107

    window_dx_1 = -5
    window_dy_1 = -5
    window_dx_2 = 70
    window_dy_2 = 40

    # front
    for i in range(FINAL_RESTRICTION_RLS_CLEAR_UNIT_ROW_COUNT):
        curr_y = start_y + i * dy
        for j in range(FINAL_RESTRICTION_RLS_FRONT_STUDENT_CNT):
            curr_x = int(start_x + j * dx)
            region = (
                curr_x + window_dx_1,
                curr_y + window_dy_1,
                curr_x + window_dx_2,
                curr_y + window_dy_2
            )
            if search_in_area(
                self,
                "final_restriction_rls_clear-unit-empty-student",
                region
            ):
                ret[i][j] = 0
    # back
    start_x = 673
    for i in range(FINAL_RESTRICTION_RLS_CLEAR_UNIT_ROW_COUNT):
        curr_y = start_y + i * dy
        for j in range(FINAL_RESTRICTION_RLS_BACK_STUDENT_CNT):
            curr_x = int(start_x + j * dx)
            region = (
                curr_x + window_dx_1,
                curr_y + window_dy_1,
                curr_x + window_dx_2,
                curr_y + window_dy_2
            )
            if search_in_area(
                self,
                "final_restriction_rls_clear-unit-empty-student",
                region
            ):
                ret[i][j + 6] = 0
    return ret


def region_student_is_available(img, x, y):
    start_dx = -6
    start_dy = 51

    k1 = 0
    dx1 = 68
    k2 = -5.3
    dx2 = 12
    pixel_threshold = 140
    para = Parallelogram(x+start_dx, y+start_dy, k1, dx1, k2, dx2)
    if check_geometry_pixels(img, para, (0, pixel_threshold, 0, pixel_threshold, 0, pixel_threshold), 50):
        return 1 # unavailable
    return 2 # available
