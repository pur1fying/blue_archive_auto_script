import threading
import time
import cv2
import numpy as np
from core import image, color, picture


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    op = np.full(2, False, dtype=bool)
    op[1] = get_invitation_ticket_status(self)
    op[0] = get_cafe_earning_status(self)
    if op[0]:
        self.logger.info("Collect Cafe Earnings")
        collect(self, True)
        to_cafe(self)
    if op[1]:
        invite_girl(self, 1)
    interaction_for_cafe_solve_method3(self)
    if self.server == 'JP':
        self.logger.info("start no2 cafe relationship interaction")
        to_no2_cafe(self)
        if get_invitation_ticket_status(self):
            invite_girl(self, 2)
        interaction_for_cafe_solve_method3(self)
    return True


def to_cafe(self, skip_first_screenshot=False):
    img_possibles = {
        'cafe_cafe-reward-status': (904, 159),
        'cafe_invitation-ticket': (835, 97),
        'cafe_students-arrived': (922, 189),
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (908, 138)
    }
    rgb_possibles = {
        "main_page": [95, 699],
        'gift': [1240, 577],
        'reward_acquired': [640, 154],
        'relationship_rank_up': [640, 360]
    }
    picture.co_detect(self, 'cafe', rgb_possibles, 'cafe_menu', img_possibles, skip_first_screenshot)


def to_no2_cafe(self):
    self.click(112, 97, wait_over=True, duration=0.5)
    self.click(245, 159, wait_over=True, duration=0.5)
    to_cafe(self)


def match(img):
    res = []
    for i in range(1, 5):
        template = cv2.imread("src/images/CN/cafe/happy_face" + str(i) + ".png")
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.75
        locations = np.where(result >= threshold)
        for pt in zip(*locations[::-1]):
            res.append([int(pt[0] + template.shape[1] / 2), int(pt[1] + template.shape[0] / 2 + 58)])
    return res


def cafe_to_gift(self):
    click_pos = [[163, 639]]
    los = ["cafe"]
    ends = ["gift"]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def shot(self):
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()


def gift_to_cafe(self):
    click_pos = [[1240, 574]]
    los = ["gift"]
    ends = ["cafe"]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def interaction_for_cafe_solve_method3(self):
    self.connection().pinch_in()
    self.swipe(709, 558, 709, 209, duration=0.2)
    max_times = 4
    for i in range(0, max_times):
        cafe_to_gift(self)
        t1 = threading.Thread(target=shot, args=(self,))
        t1.start()
        self.swipe(131, 660, 1280, 660, duration=0.5)
        t1.join()
        res = match(self.latest_img_array)
        gift_to_cafe(self)
        if res:
            res.sort(key=lambda x: x[0])
            temp = 0
            while temp < len(res):
                if temp == len(res) - 1:
                    break
                tt = temp + 1
                pop_f = False
                while abs(res[temp][0] - res[tt][0]) <= 10:
                    if abs(res[temp][1] - res[tt][1]) <= 10:
                        res.pop(tt)
                        pop_f = True
                        if tt > len(res) - 1:
                            break
                    else:
                        tt = tt + 1
                        if tt > len(res) - 1:
                            break
                if not pop_f:
                    temp += 1
                else:
                    continue
            self.logger.info("totally find " + str(len(res)) + " interactions")
            for j in range(0, len(res)):
                self.click(res[j][0], min(res[j][1], 591), wait=False, wait_over=True)

        if i != max_times - 1:
            time.sleep(2)
            to_cafe(self)
            self.click(68, 636, wait_over=True)
            time.sleep(1)
            self.click(1169, 90, wait_over=True)
            time.sleep(1)


def to_invitation_ticket(self, skip_first_screenshot=False):
    img_possible = {
        'cafe_cafe-reward-status': (905, 159),
        'cafe_menu': (838, 647),
    }
    img_end = 'cafe_invitation-ticket'
    picture.co_detect(self, None, None, img_end, img_possible, skip_first_screenshot)


def get_student_name(self):
    current_server_student_name_list = []
    target = self.server + "_name"
    for i in range(0, len(self.static_config['student_names'])):
        current_server_student_name_list.append(self.static_config['student_names'][i][target])
    return operate_name(current_server_student_name_list, self.server)


