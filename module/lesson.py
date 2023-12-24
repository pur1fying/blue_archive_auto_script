import numpy as np

from core import color, image
import time

from gui.util import log
from datetime import datetime

x = {
    'location-selection': (107, 9, 162, 36),
    'choose-lesson': (107, 9, 224, 40),
    'lesson-information': (575, 100, 703, 135),
    'all-locations': (575, 100, 703, 135),
    'lesson-report': (582, 120, 705, 158),
    'inadequate-lesson-ticket': (694,313,747,348)
}


def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    next_time = datetime(year, month, day + 1, 4)
    return next_time.timestamp()


def implement(self):
    self.quick_method_to_main_page()
    self.lesson_times = self.config['lesson_times']
    if self.server == 'CN':
        return cn_implement(self)
    elif self.server == 'Global':
        return global_implement(self)


def get_region_num(self, region_name, letter_dict=None, region_name_len=None):
    if self.server == 'CN':
        self.latest_img_array = self.get_screenshot_array()
        t1 = time.time()
        name = self.ocrCN.ocr_for_single_line(self.latest_img_array[97:128, 925:1240])['text']
        t2 = time.time()
        self.logger.info("ocr_lesson_name:" + str(t2 - t1))
        for i in range(4, -1, -1):
            if name[i] in ['评', '级', ' '] or name[i].isdigit():
                name = name[i + 1:]
                break
        acc = []
        for i in range(0, len(region_name)):
            cnt = 0
            for j in range(0, min(len(region_name[i]), len(name))):
                if region_name[i][j] == name[j]:
                    cnt += 1
            acc.append(cnt / len(region_name[i]))
        return np.argmax(acc)
    elif self.server == 'Global':
        img = self.latest_img_array[101:129, 932:1253, :]
        t1 = time.time()
        ocr_res = self.ocrEN.ocr_for_single_line(img)
        t2 = time.time()
        self.logger.info("ocr_lesson_region:" + str(t2 - t1))
        temp = ocr_res['text']
        if temp[0:4].lower() == 'rank':
            temp = temp[5:]
        acc, word_len = get_lesson_region_num(temp, letter_dict)
        res = []
        for j in range(0, len(acc)):
            res.append(acc[j] / max(word_len, region_name_len[j]))
        return np.argmax(res)


def cn_implement(self):
    region_name = ["沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区", "崔尼蒂广场区"]

    lo = [[307, 257], [652, 257], [995, 257],
          [307, 408], [652, 408], [995, 408],
          [307, 560], [652, 560], [985, 560]]

    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    for k in range(0, len(self.lesson_times)):
        if self.lesson_times[k] == 0:
            continue
        tar_num = k
        times = self.lesson_times[k]
        self.logger.info("begin schedule in [" + region_name[k] + "]")

        to_before_all_locations(self)
        cur_num = get_region_num(self, region_name)
        self.logger.info("now in page " + region_name[cur_num])
        while cur_num != tar_num:
            if cur_num > tar_num:
                if (cur_num - tar_num) * 2 < len(region_name):
                    self.click(left_change_page_x, change_page_y, count=cur_num - tar_num, wait=False, duration=1.5)
                else:
                    self.click(right_change_page_x, change_page_y, count=len(region_name) - cur_num + tar_num,
                               wait=False, duration=1.5)
            else:
                if (tar_num - cur_num) * 2 < len(region_name):
                    self.click(right_change_page_x, change_page_y, count=tar_num - cur_num, duration=1.5)
                else:
                    self.click(left_change_page_x, change_page_y, count=len(region_name) - tar_num + cur_num,
                               wait=False, duration=1.5)
            to_before_all_locations(self)
            cur_num = get_region_num(self, region_name)
            self.logger.info("now in page " + region_name[cur_num])
        for j in range(0, times):
            to_all_locations(self)
            res = []
            last_available = -1
            for i in range(0, 9):
                if color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 250, 255, 250, 255, 250, 255):
                    res.append("available")
                    last_available = i
                elif color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 230, 249, 230, 249, 230, 249):
                    res.append("done")
                elif color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 140, 160, 140, 160, 140, 160):
                    res.append("lock")
                elif color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 197, 217, 197, 217, 195, 215):
                    res.append("no activity")
                else:
                    res.append("unknown")
            self.logger.info("schedule status: " + str(res))

            if last_available == -1:
                break

            to_location_info(self, lo[last_available][0], lo[last_available][1])
            res = start_lesson(self)
            if res == "lesson_inadequate-lesson-ticket":
                self.logger.info("INADEQUATE LESSON TICKET")
                return True
            if res == "lesson_report":
                self.logger.info("complete one lesson")
                continue
    return True


