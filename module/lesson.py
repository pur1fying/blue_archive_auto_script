import importlib
import time

import cv2

from core import color, picture, image
from core.utils import build_possible_string_dict_and_length, most_similar_string


def implement(self):
    self.to_main_page()
    self.lesson_times = self.config.lesson_times
    region_name = self.static_config.lesson_region_name[self.identifier].copy()
    for i in range(0, len(region_name)):
        region_name[i] = pre_process_lesson_name(self, region_name[i])

    self.lesson_letter_dict, self.lesson_region_name_len = build_possible_string_dict_and_length(region_name)

    purchase_ticket_times = min(self.config.purchase_lesson_ticket_times, 4)
    to_lesson_location_select(self, True)
    if purchase_ticket_times > 0:
        self.logger.info("Purchase lesson ticket times :" + str(purchase_ticket_times))
        purchase_lesson_ticket(self, purchase_ticket_times)
    res = get_lesson_tickets(self)
    self.lesson_tickets = res
    if self.lesson_tickets == 0:
        self.logger.warning("No Lesson Tickets")
        return True
    to_lesson_location_select(self, True)
    self.swipe(940, 213, 940, 560, duration=0.1, post_sleep_time=0.5)
    if self.config_set.get("lesson_enableInviteFavorStudent"):
        invite_favor_student(self)
        if self.lesson_tickets == 0:
            return True
    to_select_location(self, True)
    cur_num = get_lesson_region_num(self)
    for k in range(0, len(self.lesson_times)):
        if self.lesson_times[k] == 0:
            continue
        tar_num = k
        times = self.lesson_times[k]
        self.logger.info("begin schedule in [" + region_name[k] + "]")
        cur_num = to_lesson_region(self, tar_num, cur_num)
        for j in range(0, times):
            to_all_locations(self, True)
            res = [get_lesson_each_region_status(self), get_lesson_relationship_counts(self)]
            out_lesson_status(self, res)
            choice = choose_lesson(self, res, cur_num)
            if choice == -1:
                break
            res = execute_lesson(self, choice)
            if res == "inadequate_ticket":
                self.logger.warning("INADEQUATE LESSON TICKET.")
                return True
            if res == "lesson_report":
                self.logger.info("Complete one lesson.")
                self.lesson_tickets -= 1
                if self.lesson_tickets == 0:
                    self.logger.info("No Tickets.")
                    return True
    return True


def pre_process_lesson_name(self, name):
    temp = ""
    name = name.lower()
    if self.server == "Global":
        if name.startswith("rank"):
            name = name[4:]
        for i in range(0, len(name)):
            if name[i] == ' ' or name[i].isdigit():
                continue
            temp += name[i]
    elif self.server == "JP":
        for i in range(0, len(name)):
            if name[i] == ' ' or name[i].isdigit():
                continue
            temp += name[i]
    elif self.server == "CN":
        if name.startswith("评级"):
            name = name[2:]
        temp = ""
        for i in range(0, len(name)):
            if name[i] == ' ' or name[i].isdigit():
                continue
            temp += name[i]
    return temp


def to_lesson_region(self, tar_num, cur_num=0):
    region_name = self.static_config.lesson_region_name[self.identifier]
    to_select_location(self, True)
    while cur_num != tar_num and self.flag_run:
        self.logger.info("now in page [ " + region_name[cur_num] + " ]")
        if cur_num > tar_num:
            res = switch_lesson_region_page(self, to_left_page=True, cur_num=cur_num)
        else:
            res = switch_lesson_region_page(self, to_left_page=False, cur_num=cur_num)
        get_lesson_region_num(self)
        if res != 'NOT FOUND':
            cur_num = res
        else:
            self.logger.warning("fail to find region name, use last region name")
            cur_num = tar_num
    self.logger.info("Reach lesson page [ " + region_name[cur_num] + " ]")
    return cur_num


