from core import color, picture
from core.geometry.parallelogram import Parallelogram
from core.utils import build_possible_string_dict_and_length, most_similar_string, purchase_ticket_times_to_int


def implement(self):
    self.update_screenshot_array()
    # for i in range(0, 9):
    #     print(check_region_availability(self, i))
    # cv2.imshow("test", self.latest_img_array)
    # cv2.waitKey(0)
    #
    # exit(0)
    self.to_main_page()
    self.lesson_times = self.config.lesson_times
    region_name = self.static_config.lesson_region_name[self.identifier].copy()
    for i in range(0, len(region_name)):
        region_name[i] = pre_process_lesson_name(self, region_name[i])

    self.lesson_letter_dict, self.lesson_region_name_len = build_possible_string_dict_and_length(region_name)
    purchase_ticket_times = purchase_ticket_times_to_int(self.config.purchase_lesson_ticket_times, 4)
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
    if self.config.lesson_enableInviteFavorStudent:
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
        self.logger.info("Begin schedule in [" + region_name[k] + "]")
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
        'CN': [(357, 295), (700, 295), (1043, 295),
               (357, 445), (701, 445), (1043, 445),
               (357, 598), (701, 598), (1043, 598)],
        'Global': [(357, 295), (700, 295), (1043, 295),
               (357, 445), (701, 445), (1043, 445),
               (357, 598), (701, 598), (1043, 598)],
        'JP': [(357, 295), (700, 295), (1043, 295),
               (357, 445), (701, 445), (1043, 445),
               (357, 598), (701, 598), (1043, 598)]
    }
    dx = {
        'CN': 72,
        'Global': 72,
        'JP': 72
    }
    rgb_range = {
        'CN': [223, 255, 164, 224, 190, 230],
        'Global': [223, 255, 164, 224, 190, 230],
        'JP': [223, 255, 164, 224, 190, 230]
    }
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
    y_list = [238, 391, 543]

    pd_lo = [[289,  y_list[0]], [643,  y_list[0]], [985,  y_list[0]],
             [289,  y_list[1]], [643,  y_list[1]], [985,  y_list[1]],
             [289,  y_list[2]], [643,  y_list[2]], [985,  y_list[2]]]
    res = []
    for i in range(0, 9):
        if color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 250, 255, 250, 255, 250, 255):
            res.append(check_region_availability(self, i))
        elif color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 31, 160, 31, 160, 31, 160):
            res.append("lock")
        elif color.rgb_in_range(self, pd_lo[i][0], pd_lo[i][1], 197, 217, 197, 217, 195,215):
            res.append("no activity")
        else:
            res.append("unknown")
    return res

