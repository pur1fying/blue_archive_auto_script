import threading
import time
import cv2
import numpy as np
from core import image, color, picture


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    if self.config['cafe_reward_collect_hour_reward'] and get_cafe_earning_status(self):
        self.logger.info("Collect Cafe Earnings")
        collect(self)
        to_cafe(self, False)
    if self.config['cafe_reward_use_invitation_ticket'] and get_invitation_ticket_status(self):
        invite_girl(self, 1)
    interaction_for_cafe_solve_method3(self)
    if (self.server == 'JP' or self.server == 'Global') and self.config['cafe_reward_has_no2_cafe']:
        self.logger.info("start no2 cafe relationship interaction")
        to_no2_cafe(self)
        if get_invitation_ticket_status(self) and self.config['cafe_reward_use_invitation_ticket']:
            invite_girl(self, 2)
        interaction_for_cafe_solve_method3(self)
    return True


def to_cafe(self, skip_first_screenshot=False):
    reward_status_cross_x = {
        'CN': 904,
        'JP': 985,
        'Global': 985,
    }
    img_possibles = {
        "cafe_gift": (1240, 577),
        'cafe_cafe-reward-status': (reward_status_cross_x[self.server], 159),
        'cafe_invitation-ticket': (835, 97),
        'cafe_students-arrived': (922, 189),
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (908, 138)
    }
    rgb_possibles = {
        "main_page": (95, 699),
        'gift': (1240, 577),
        'reward_acquired': (640, 154),
        'relationship_rank_up': (640, 360)
    }
    picture.co_detect(self, 'cafe', rgb_possibles, 'cafe_menu', img_possibles, skip_first_screenshot)


def to_no2_cafe(self):
    to_cafe(self)
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
    img_ends = "cafe_gift"
    rgb_possibles = {"cafe": (163, 639)}
    rgb_ends = "gift"
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, None, True)


def shot(self):
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()


def gift_to_cafe(self):
    img_possibles = {
        'cafe_gift': (1240, 574),
    }
    rgb_possibles = {"gift": (1240, 574)}
    rgb_ends = "cafe"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)


def interaction_for_cafe_solve_method3(self):
    self.connection().pinch_in(percent=50, steps=30)
    self.swipe(709, 558, 709, 309, duration=0.2)
    max_times = 4
    for i in range(0, max_times):
        cafe_to_gift(self)
        t1 = threading.Thread(target=shot, args=(self,))
        t1.start()
        self.swipe(131, 660, 1280, 660, duration=0.5)
        t1.join()
        img = cv2.resize(self.latest_img_array, (1280, 720), interpolation=cv2.INTER_AREA)
        res = match(img)
        gift_to_cafe(self)
        index = 0
        while index < len(res):
            if res[index][0] > 1174 and res[index][1] < 134:
                res.pop(index)
            else:
                index += 1
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
                self.click(res[j][0], min(res[j][1], 591), wait_over=True)

        if i != max_times - 1:
            time.sleep(2)
            to_cafe(self)
            self.click(68, 636, wait_over=True, duration=1)
            self.click(1169, 90, wait_over=True, duration=1)


def to_invitation_ticket(self, skip_first_screenshot=False):
    img_end = [
        'cafe_invitation-ticket',
        'cafe_invitation-ticket-invalid',
    ]
    img_possible = {
        'cafe_cafe-reward-status': (905, 159),
        'cafe_menu': (838, 647),
    }
    return picture.co_detect(self, None, None, img_end, img_possible, skip_first_screenshot)


def get_student_name(self):
    current_server_student_name_list = []
    target = self.server + "_name"
    for i in range(0, len(self.static_config['student_names'])):
        current_server_student_name_list.append(self.static_config['student_names'][i][target])
    return operate_name(current_server_student_name_list, self.server)