def global_implement(self):
    region_name = ["Schale Office", "Schale Residence Hall", "Gehenna Hub", "Abydos Main Building",
                   "Millennium Study Center", "Trinity Plaza Area", "Red Winter Federal Academy",
                   "Hyakkiyako Central Area", "D.U. Shiratori City"]
    region_name_len = np.zeros(len(region_name))
    letter_dict = []
    for i in range(0, 9):
        letter_dict.append({chr(i): 0 for i in range(ord('a'), ord('z') + 1)})
        for j in range(0, len(region_name[i])):
            if is_english_letter(region_name[i][j]):
                region_name_len[i] += 1
                letter_dict[i][region_name[i][j].lower()] += 1
    temp1 = []
    temp2 = []
    for i in range(0, len(self.lesson_times)):
        if self.lesson_times[i] == 0:
            continue
        temp1.append(i)
        temp2.append(self.lesson_times[i])

    to_lesson_location_selection(self)
    buy_ticket_times = min(self.config['purchase_lesson_ticket_times'], 4)  # ** 购买日程券的次数
    if buy_ticket_times > 0:
        purchase_lesson_ticket(self, buy_ticket_times)
    res = get_lesson_tickets(self)
    if res == "UNKNOWN":
        lesson_tickets = 7
    else:
        lesson_tickets = res[0]
        if lesson_tickets == 0:
            self.logger.info("no tickets")
            return True
    click_lo = [[307, 257], [652, 257], [995, 257],
                [307, 408], [652, 408], [995, 408],
                [307, 560], [652, 560], [985, 560]]
    lo = [[289, 204], [643, 204], [985, 204],
          [289, 359], [643, 359], [985, 359],
          [289, 511], [643, 511], [985, 511]
          ]
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    for k in range(0, len(temp1)):
        tar_num = temp1[k]
        times = temp2[k]
        self.logger.info("begin schedule in [" + region_name[temp1[k]] + "]")
        to_before_all_locations(self)
        cur_num = get_region_num(self, region_name, letter_dict, region_name_len)
        self.logger.info("now in page " + region_name[cur_num])
        while cur_num != tar_num:
            if cur_num > tar_num:
                if (cur_num - tar_num) * 2 < len(region_name):
                    self.click(left_change_page_x, change_page_y, count=cur_num - tar_num, wait=False, duration=1.5)
                else:
                    self.click(right_change_page_x, change_page_y, count=len(region_name) - cur_num + tar_num,
                               wait=False, duration=1.5)
            else:
                if (tar_num - cur_num) * 2 < len(region_name):
                    self.click(right_change_page_x, change_page_y, count=tar_num - cur_num, duration=1.5)
                else:
                    self.click(left_change_page_x, change_page_y, count=len(region_name) - tar_num + cur_num,
                               wait=False, duration=1.5)
            to_before_all_locations(self)
            cur_num = get_region_num(self, region_name, letter_dict, region_name_len)
            self.logger.info("now in page " + region_name[cur_num])

        for j in range(0, times):
            to_all_locations(self)
            res = []
            last_available = -1
            for i in range(0, 9):
                if color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 250, 255, 250, 255, 250, 255):
                    res.append("available")
                    last_available = i
                elif color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 230, 249, 230, 249, 230, 249):
                    res.append("done")
                elif color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 32, 52, 32, 52, 31, 51):
                    res.append("lock")
                elif color.judge_rgb_range(self.latest_img_array, lo[i][0], lo[i][1], 197, 217, 197, 217, 195, 215):
                    res.append("no activity")
                else:
                    res.append("unknown")
            self.logger.info("schedule status: " + str(res))

            if last_available == -1:
                break

            to_location_info(self, click_lo[last_available][0], click_lo[last_available][1])
            res = start_lesson(self)
            if res == "purchase_lesson_ticket":
                self.logger.info("INADEQUATE LESSON TICKET")
                return True
            if res == "lesson_report":
                lesson_tickets -= 1
                if lesson_tickets == 0:
                    self.logger.info("no tickets")
                    return True
    return True