def switch_lesson_region_page(self, to_left_page=False, cur_num=0):
    """
        Switch one lesson region page.
        Returns:
            final page num
    """
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    x = right_change_page_x
    if to_left_page:
        x = left_change_page_x
    while True:
        self.click(x, change_page_y, duration=0.5, wait_over=True)
        to_select_location(self)
        res = get_lesson_region_num(self)
        if res != cur_num:  # if res == 'NOT FOUND', keep switching
            return res


def get_lesson_region_num(self):
    region = {
        'CN': (925, 94, 1240, 128),
        'Global_en-us': (932, 94, 1240, 129),
        'Global_zh-tw': (932, 94, 1240, 129),
        'Global_ko-kr': (1005, 94, 1240, 129),
        'JP': (932, 94, 1240, 129)
    }
    check_fail_times = 0
    while self.flag_run:
        name = self.ocr.get_region_res(
            baas=self,
            region=region[self.identifier],
            language=self.ocr_language,
            log_info="Region Name"
        )
        name = pre_process_lesson_name(self, name)
        max_acc, idx = most_similar_string(name, self.lesson_letter_dict, self.lesson_region_name_len)
        if max_acc <= 0.4:
            self.logger.info("NOT FOUND")
            check_fail_times += 1
            if check_fail_times >= 4:
                self.logger.warning("Fail To Detect Lesson Region Name After 4 Times.")
                return 'NOT FOUND'
            else:
                self.update_screenshot_array()
        else:
            self.logger.info(f"Lesson Region Num : {idx} | Acc : {round(max_acc, 3)}")
            return idx


def get_lesson_tickets(self):
    to_purchase_lesson_ticket(self)
    try:
        region = [574, 332, 631, 361]
        ocr_res = self.ocr.get_region_res(self, region, 'en-us', "lesson ticket count", "0123456789")
        return int(ocr_res)
    except Exception:
        self.logger.warning("UNKNOWN tickets")
        return 999


