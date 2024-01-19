import time

import numpy as np

from core import color, image, picture


def implement(self):
    self.quick_method_to_main_page()
    self.lesson_times = self.config['lesson_times']
    region_name_origin = {
        'CN': ["沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区", "崔尼蒂广场区"],
        'Global': ["Schale Office", "Schale Residence Hall", "Gehenna Hub", "Abydos Main Building",
                   "Millennium Study Center", "Trinity Plaza Area", "Red Winter Federal Academy",
                   "Hyakkiyako Central Area", "D.U. Shiratori City"]
    }
    region_name = region_name_origin[self.server]
    region_name_len = np.zeros(len(region_name))
    letter_dict = []
    for i in range(0, len(region_name)):
        letter_dict.append({chr(i): 0 for i in range(ord('a'), ord('z') + 1)})
        for j in range(0, len(region_name[i])):
            if is_english_letter(region_name[i][j]):
                region_name_len[i] += 1
                letter_dict[i][region_name[i][j].lower()] += 1
    pd_lo = {
        'CN': [[307, 257], [652, 257], [995, 257],
               [307, 408], [652, 408], [995, 408],
               [307, 560], [652, 560], [985, 560]],
        'Global': [[289, 204], [643, 204], [985, 204],
                   [289, 359], [643, 359], [985, 359],
                   [289, 511], [643, 511], [985, 511]]
    }
    pd_lo = pd_lo[self.server]
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
        lesson_tickets = 7
    else:
        lesson_tickets = res[0]
        self.logger.info("tickets: " + str(lesson_tickets))
        if lesson_tickets == 0:
            self.logger.info("no tickets")
            return True
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    for k in range(0, len(self.lesson_times)):
        if self.lesson_times[k] == 0:
            continue
        tar_num = k
        times = self.lesson_times[k]
        self.logger.info("begin schedule in [" + region_name[k] + "]")

        to_select_location(self, True)
        cur_num = get_region_num(self, region_name, letter_dict, region_name_len)
        if cur_num == 'NOT FOUND':
            return True
        self.logger.info("now in page " + region_name[cur_num])
        while cur_num != tar_num and self.flag_run:
            if cur_num > tar_num:
                if (cur_num - tar_num) * 2 < len(region_name):
                    self.click(left_change_page_x, change_page_y, count=cur_num - tar_num, wait=False,
                               duration=1.5, wait_over=True)
                else:
                    self.click(right_change_page_x, change_page_y, count=len(region_name) - cur_num + tar_num,
                               wait=False, duration=1.5, wait_over=True)
            else:
                if (tar_num - cur_num) * 2 < len(region_name):
                    self.click(right_change_page_x, change_page_y, count=tar_num - cur_num, duration=1.5,
                               wait_over=True)
                else:
                    self.click(left_change_page_x, change_page_y, count=len(region_name) - tar_num + cur_num,
                               wait=False, duration=1.5, wait_over=True)
            to_select_location(self)
            cur_num = get_region_num(self, region_name, letter_dict, region_name_len)
            if cur_num == 'NOT FOUND':
                return True
            self.logger.info("now in page " + region_name[cur_num])
        for j in range(0, times):
            to_all_locations(self, True)
            res = []
            last_available = -1
            for i in range(0, 9):
                if color.judge_rgb_range(self.latest_img_array, pd_lo[i][0], pd_lo[i][1], 250, 255, 250, 255, 250, 255):
                    res.append("available")
                    last_available = i
                elif color.judge_rgb_range(self.latest_img_array, pd_lo[i][0], pd_lo[i][1], 230, 249, 230, 249, 230,
                                           249):
                    res.append("done")
                elif color.judge_rgb_range(self.latest_img_array, pd_lo[i][0], pd_lo[i][1], 140, 160, 140, 160, 140,
                                           160):
                    res.append("lock")
                elif color.judge_rgb_range(self.latest_img_array, pd_lo[i][0], pd_lo[i][1], 197, 217, 197, 217, 195,
                                           215):
                    res.append("no activity")
                else:
                    res.append("unknown")
            self.logger.info("schedule status: ")
            self.logger.info(res[0:3])
            self.logger.info(res[3:6])
            self.logger.info(res[6:9])

            if last_available == -1:
                break

            to_location_info(self, click_lo[last_available][0], click_lo[last_available][1])
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


def get_region_num(self, region_name, letter_dict=None, region_name_len=None):
    region = {
        'CN': (925, 94, 1240, 128),
        'Global': (932, 94, 1240, 129),
    }
    if self.server == 'CN':
        name = self.ocr.get_region_pure_chinese(self.latest_img_array, region[self.server])
        self.logger.info("lesson_name: " + name)
        for i in range(0, len(region_name)):
            if len(name) >= len(region_name[i]):
                if name[len(name) - len(region_name[i]):] == region_name[i]:
                    return i
        self.logger.error("can't find lesson name")
        return 'NOT FOUND'
    elif self.server == 'Global':
        name = self.ocr.get_region_pure_english(self.latest_img_array, region[self.server])
        if name[0:4].lower() == 'rank':
            name = name[5:]
        acc, word_len = get_lesson_region_num(name, letter_dict)
        res = []
        for j in range(0, len(acc)):
            res.append(acc[j] / max(word_len, region_name_len[j]))
        return np.argmax(res)


def get_lesson_tickets(self):
    region = {
        "CN": (280, 85, 320, 114),
        "Global": (220, 88, 262, 112),
        "JP": (220, 88, 232, 112),
    }
    ocr_res = self.ocr.get_region_res(self.latest_img_array, region[self.server], 'Global')
    if ocr_res[0] == 'Z':
        return [7, 7]
    if ocr_res[1] == '1':
        return [int(ocr_res[0]), int(ocr_res[2])]
    for j in range(0, len(ocr_res)):
        if ocr_res[j] == '/':
            return [int(ocr_res[:j]), int(ocr_res[j + 1:])]
    self.logger.info("tickets: UNKNOWN")
    return "UNKNOWN"


def purchase_lesson_ticket(self, times):
    self.click(148, 101, wait=False, rate=1.5)
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


def is_english_letter(char):
    return char.isalpha() and (char.isupper() or char.islower())


def get_lesson_region_num(words, letter_dict):
    word_dict = {chr(i): 0 for i in range(ord('a'), ord('z') + 1)}
    word_len = 0
    for i in range(0, len(words)):
        if is_english_letter(words[i]):
            word_len += 1
            word_dict[words[i].lower()] += 1
    acc_word = np.zeros(len(letter_dict))
    for i in range(0, len(letter_dict)):
        for j in range(0, 26):
            acc_word[i] += min(letter_dict[i][chr(j + ord('a'))], word_dict[chr(j + ord('a'))])
    return acc_word, word_len


def to_location_info(self, x, y):
    possibles = {"lesson_all-locations": (x, y)}
    image.detect(self, end='lesson_lesson-information', possibles=possibles, skip_first_screenshot=True)


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
    rgb_possibles = {'relationship_rank_up': (640, 360)}
    picture.co_detect(self, None,rgb_possibles, img_ends, img_possibles, skip_first_screenshot)