def invite_girl(self, no=1):
    student_name = get_student_name(self)
    if no == 1:
        target_name_list = self.config['favorStudent1']
    elif no == 2:
        target_name_list = self.config['favorStudent2']
    student_name.sort(key=len, reverse=True)
    self.logger.info("INVITING : " + str(target_name_list))
    f = True
    for i in range(0, len(target_name_list)):
        to_invitation_ticket(self, skip_first_screenshot=True)
        target_name = target_name_list[i]
        self.logger.info("Begin Find Student " + target_name)
        target_name = operate_name(target_name, self.server)
        stop_flag = False
        last_student_name = None
        while not stop_flag:
            region = {
                'CN': (489, 185, 709, 604),
                'Global': (489, 185, 709, 604),
                'JP': (489, 185, 709, 604),
            }
            out = operate_student_name(
                self.ocr.get_region_raw_res(self.latest_img_array, region[self.server], model=self.server))
            detected_name = []
            location = []
            for k in range(0, len(out)):
                temp = out[k]['text']
                res = operate_name(temp, self.server)
                for j in range(0, len(student_name)):  # 此处可用二分查找优化
                    if res == student_name[j]:
                        if student_name[j] == "干世":
                            detected_name.append("千世")
                        else:
                            detected_name.append(student_name[j])
                        location.append(out[k]['position'][0][1] + 210)
                        if len(detected_name) == 5:
                            break

            if len(detected_name) == 0:
                self.logger.info("No name detected")
                break
            st = ""
            for x in range(0, len(detected_name)):
                st = st + detected_name[x]
                if x != len(detected_name) - 1:
                    st = st + ","
            self.logger.info("detected name : [ " + st + " ]")
            if detected_name[len(detected_name) - 1] == last_student_name:
                self.logger.warning("Can't detect target student")
                stop_flag = True
            else:
                last_student_name = detected_name[len(detected_name) - 1]
                for s in range(0, len(detected_name)):
                    if detected_name[s] == target_name:
                        self.logger.info("find student " + target_name + " at " + str(location[s]))
                        stop_flag = True
                        f = False
                        self.click(784, location[s], wait=False, duration=0.7, wait_over=True)
                        self.click(770, 500, wait=False, wait_over=True)
                        break
                if not stop_flag:
                    self.logger.info("didn't find target student swipe to next page")
                    self.swipe(412, 580, 412, 150, duration=0.3)
                    self.click(412, 500, wait=False, wait_over=True)
                    self.latest_img_array = self.get_screenshot_array()
        to_cafe(self, skip_first_screenshot=True)
        if not f:
            break


def collect(self, skip_first_screenshot=False):
    self.click(1150, 643, duration=1, wait_over=True)
    self.click(640, 522, wait_over=True)


def get_invitation_ticket_status(self):
    if color.judge_rgb_range(self.latest_img_array, 851, 647, 250, 255, 250, 255, 250, 255):
        self.logger.info("Invite ticket available for use")
        return True
    else:
        self.logger.info("Invitation ticket unavailable")
        return False


def get_cafe_earning_status(self):
    if not image.compare_image(self, 'cafe_0.0', 3):
        return True


def find_k_b_of_point1_and_point2(point1, point2):
    k = (point1[1] - point2[1]) / (point1[0] - point2[0])
    b = point1[1] - k * point1[0]
    return k, b


def operate_name(name, server):
    if type(name) is str:
        t = ""
        for i in range(0, len(name)):
            if name[i] == '(' or name[i] == "（" or name[i] == ")" or \
                name[i] == "）" or name[i] == ' ':
                continue
            elif server == 'JP' and is_english(name[i]):
                continue
            else:
                t = t + name[i]
        return t.lower()
    for i in range(0, len(name)):
        t = ""
        for j in range(0, len(name[i])):
            if name[i][j] == '(' or name[i][j] == "（" or name[i][j] == ")" or \
                name[i][j] == "）" or name[i][j] == ' ':
                continue
            elif server == 'JP' and is_english(name[i]):
                continue
            else:
                t = t + name[i][j]
        name[i] = t.lower()
    return name


def operate_student_name(names):
    res = []
    i = 0
    length = len(names)
    while i < length - 1:
        start_position = names[i]['position']
        temp = [(start_position[0][0], names[i]['text'])]
        while calc_y_difference(start_position, names[i + 1]['position']) <= 10 and i < length - 2:
            temp.append((names[i + 1]['position'][0][0], names[i + 1]['text']))
            i += 1
        temp.sort(key=lambda x: x[0])
        t = ""
        for j in range(0, len(temp)):
            t += temp[j][1]
        res.append({'text': t, 'position': start_position})
        i += 1
    return res


def calc_y_difference(position1, position2):
    return abs(position1[0][1] - position2[0][1]) + abs(position1[1][1] - position2[1][1])


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