def get_lesson_tickets(self):
    img = self.latest_img_array[88:112, 220:262]
    # cv2.imshow("img",img)
    # cv2.waitKey(0)
    t1 = time.time()
    ocr_res = self.ocrEN.ocr_for_single_line(img)
    t2 = time.time()
    print("ocr_lesson_ticket:", t2 - t1)
    self.logger.info("ocr_lesson_ticket:" + str(t2 - t1))
    temp = ""
    if ocr_res['text'][0] == 'Z':
        return [7, 7]
    for j in range(0, len(ocr_res['text'])):
        if ocr_res['text'][j] == '/':
            self.logger.info("tickets:" + temp)
            return [int(ocr_res["text"][:j]), int(ocr_res["text"][j + 1:])]
    self.logger.info("tickets: UNKNOWN")
    return "UNKNOWN"


def purchase_lesson_ticket(self, times):
    self.click(148, 101, wait=False, rate=1.5)
    if times == 4:  # max
        self.click(879, 346, wait=False)
    else:
        self.click(807, 346, count=times - 1, wait=False)

    click_pos = [
        [766, 507],
        [766, 507],
        [640, 116],
    ]
    pd_los = [
        "purchase_lesson_ticket",
        "purchase_ticket_notice",
        "reward_acquired",
    ]
    ends = [
        "lesson_location_selection",
    ]
    color.common_rgb_detect_method(self, click_pos, pd_los, ends)


def to_lesson_location_selection(self):
    click_pos = [
        [210, 655],
        [640, 116],
        [920, 165],
        [889, 180],

    ]
    los = [
        "main_page",
        "reward_acquired",
        "purchase_lesson_ticket",
        "purchase_ticket_notice",

    ]
    ends = [
        "lesson_location_selection"
    ]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def to_before_all_locations(self):
    if self.server == "CN":
        possibles = {
            'main_page_home-feature': (211, 664),
            'lesson_location-selection': (937, 186),
            'lesson_lesson-information': (964, 117),
            'lesson_all-locations': (1138, 117),
            'lesson_lesson-report':(642,556),
            'main_page_relationship-rank-up': (640, 360),
        }
        image.detect(self, 'lesson_choose-lesson', possibles)
    elif self.server == "Global":
        click_pos = [
            [210, 655],
            [916, 180],
            [1138, 114],
            [962, 114],
            [637, 116],
            [640, 558],
            [640, 153]
        ]
        los = [
            "main_page",
            "lesson_location_selection",
            "all_locations",
            "location_info",
            "area_rank_up",
            "lesson_report",
            "relationship_rank_up",
        ]
        ends = [
            "before_all_locations"
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)


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
    if self.server == 'CN':
        possibles = {
            "lesson_all-locations": (x, y)
        }
        image.detect(self, end='lesson_lesson-information', possibles=possibles)

    if self.server == 'Global':
        click_pos = [[x, y]]
        los = ["all_locations"]
        ends = ["location_info"]
        color.common_rgb_detect_method(self, click_pos, los, ends)


def start_lesson(self):
    if self.server == 'CN':
        possibles = {
            'lesson_lesson-information': (640, 556),
            'main_page_relationship-rank-up': (640, 360),
        }
        ends = [
            'lesson_lesson-report',
            'lesson_inadequate-lesson-ticket',
        ]
        return image.detect(self, end=ends, possibles=possibles,pre_func=color.detect_rgb_one_time,pre_argv=(self,[[640,100]],['area_rank_up'],[]))
    elif self.server == 'Global':
        click_pos = [
            [640, 556],
            [637, 116],
            [640, 153]
        ]
        los = [
            "location_info",
            "area_rank_up",
            "relationship_rank_up",
        ]
        ends = [
            "lesson_report",
            "purchase_lesson_ticket",
        ]
        return color.common_rgb_detect_method(self, click_pos, los, ends)


def to_all_locations(self):
    if self.server == "CN":
        possibles = {
            'lesson_choose-lesson': (1160, 664),
            'lesson_lesson-information': (964, 117),
            'lesson_location-selection': (937, 186),
            'lesson_lesson-report': (642, 556),
            'main_page_relationship-rank-up': (640, 360),

        }
        image.detect(self, 'lesson_all-locations', possibles)
    elif self.server == "Global":
        click_pos = [
            [1160, 664],
            [962, 114],
            [637, 116],
            [640, 558],
            [640, 153]
        ]
        los = [
            "before_all_locations",
            "location_info",
            "area_rank_up",
            "lesson_report",
            "relationship_rank_up",
        ]
        ends = [
            "all_locations",
        ]
        color.common_rgb_detect_method(self, click_pos, los, ends)
