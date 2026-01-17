import time
import numpy as np

from core.image import search_in_area, resize_ss_image, check_geometry_pixels, swipe_search_target_str
from core.geometry.parallelogram import Parallelogram
from core.picture import GAME_ONE_TIME_POP_UPS, co_detect

FINAL_RESTRICTION_RLS_FRONT_STUDENT_CNT = 6
FINAL_RESTRICTION_RLS_BACK_STUDENT_CNT = 4
FINAL_RESTRICTION_RLS_MAX_STAGE = 124
FINAL_RESTRICTION_RLS_MAX_STAGE_LIST = [24, 49, 74, 99, 124]

def implement(self):
    self.to_main_page()
    to_page_select_stage_menu(self)
    open_ = True if get_open_state(self) == "Open" else False
    if open_ :
        curr_stage = get_highest_passed_stage(self)
        if curr_stage == FINAL_RESTRICTION_RLS_MAX_STAGE:
            self.logger.info("Already Passed Highest Stage, Quit")
        else:
            push_stage(self, curr_stage)
    else:
        pass
    return True

def push_stage(self, start):
    index = get_next_max_stage_index(start)
    while index is not None:
        self.logger.info(f"Pushing Stage {FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[index]}")
        to_page_select_stage(self)
        select_stage(self, index)
        select_accurate_stage(self, FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[index], index)

        battle_result = fight()

        if battle_result == True:
            index = get_next_max_stage_index(start)
            if index is None:
                self.logger.info("Passed Highest Stage, Quit")
                return
        else:
            break

    l = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[index-1] if index >= 1 else 0
    r = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[index]

def select_accurate_stage(self, target_stage_index, stage_region_index):
    _min = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[stage_region_index-1] if stage_region_index >= 1 else 1
    _max = FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[stage_region_index]
    assert(_min <= target_stage_index <= _max)

    self.logger.info(f"Select Accurate Stage [ f{target_stage_index} ], in Range [f{_min}, f{_max} ]")

    stage_index_display_region = (574, 476, 1194, 504)
    _retry_cnt = 5
    for i in range(_retry_cnt):
        ret = self.ocr.get_region_raw_res(
            self.latest_img_array,
            stage_index_display_region,
            "en-us",
            self.ratio,
            candidates="0123456789"
        )
        # sort by X coordinate
        ret = [((sum(p[0] for p in item["position"]) / len(item["position"]), sum(p[1] for p in item["position"]) / len(item["position"])), item["text"]) for item in ret]
        ret = sorted(ret, key=lambda x: x[0])
        self.logger.info("Detected Stage Indexes : ")
        for item in ret:
            self.logger.info(f"{item[1]} at {item[0][0]}")

        for item in ret:



def to_page_select_stage(self):
    img_possibles = {
        "final_restriction_rls_button-return-to-select-stage": (123, 123),
        "final_restriction_rls_state-open": (981, 578)
    }

    rgb_end = "final-restriction-rls-select-stage"
    co_detect(self, rgb_end, None, None,img_possibles, skip_first_screenshot=True)

def select_stage(self, index):
    def replace_100(text):
        if text == "100":
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
        ocr_str_replace_func=replace_100,
        max_swipe_times=5
    )

    img_end = "final_restriction_rls_button-enter-stage"
    rgb_possibles = {
        "final-restriction-rls-select-stage": (ret[0], 527)
    }
    co_detect(self, None, rgb_possibles, img_end, skip_first_screenshot=True)


def get_next_max_stage_index(integer):
    for i in range(len(FINAL_RESTRICTION_RLS_MAX_STAGE_LIST)):
        if integer < FINAL_RESTRICTION_RLS_MAX_STAGE_LIST[i]:
            return i
    return None

def to_page_select_stage_menu(self):
    img_possibles = {
        "main_page_bus": (1118, 589)
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
    self.logger.info(f"Final Restriction Rls State {state}")
    return state

def get_highest_passed_stage(self):
    region = {
        "CN": (),
        "JP": (880, 433, 1197, 463)
    }
    region = region[self.identifier]
    text = self.ocr.get_region_res(self, region,"en-us", "Final Restriction Rls Highest Passed Stage")
    ret = 0
    if text.find('(') != -1:
        text = text.split('(')[0].strip()
    try:
        ret = int(text)
    except:
        pass
    return ret


def get_clear_formation_state(self):
    """
        Returns:
            4 * 10 array recording the 4 clear formation character available state.
            Element :
                0 : empty
                1 : character unavailable
                2 : character available
    """
    t1 = time.time()
    ret = get_empty_position_in_clear_formation(self)
    t2 = time.time()
    print("get empty position time:", t2 - t1)
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
            t1 = time.time()
            ret[i][j] = region_student_is_available(img_resized, curr_x, curr_y)
            t2 = time.time()
            print("region_student_is_available:", t2 - t1)
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
    for i in range(4):
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
    for i in range(4):
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
