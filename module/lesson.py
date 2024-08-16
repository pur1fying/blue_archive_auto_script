import time
from core import color, picture


def implement(self):
    self.quick_method_to_main_page()
    self.lesson_times = self.config["lesson_times"]
    region_name = self.static_config["lesson_region_name"][self.server]
    letter_dict = []
    region_name_len = []
    for i in range(0, len(region_name)):
        letter_dict.append({})
        temp = pre_process_lesson_name(self, region_name[i])
        region_name_len.append(len(temp))
        for j in range(0, len(temp)):
            letter_dict[i].setdefault(temp[j], 0)
            letter_dict[i][temp[j]] += 1

    click_lo = [[307, 257], [652, 257], [995, 257],
                [307, 408], [652, 408], [995, 408],
                [307, 560], [652, 560], [985, 560]]
    purchase_ticket_times = min(self.config['purchase_lesson_ticket_times'], 4)  # ** 购买日程券的次数
    to_lesson_location_select(self, True)
    if purchase_ticket_times > 0:
        self.logger.info("Purchase lesson ticket times :" + str(purchase_ticket_times))
        purchase_lesson_ticket(self, purchase_ticket_times)
    res = get_lesson_tickets(self)
    if res == "UNKNOWN":
        self.logger.info("UNKNOWN tickets")
        lesson_tickets = 999
    else:
        lesson_tickets = res[0]
        self.logger.info("tickets: " + str(lesson_tickets))
        if lesson_tickets == 0:
            self.logger.info("no tickets")
            return True
    self.swipe(940, 213, 940, 560, duration=0.1, post_sleep_time=0.5)
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    cur_num = 0
    for k in range(0, len(self.lesson_times)):
        if self.lesson_times[k] == 0:
            continue
        tar_num = k
        times = self.lesson_times[k]
        self.logger.info("begin schedule in [" + region_name[k] + "]")
        to_select_location(self, True)
        self.logger.info("now in page " + region_name[cur_num])
        while cur_num != tar_num and self.flag_run:
            if cur_num > tar_num:
                if (cur_num - tar_num) * 2 < len(region_name):
                    self.click(left_change_page_x, change_page_y, count=cur_num - tar_num,
                               duration=1.5, wait_over=True)
                else:
                    self.click(right_change_page_x, change_page_y, count=len(region_name) - cur_num + tar_num,
                               duration=1.5, wait_over=True)
            else:
                if (tar_num - cur_num) * 2 < len(region_name):
                    self.click(right_change_page_x, change_page_y, count=tar_num - cur_num, duration=1.5,
                               wait_over=True)
                else:
                    self.click(left_change_page_x, change_page_y, count=len(region_name) - tar_num + cur_num,
                               duration=1.5, wait_over=True)
            to_select_location(self)
            res = get_lesson_region_num(self, letter_dict, region_name_len)
            if res != 'NOT FOUND':
                cur_num = res
            else:
                self.logger.warning("fail to find region name, use last region name")
                cur_num = tar_num
            self.logger.info("now in page " + region_name[cur_num])
        for j in range(0, times):
            to_all_locations(self, True)
            res = [get_lesson_each_region_status(self), get_lesson_relationship_counts(self)]
            out_lesson_status(self, res)
            choice = choose_lesson(self, res, cur_num)
            if choice == -1:
                break
            self.logger.info("CHOOSE lesson " + str(choice + 1))
            to_location_info(self, click_lo[choice][0], click_lo[choice][1])
            res = start_lesson(self)
            if res == "inadequate_ticket":
                self.logger.info("INADEQUATE LESSON TICKET")
                return True
            if res == "lesson_report":
                self.logger.info("complete one lesson")
                lesson_tickets -= 1
                if lesson_tickets == 0:
                    self.logger.info("no tickets")
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
            if name[i] == ' ' or is_english(name[i]) or name[i].isdigit():
                continue
            temp += name[i]
    elif self.server == "CN":
        if name.startswith("评级"):
            name = name[2:]
        temp = ""
        for i in range(0, len(name)):
            if name[i] == ' ' or is_english(name[i]) or name[i].isdigit():
                continue
            temp += name[i]
    return temp


def get_lesson_region_num(self, letter_dict=None, region_name_len=None):
    region = {
        'CN': (925, 94, 1240, 128),
        'Global': (932, 94, 1240, 129),
        'JP': (932, 94, 1240, 129),
    }
    check_fail_times = 0
    while self.flag_run:
        name = self.ocr.get_region_res(self.latest_img_array, region[self.server], self.server, self.ratio)
        name = pre_process_lesson_name(self, name)
        acc = []
        detected_name_dict = {}
        for i in range(0, len(name)):
            detected_name_dict.setdefault(name[i], 0)
            detected_name_dict[name[i]] += 1
        detected_name_dict_keys = detected_name_dict.keys()
        for i in range(0, len(letter_dict)):
            cnt = 0
            t = letter_dict[i].keys()
            for j in t:
                if j not in detected_name_dict_keys:
                    continue
                cnt = cnt + letter_dict[i][j] - abs(letter_dict[i][j] - detected_name_dict[j])
            acc.append(cnt / region_name_len[i])
        max_acc = max(acc)
        if max_acc < 0.5:
            self.logger.info("NOT FOUND")
            check_fail_times += 1
            if check_fail_times >= 4:
                return 'NOT FOUND'
            else:
                self.latest_img_array = self.get_screenshot_array()
        else:
            return acc.index(max_acc)