def check_region_availability(self, region_cnt):
    k1 = 0
    dx1 = 33
    k2 = -5.3
    dx2 = [9, 4]
    y_list = [308, 459, 612]
    region_start_p = [
        (154, y_list[0]), (498, y_list[0]), (842, y_list[0]),
        (154, y_list[1]), (498, y_list[1]), (842, y_list[1]),
        (156, y_list[2]), (500, y_list[2]), (844, y_list[2])
    ]
    dx2 = dx2[int(region_cnt / 6)]
    start_p = region_start_p[region_cnt]
    y_min, x_min_list, y_min_list = Parallelogram(start_p[0], start_p[1], k1, dx1, k2, dx2).pixels()

    unavailable_max_pixel = 140
    cnt = 0
    for i in range(0, len(x_min_list)):
        for j in range(x_min_list[i], y_min_list[i] + 1):
            if not color.rgb_in_range(self, j, y_min + i, 0, unavailable_max_pixel, 0, unavailable_max_pixel, 0, unavailable_max_pixel):
                # self.latest_img_array[y_min + i, j] = [255, 0, 0]  # mark unavailable area
                cnt += 1
                if cnt >= 50:
                    return "available"
    return "done"



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
    """Use one fixed-layout screenshot per region to prioritize configured students."""
    from pathlib import Path

    from core.student_recognition import StudentRecognitionService

    self.logger.info("Lesson Inviting favor student.")
    service = StudentRecognitionService(
        self.static_config.student_names,
        Path(self.project_dir),
    )
    favor_student_list, unknown = service.catalog.validate_names(
        self.config.lesson_favorStudent
    )
    if unknown:
        self.logger.warning("Unknown student name(s): " + ", ".join(unknown))
    if not favor_student_list:
        self.logger.info("FavorStudent list is empty.")
        return
    if not service.available:
        self.logger.warning(
            "Student recognition is unavailable; use normal lesson selection. "
            + (service.load_error or "")
        )
        return

    to_select_location(self, True)
    start_num = get_lesson_region_num(self)
    if not isinstance(start_num, int) or not 0 <= start_num < len(self.lesson_region_name_len):
        self.logger.warning("Cannot resolve lesson region; use normal lesson selection.")
        return

    detected_positions = {}
    region_card_names = [[[] for _ in range(9)] for _ in range(len(self.lesson_region_name_len))]
    primary = favor_student_list[0]
    cur_num = start_num
    visited_regions = set()
    self.logger.info("Target Student : [ " + primary + " ]")

    while cur_num not in visited_regions and self.flag_run:
        visited_regions.add(cur_num)
        to_all_locations(self, True)
        statuses = get_lesson_each_region_status(self)
        self.update_screenshot_array()
        cards = service.recognize_lesson(self.latest_img_array, statuses, self.server)
        selected_card = service.select_priority_card(cards, [primary])

        for card in cards:
            names = []
            diagnostic = []
            for avatar in card.avatars:
                prediction = avatar.prediction
                if prediction is None or not prediction.accepted or not prediction.name:
                    continue
                diagnostic.append(prediction.name + ("" if avatar.eligible else " [gray]"))
                if avatar.eligible:
                    names.append(prediction.name)
            if diagnostic:
                self.logger.info("Block " + str(card.index + 1) + " : " + ", ".join(diagnostic))
            if card is selected_card:
                continue
            region_card_names[cur_num][card.index] = names
            for name in names:
                detected_positions.setdefault(name, set()).add((cur_num, card.index))

        if selected_card is not None:
            self.logger.info("Find [ " + primary + " ] in Block " + str(selected_card.index + 1))
            result = execute_lesson(self, selected_card.index)
            if result == "inadequate_ticket":
                self.logger.warning("INADEQUATE LESSON TICKET")
                return
            if result == "lesson_report":
                self.logger.info("Complete one lesson.")
                self.lesson_tickets -= 1
                if self.lesson_tickets == 0:
                    self.logger.info("No Tickets.")
                    return True

        to_select_location(self, True)
        next_num = switch_lesson_region_page(self, to_left_page=False, cur_num=cur_num)
        if not isinstance(next_num, int) or not 0 <= next_num < len(self.lesson_region_name_len):
            self.logger.warning("Cannot resolve next lesson region; stop student scan.")
            break
        cur_num = next_num
        if cur_num == start_num:
            break

    for student in favor_student_list[1:]:
        self.logger.info("Target Student : " + student)
        positions = detected_positions.get(student, set())
        while positions and self.flag_run:
            region, lesson_id = positions.pop()
            to_lesson_region(self, region, start_num)
            to_all_locations(self, True)
            statuses = get_lesson_each_region_status(self)
            self.update_screenshot_array()
            cards = service.recognize_lesson(self.latest_img_array, statuses, self.server)
            confirmed = service.select_priority_card(
                [card for card in cards if card.index == lesson_id], [student]
            )
            if confirmed is None:
                self.logger.warning("Cached student position is no longer actionable; skip.")
                continue
            result = execute_lesson(self, lesson_id)
            if result == "inadequate_ticket":
                self.logger.warning("INADEQUATE LESSON TICKET")
                return
            if result == "lesson_report":
                self.logger.info("Complete one lesson.")
                self.lesson_tickets -= 1
                names = region_card_names[region][lesson_id]
                for name in names:
                    detected_positions.get(name, set()).discard((region, lesson_id))
                if self.lesson_tickets == 0:
                    self.logger.info("No Tickets.")
                    return True