def to_purchase_lesson_ticket(self):
    img_ends = 'lesson_purchase-lesson-ticket-menu'
    img_possibles = {
        'lesson_location-select': (148, 101)
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def purchase_lesson_ticket(self, times):
    to_purchase_lesson_ticket(self)
    if times == 4:  # max
        self.click(879, 346, wait_over=False)
    else:
        self.click(807, 346, count=times - 1, wait_over=False)
    rgb_possibles = {'reward_acquired': (640, 116)}
    img_ends = 'lesson_location-select'
    img_possibles = {
        'lesson_purchase-lesson-ticket-menu': (766, 507),
        'lesson_purchase-lesson-ticket-notice': (766, 507),
    }
    picture.co_detect(self, img_ends, img_possibles, rgb_possibles)


def to_lesson_location_select(self, skip_first_screenshot=False):
    rgb_possibles = {
        "main_page": (210, 655),
        "reward_acquired": (640, 116)
    }
    img_ends = 'lesson_location-select'
    img_possibles = {
        'main_page_home-feature': (210, 655),
        'lesson_purchase-lesson-ticket-notice': (920, 165),
        'lesson_purchase-lesson-ticket-menu': (920, 165),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_select_location(self, skip_first_screenshot=False):
    rgb_possibles = {
        "main_page": (210, 655),
        "area_rank_up": (640, 116),
        "relationship_rank_up": (640, 153)
    }
    img_ends = 'lesson_select-location'
    img_possibles = {
        'lesson_purchase-lesson-ticket-menu': (920, 165),
        'main_page_home-feature': (211, 664),
        'lesson_location-select': (937, 186),
        'lesson_lesson-information': (964, 117),
        'lesson_all-locations': (1138, 117),
        'lesson_lesson-report': (642, 556),
        'main_page_relationship-rank-up': (640, 360),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def execute_lesson(self, lesson_id):
    self.logger.info("Execute Lesson " + str(lesson_id + 1))
    to_location_info(self, lesson_id)
    return start_lesson(self)


def to_location_info(self, lesson_id):
    click_lo = [[307, 257], [652, 257], [995, 257],
                [307, 408], [652, 408], [995, 408],
                [307, 560], [652, 560], [985, 560]]
    img_possibles = {"lesson_all-locations": click_lo[lesson_id]}
    img_ends = 'lesson_lesson-information'
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def start_lesson(self):
    img_possibles = {
        'lesson_lesson-information': (640, 556),
        'main_page_relationship-rank-up': (640, 360),
    }
    img_ends = [
        'lesson_lesson-report',
        'lesson_purchase-lesson-ticket-menu',
    ]
    rgb_possibles = {
        'reward_acquired': (637, 116),
        'relationship_rank_up': (640, 360),
        'area_rank_up': (637, 116),
    }
    res = picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)
    if res == 'lesson_purchase-lesson-ticket-menu':
        return 'inadequate_ticket'
    return 'lesson_report'


def to_all_locations(self, skip_first_screenshot=False):
    img_ends = 'lesson_all-locations'
    img_possibles = {
        'lesson_select-location': (1160, 664),
        'lesson_lesson-information': (964, 117),
        'lesson_location-select': (937, 186),
        'lesson_lesson-report': (1036, 124),
        'main_page_relationship-rank-up': (640, 360),
    }
    rgb_possibles = {
        'relationship_rank_up': (640, 360),
        'reward_acquired': (637, 116),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def is_upper_english(char):
    if 'A' <= char <= 'Z':
        return True
    return False


def is_lower_english(char):
    if 'a' <= char <= 'z':
        return True
    return False


def is_english(char):
    return is_upper_english(char) or is_lower_english(char)


def is_chinese_char(char):
    return 0x4e00 <= ord(char) <= 0x9fff


def get_lesson_relationship_counts(self):
    position = {
        'CN': [(443, 290), (787, 290), (1132, 290),
               (443, 441), (787, 441), (1132, 441),
               (443, 591), (787, 591), (1132, 591)],
        'Global': [(443, 290), (787, 290), (1132, 290),
                   (443, 441), (787, 441), (1132, 441),
                   (443, 591), (787, 591), (1132, 591)],
        'JP': [(354, 271), (701, 271), (1043, 271),
               (354, 422), (701, 422), (1043, 422),
               (354, 574), (701, 574), (1043, 574)]
    }
    dx = {
        'CN': 51,
        'Global': 51,
        'JP': 72
    }
    rgb_range = {
        'CN': [245, 255, 108, 128, 134, 154],
        'Global': [245, 255, 108, 128, 134, 154],
        'JP': [223, 255, 164, 224, 190, 230]
    }
    if self.server == "JP":
        self.swipe(983, 588, 983, 466, duration=0.1, post_sleep_time=1.0)
        self.update_screenshot_array()
    rgb_range = rgb_range[self.server]
    position = position[self.server]
    dx = dx[self.server]
    res = []
    for i in range(0, 9):
        cnt = 0
        for j in range(0, 3):
            if color.rgb_in_range(
                    self,
                    position[i][0] - dx * j,
                    position[i][1],
                    rgb_range[0],
                    rgb_range[1],
                    rgb_range[2],
                    rgb_range[3],
                    rgb_range[4],
                    rgb_range[5],
            ):
                cnt += 1
            # cv2.circle(self.latest_img_array, (position[i][0] - dx * j, position[i][1]), radius=2, color=1, thickness=1)

        res.append(cnt)
    # cv2.imshow("test", self.latest_img_array)
    # cv2.waitKey(0)
    return res


def get_lesson_each_region_status(self):
    pd_lo = [[289, 204], [643, 204], [985, 204],
             [289, 359], [643, 359], [985, 359],
             [289, 511], [643, 511], [985, 511]]
    res = []
    for i in range(0, 9):
        if color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 250, 255, 250, 255, 250, 255):
            res.append("available")
        elif color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 230, 249, 230, 249, 230, 249):
            res.append("done")
        elif color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 31, 160, 31, 160, 31, 160):
            res.append("lock")
        elif color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 197, 217, 197, 217, 195,
                                215):
            res.append("no activity")
        else:
            res.append("unknown")
    return res