def invite_lowest_affection(self):
    self.logger.info("Invite lowest affection student")
    relationship_order_button_location = {
        'CN': (749, 263),
        'Global': (535, 323),
        'JP': (535, 323),
    }
    if to_invitation_ticket(self, True) == 'cafe_invitation-ticket-invalid':
        self.logger.info("invitation ticket NOT available")
        return
    if not image.compare_image(self, 'cafe_invitation-ticket-order-affection', threshold=0.9):
        self.logger.info("Switch to affection order")
        self.click(704, 152, wait_over=True, duration=0.5)
        self.click(relationship_order_button_location[self.server][0],
                   relationship_order_button_location[self.server][1], wait_over=True, duration=0.5)
        self.click(627, 390, wait_over=True, duration=0.5)
    self.latest_img_array = self.get_screenshot_array()
    if not image.compare_image(self, 'cafe_invitation-ticket-order-up', threshold=0.9):
        self.logger.info("Switch to lowest affection order")
        self.click(812, 153, wait_over=True, duration=0.5)
    to_confirm_invite(self, (785, 226))
    confirm_invite(self)


def to_confirm_invite(self, lo):
    img_possibles = {
        'cafe_invitation-ticket': lo,
    }
    img_ends = [
        "cafe_confirm-invite",
        "cafe_switch-clothes-notice",
        "cafe_duplicate-invite-notice",
    ]
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def confirm_invite(self):
    img_possibles = {
        "cafe_confirm-invite": (767, 514),
        "cafe_duplicate-invite": (767, 514),
        'cafe_invitation-ticket': (835, 97),
        'cafe_switch-clothes-notice': (764, 501),
        "cafe_duplicate-invite-notice": (764, 514),
    }
    img_ends = "cafe_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def invite_girl(self, no=1):
    if self.config['cafe_reward_lowest_affection_first']:
        invite_lowest_affection(self)
        return
    student_name = get_student_name(self)
    if no == 1:
        target_name_list = self.config['favorStudent1']
    elif no == 2:
        target_name_list = self.config['favorStudent2']
    student_name.sort(key=len, reverse=True)
    self.logger.info("INVITING : " + str(target_name_list))
    for i in range(0, len(target_name_list)):
        to_invitation_ticket(self, skip_first_screenshot=True)
        target_name = target_name_list[i]
        self.logger.info("Begin Find Student " + target_name)
        target_name = operate_name(target_name, self.server)
        stop_flag = False
        last_student_name = None
        while not stop_flag and self.flag_run:
            region = {
                'CN': (489, 185, 709, 604),
                'Global': (489, 185, 709, 604),
                'JP': (489, 185, 709, 604),
            }
            out = operate_student_name(
                self.ocr.get_region_raw_res(self.latest_img_array, region[self.server], self.server, self.ratio))
            detected_name = []
            location = []
            for k in range(0, len(out)):
                temp = out[k]['text']
                res = operate_name(temp, self.server)
                for j in range(0, len(student_name)):
                    if res == student_name[j]:
                        if student_name[j] == "干世":
                            detected_name.append("千世")
                        else:
                            detected_name.append(student_name[j])
                        location.append((out[k]['position'][0][1] / self.ratio) + 210)
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
                        to_confirm_invite(self, (785, location[s]))
                        confirm_invite(self)
                        return True
                if not stop_flag:
                    self.logger.info("didn't find target student swipe to next page")
                    self.swipe(412, 580, 412, 150, duration=0.3)
                    self.click(412, 500, wait_over=True)
                    self.latest_img_array = self.get_screenshot_array()
        to_cafe(self)


def to_cafe_earning_status(self):
    rgb_possibles = {
        'cafe': (1142, 639)
    }
    img_ends = "cafe_cafe-reward-status"
    img_possibles = {
        'cafe_students-arrived': (922, 189),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def collect(self):
    to_cafe_earning_status(self)
    if color.judge_rgb_range(self, 563, 539, 225, 255, 213, 255, 55, 95):
        self.logger.info("Collect Cafe Earnings")
        self.click(643, 521, wait_over=True)


def get_invitation_ticket_status(self):
    if color.judge_rgb_range(self, 851, 647, 250, 255, 250, 255, 250, 255):
        self.logger.info("Invite ticket available for use")
        return True
    else:
        self.logger.info("Invitation ticket unavailable")
        return False


def get_cafe_earning_status(self):
    if not image.compare_image(self, 'cafe_0.0'):
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