def get_lesson_tickets(self):
    try:
        region = {
            "CN": (280, 85, 340, 114),
            "Global": (220, 88, 282, 112),
            "JP": (188, 88, 252, 112),
        }
        ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global', self.ratio)
        if ocr_res[0] == 'Z':
            return [7, 7]
        if ocr_res[1] == '1':
            return [int(ocr_res[0]), int(ocr_res[2])]
        for j in range(0, len(ocr_res)):
            if ocr_res[j] == '/':
                return [int(ocr_res[:j]), int(ocr_res[j + 1:])]
        return "UNKNOWN"
    except Exception as e:
        print(e)
        return "UNKNOWN"


def purchase_lesson_ticket(self, times):
    self.click(148, 101, rate=1.5)
    if times == 4:  # max
        self.click(879, 346, wait=False)
    else:
        self.click(807, 346, count=times - 1, wait=False)
    rgb_possibles = {'reward_acquired': (640, 116)}
    img_ends = 'lesson_location-select'
    img_possibles = {
        'lesson_purchase-lesson-ticket': (766, 507),
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
        'lesson_purchase-lesson-ticket': (920, 165),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_select_location(self, skip_first_screenshot=False):
    rgb_possibles = {
        "main_page": (210, 655),
        "area_rank_up": (640, 116),
        "relationship_rank_up": (640, 153)
    }
    img_ends = 'lesson_select-location'
    img_possibles = {
        'main_page_home-feature': (211, 664),
        'lesson_location-select': (937, 186),
        'lesson_lesson-information': (964, 117),
        'lesson_all-locations': (1138, 117),
        'lesson_lesson-report': (642, 556),
        'main_page_relationship-rank-up': (640, 360),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def to_location_info(self, x, y):
    img_possibles = {"lesson_all-locations": (x, y)}
    img_ends = 'lesson_lesson-information'
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def start_lesson(self):
    img_possibles = {
        'lesson_lesson-information': (640, 556),
        'main_page_relationship-rank-up': (640, 360),
    }
    img_ends = [
        'lesson_lesson-report',
        'lesson_inadequate-lesson-ticket',
        'lesson_purchase-lesson-ticket',
    ]
    rgb_possibles = {
        'reward_acquired': (637, 116),
        'relationship_rank_up': (640, 360),
        'area_rank_up': (637, 116),
    }
    res = picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)
    if res == 'lesson_inadequate-lesson-ticket' or res == 'lesson_purchase-lesson-ticket':
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
    position = [(443, 290), (787, 290), (1132, 290),
                (443, 441), (787, 441), (1132, 441),
                (443, 591), (787, 591), (1132, 591)]
    dx = 51
    res = []
    for i in range(0, 9):
        cnt = 0
        for j in range(0, 3):
            if color.judge_rgb_range(self, position[i][0] - dx * j, position[i][1], 245, 255, 108, 128,
                                     134, 154):
                cnt += 1
        res.append(cnt)
    return res


def get_lesson_each_region_status(self):
    pd_lo = [[289, 204], [643, 204], [985, 204],
             [289, 359], [643, 359], [985, 359],
             [289, 511], [643, 511], [985, 511]]
    res = []
    for i in range(0, 9):
        if color.judge_rgb_range(self, pd_lo[i][0], pd_lo[i][1], 250, 255, 250, 255, 250, 255):
            res.append("available")
        elif color.judge_rgb_range(self, pd_lo[i][0], pd_lo[i][1], 230, 249, 230, 249, 230,
                                   249):
            res.append("done")
        elif color.judge_rgb_range(self, pd_lo[i][0], pd_lo[i][1], 31, 160, 31, 160, 31, 160):
            res.append("lock")
        elif color.judge_rgb_range(self, pd_lo[i][0], pd_lo[i][1], 197, 217, 197, 217, 195,
                                   215):
            res.append("no activity")
        else:
            res.append("unknown")
    return res


def out_lesson_status(self, res):
    message = "schedule status:"
    for i in range(0, 9):
        if i % 3 == 0:
            message += "\n"
        message += "\t" + res[0][i]
        if res[0][i] == "available":
            message += " :" + str(res[1][i])
    self.logger.info(message)


def choose_lesson(self, res, region):
    if self.config['lesson_relationship_first']:
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
        pri = self.config['lesson_each_region_object_priority'][region]
        if pri == []:
            for i in range(8, -1, -1):
                if res[0][i] == "available":
                    return i
            return -1
        else:
            choice = -1
            max_relationship = -1
            for i in range(0, len(tier)):
                if tier[i] in pri:
                    for j in range(2 * (3 - i), 2 * (4 - i)):
                        if res[0][j] == "available" and res[1][j] > max_relationship:
                            if max_relationship != -1:
                                self.logger.info("Due to relationship priority, current choice forward from [ " + str(
                                    choice + 1) + " ] to [ " + str(j + 1) + " ]")
                            max_relationship = res[1][j]
                            choice = j
                        if choice != -1:
                            return choice
            return choice