def out_lesson_status(self, res):
    self.logger.info("Lesson status :")
    message = ""
    for i in range(0, 9):
        message += "\t" + res[0][i]
        if res[0][i] == "available":
            message += " :" + str(res[1][i])
        if i % 3 == 2:
            self.logger.info(message)
            message = ""


def choose_lesson(self, res, region):
    """
        Choose a lesson according to detected lesson status and config
        res (List(str), List(int)):
            Contains two list :
                1.lesson availability list
                2.relationship count list
    """
    if self.config.lesson_relationship_first:  # choose bigger relationship count
        max_relationship = -1
        lo = -1
        for i in range(0, 9):
            if res[0][i] == "available":
                if res[1][i] >= max_relationship:
                    max_relationship = res[1][i]
                    lo = i
        return lo
    else:
        tier = ["superior", "advanced", "normal", "primary"]
        pri = self.config.lesson_each_region_object_priority[region]
        if pri == []:
            for i in range(8, -1, -1):  # choose the last available which gives higher tier reward
                if res[0][i] == "available":
                    return i
            return -1
        else:
            choice = -1
            max_relationship = -1
            for i in range(0, len(tier)):
                if tier[i] in pri:
                    for j in range(2 * (3 - i), 2 * (4 - i)):  # i = 0 -- > [6, 7]
                        if res[0][j] == "available" and res[1][j] > max_relationship:
                            if max_relationship != -1:
                                self.logger.info("Due to relationship priority, current choice forward from [ " + str(
                                    choice + 1) + " ] to [ " + str(j + 1) + " ]")
                            max_relationship = res[1][j]
                            choice = j
                    if choice != -1:
                        return choice
            return choice


def invite_favor_student(self):
    """
        search all lessons and invite specified student
        use each server image template, if image not exists use shared
    """
    self.logger.info("Lesson Inviting favor student.")
    favorStudentList = self.config.lesson_favorStudent.copy()

    detected_student_pos = dict()  # student name : {(region, block)}
    region_block_names = [[[] for _ in range(9)] for _ in range(len(self.lesson_region_name_len))]
    template_image_names = get_favor_student_image_template_names(self.identifier)
    template_not_exist = [x for x in favorStudentList if x not in template_image_names]
    if len(template_not_exist) > 0:
        self.logger.warning("Didn't find template image for [ " + ", ".join(template_not_exist) + " ]")
        self.logger.warning("Possible reasons : ")
        self.logger.warning("                   1. Template image not exists, please contact developer to add it.")
        self.logger.warning("                   2. You wrote wrong student name.")
    favorStudentList = [x for x in favorStudentList if x not in template_not_exist]
    if len(favorStudentList) == 0:
        self.logger.info("FavorStudent list is empty.")
        return
    to_select_location(self, True)
    start_num = get_lesson_region_num(self)
    cur_num = start_num
    tar_stu = favorStudentList[0]
    self.logger.info("Target Student : [ " + tar_stu + " ]")
    # the first student will search a round, all detected data during this round are stored in detected_student_pos
    while True:
        to_all_locations(self, True)
        res = [get_lesson_each_region_status(self), get_lesson_relationship_counts(self)]  # [status, relationship]
        out_lesson_status(self, res)
        self.swipe(983, 588, 983, 466, duration=0.1, post_sleep_time=0.5)
        self.update_screenshot_array()
        self.logger.info("Get Page Favor Student Names.")
        t1 = time.time()
        lesson_need_to_execute = None
        for j in range(0, 9):
            block_existing_names = []
            if res[0][j] == "available":
                detect_region = get_favor_student_detect_region(self, j)
                block_detect_student = []
                for key in template_image_names:
                    if key in block_existing_names:
                        continue
                    ret = image.search_in_area(self, "lesson_" + key, detect_region, threshold=0.75)
                    if not ret:
                        continue
                    block_detect_student.append((ret[0], key))
                    block_existing_names.append(key)

                    if len(block_detect_student) == res[1][j]:  # reach max affection stu count
                        break
                if len(block_detect_student) == 0:
                    continue
                block_detect_student.sort()
                block_names = [x[1] for x in block_detect_student]
                self.logger.info("Block " + str(j + 1) + " : " + ", ".join(block_names))
                if tar_stu in block_names:
                    self.logger.info("Find [ " + tar_stu + " ] in Block.")
                    lesson_need_to_execute = j
                else:
                    for name in block_names:
                        detected_student_pos.setdefault(name, set())
                        detected_student_pos[name].add((cur_num, j))
                    region_block_names[cur_num][j] = block_names
        t2 = time.time()
        self.logger.info("Detecting time : " + str(int((t2 - t1) * 1000)) + "ms.")
        if lesson_need_to_execute is not None:  # target student found
            t = execute_lesson(self, lesson_need_to_execute)
            if t == "inadequate_ticket":
                self.logger.warning("INADEQUATE LESSON TICKET")
                return
            if t == "lesson_report":
                self.logger.info("Complete one lesson.")
                self.lesson_tickets -= 1
                if self.lesson_tickets == 0:
                    self.logger.info("No Tickets.")
                    return True
        to_select_location(self, True)
        cur_num = switch_lesson_region_page(self, to_left_page=False, cur_num=cur_num)
        if cur_num == start_num:  # checked a round
            break
    for student in favorStudentList[1:]:
        self.logger.info("Target Student : " + student)
        if student not in detected_student_pos:
            self.logger.warning("Didn't find [ " + student + " ] in any lesson regions.Skip")
            continue
        self.logger.info("Recorded Position(s) : " + str(detected_student_pos[student]))
        while True:
            _set = detected_student_pos[student]
            if len(_set) == 0:
                break
            region, lesson_id = next(iter(_set))
            to_lesson_region(self, region, start_num)
            to_all_locations(self, True)
            t = execute_lesson(self, lesson_id)
            if t == "inadequate_ticket":
                self.logger.warning("INADEQUATE LESSON TICKET")
                return
            if t == "lesson_report":
                self.logger.info("Complete one lesson.")
                self.lesson_tickets -= 1
                if self.lesson_tickets == 0:
                    self.logger.info("No Tickets.")
                    return True
                else:
                    names = region_block_names[region][lesson_id]
                    self.logger.info("Pop [" + str(region) + ", " + str(lesson_id) + "] : " + ", ".join(names))
                    for name in region_block_names[region][lesson_id]:
                        detected_student_pos[name].remove((region, lesson_id))


def get_favor_student_detect_region(self, lesson_cnt):
    if self.server in ['CN', 'Global']:
        x_start = 285
        y_start = 240
        dx1 = 344
        dy1 = 152
        dx2 = 161
        dy2 = 52
    else:
        x_start = 145
        y_start = 232
        dx1 = 344
        dy1 = 152
        dx2 = 225
        dy2 = 68

    x1 = x_start + dx1 * (lesson_cnt % 3)
    y1 = y_start + dy1 * (lesson_cnt // 3)
    return x1, y1, x1 + dx2, y1 + dy2


def get_favor_student_image_template_names(identifier):
    server_image_module_path = 'src.images.' + identifier + '.x_y_range.lesson_affection'
    data = importlib.import_module(server_image_module_path)
    x_y_range = getattr(data, 'x_y_range', None)
    return list(x_y_range.keys())
