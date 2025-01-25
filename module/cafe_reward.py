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
    if self.config['cafe_reward_has_no2_cafe']:
        self.logger.info("start no2 cafe relationship interaction")
        to_no2_cafe(self)
        if get_invitation_ticket_status(self) and self.config['cafe_reward_use_invitation_ticket']:
            invite_girl(self, 2)
        interaction_for_cafe_solve_method3(self)
    return True


def to_cafe(self, skip_first_screenshot=False):
    img_possibles = {
        "cafe_gift": (1240, 577),
        'cafe_cafe-reward-status': (985, 159),
        'cafe_invitation-ticket': (835, 97),
        'cafe_students-arrived': (922, 189),
        'main_page_full-notice': (887, 165),
        'main_page_insufficient-inventory-space': (908, 138),
        'cafe_duplicate-invite-notice': (534, 497),
        'cafe_switch-clothes-notice': (534, 497),
    }
    rgb_possibles = {
        "main_page": (95, 699),
        'gift': (1240, 577),
        'reward_acquired': (640, 154),
        'relationship_rank_up': (640, 360)
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, 'cafe', rgb_possibles, 'cafe_menu', img_possibles, skip_first_screenshot)


def to_no2_cafe(self):
    to_cafe(self)
    if self.server == "JP":
        img_ends = "cafe_button-goto-no1-cafe"
        img_possibles = {
            "cafe_button-goto-no2-cafe": (118, 98),
            "cafe_students-arrived": (922, 189),
        }
        picture.co_detect(self, None, None, img_ends, img_possibles, True)
        return
    img_ends = "cafe_at-no1-cafe"
    img_possibles = {"cafe_menu": (118, 98)}
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    image.click_to_disappear(self, "cafe_at-no1-cafe", 240, 168)
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
    rgb_possibles = {"cafe": (163, 639)}
    rgb_ends = "gift"
    img_ends = "cafe_gift"
    img_possibles = {'cafe_students-arrived': (922, 189)}
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, True)


def shot(self, delay):
    time.sleep(delay)
    self.latest_img_array = self.u2_get_screenshot()


def gift_to_cafe(self):
    img_possibles = {
        'cafe_gift': (1240, 574),
    }
    rgb_possibles = {"gift": (1240, 574)}
    rgb_ends = "cafe"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)


def interaction_for_cafe_solve_method3(self):
    self.u2().pinch_in(percent=50, steps=30)
    self.swipe(709, 558, 709, 309, duration=0.2)
    max_times = 4
    for i in range(0, max_times):
        cafe_to_gift(self)
        shotDelay = self.config["cafe_reward_interaction_shot_delay"]
        t1 = threading.Thread(target=shot, args=(self, shotDelay))
        t1.start()
        startT = time.time()
        self.u2_swipe(131, 660, 1280, 660, duration=0.5)
        swipeT = time.time() - startT
        swipeT = round(swipeT, 3)
        t1.join()
        img = cv2.resize(self.latest_img_array, (1280, 720), interpolation=cv2.INTER_AREA)
        res = match(img)
        if not res:
            self.logger.info("No interaction found")
            if swipeT < self.config["cafe_reward_interaction_shot_delay"] + 0.3:
                self.logger.warning("Swipe duration : [ " + str(swipeT) + "] should be a bit larger than shot delay : ""[ " + str(shotDelay) + " ]")
                self.logger.warning("It's might be caused by your emulator fps, please adjust it to lower than 60")
                if swipeT > 0.4:
                    self.logger.info("Adjusting shot delay to [ " + str(swipeT - 0.3) + " ], and retry")
                    self.config["cafe_reward_interaction_shot_delay"] = swipeT - 0.3
                    self.config_set.set("cafe_reward_interaction_shot_delay",
                                        self.config["cafe_reward_interaction_shot_delay"])
            time.sleep(1)
            continue
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
    invitation_ticket_x = {
        'CN': 838,
        'Global': 838,
        'JP': 887,
    }
    img_possible = {
        'cafe_cafe-reward-status': (905, 159),
        'cafe_menu': (invitation_ticket_x[self.server], 647),
        'cafe_duplicate-invite-notice': (534, 497),
        'cafe_switch-clothes-notice': (534, 497),
        'cafe_duplicate-invite': (534, 497),
    }
    return picture.co_detect(self, None, None, img_end, img_possible, skip_first_screenshot)


def get_student_name(self):
    current_server_student_name_list = []
    target = self.server + "_name"
    for i in range(0, len(self.static_config['student_names'])):
        current_server_student_name_list.append(self.static_config['student_names'][i][target])
    return operate_name(current_server_student_name_list, self.server)


def checkConfirmInvite(self, y):
    res = to_confirm_invite(self, (785, y))
    f = False
    if res == 'cafe_switch-clothes-notice' and not self.config['cafe_reward_allow_exchange_student']:
        self.logger.warning("Not Allow Student Switch Clothes")
        f = True
    elif res == 'cafe_duplicate-invite' and not self.config['cafe_reward_allow_duplicate_invite']:
        self.logger.warning("Not Allow Duplicate Invite")
        f = True
    if f:
        to_invitation_ticket(self, skip_first_screenshot=True)
        return False
    confirm_invite(self)
    return True


def invite_by_affection(self, affection_order):
    if to_invitation_ticket(self, True) == 'cafe_invitation-ticket-invalid':
        self.logger.info("Invitation Ticket Not Available")
        return
    order = {
        "lowest": "up",
        "highest": "down",
    }
    order = order[affection_order]
    self.logger.info("Invite affection [ " + affection_order + " ]")
    change_order_type(self, 'affection')
    change_invitation_ticket_up_down_order(self, order)
    i = 0
    lo = [226, 309, 378, 456, 536]
    while i < 5:
        if not checkConfirmInvite(self, lo[i]):
            i += 1
        else:
            return


def to_revise_order_type(self):
    img_possibles = {
        "cafe_invitation-ticket": (705, 151),
    }
    img_ends = "cafe_invitation-ticket-change-order-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def change_order_type(self, order_type):
    target = "cafe_invitation-ticket-order-" + order_type
    if image.compare_image(self, target, False, threshold=0.9):
        self.logger.info("Invitation ticket order [ " + order_type + " ]")
        return

    self.logger.info("Switch order --> [ " + order_type + " ]")
    to_revise_order_type(self)
    order_type_location = {
        'CN': {
            "academy": (754, 267),
            "affection": (529, 322),
            "starred": (532, 263),
        },
        'Global': {
            "name": (534, 256),
            "academy": (746, 256),
            "affection": (534, 317),
            "starred": (746, 317),
        },
        'JP': {
            "name": (534, 256),
            "academy": (746, 256),
            "affection": (534, 317),
            "starred": (746, 317),
        }
    }
    img_ends = "cafe_invitation-ticket-change-order-menu-" + order_type + "-chosen"
    img_possibles = {
        "cafe_invitation-ticket-change-order-menu": order_type_location[self.server][order_type],
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    image.click_to_disappear(self, "cafe_invitation-ticket-change-order-menu", 628, 395)


def change_invitation_ticket_up_down_order(self, order):
    opposite_order = {
        "up": "down",
        "down": "up",
    }
    img_ends = "cafe_invitation-ticket-order-" + order
    img_possibles = {
        "cafe_invitation-ticket-order-" + opposite_order[order]: (815, 151),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def to_confirm_invite(self, lo):
    img_possibles = {
        'cafe_invitation-ticket': lo,
    }
    img_ends = [
        "cafe_confirm-invite",
        "cafe_switch-clothes-notice",
        "cafe_duplicate-invite",
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def confirm_invite(self):
    img_possibles = {
        "cafe_confirm-invite": (767, 514),
        "cafe_duplicate-invite": (767, 514),
        "cafe_invitation-ticket": (835, 97),
        "cafe_switch-clothes-notice": (764, 501),
        "cafe_duplicate-invite-notice": (764, 514),
    }
    img_ends = "cafe_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def invite_starred(self, no):
    self.logger.info("Invite Starred Student")
    change_order_type(self, 'starred')
    change_invitation_ticket_up_down_order(self, 'down')
    lo = [0, 226, 309, 378, 456, 536]
    to_confirm_invite(self, (785, lo[no]))
    confirm_invite(self)


def invite_girl(self, no=1):
    if to_invitation_ticket(self, True) == 'cafe_invitation-ticket-invalid':
        self.logger.info("Invitation Ticket Not Available")
        return

    method = self.config['cafe_reward_invite' + str(no) + '_criterion']

    if method == 'lowest_affection':
        invite_by_affection(self, 'lowest')
        return
    elif method == 'highest_affection':
        invite_by_affection(self, 'highest')
        return
    elif method == 'starred':
        position = self.config["cafe_reward_invite" + str(no) + "_starred_student_position"]
        invite_starred(self, position)
        return

    target_name_list = self.config['favorStudent' + str(no)]

    if len(target_name_list) == 0:
        self.logger.warning("Current mode is invite target student but no student name configured in favorStudent" + str(no))
        self.logger.warning("Current mode fallback to invite by lowest affection")
        invite_by_affection(self, 'lowest')
        return
    # name
    student_name = get_student_name(self)  # all student name in current server
    student_name.sort(key=len, reverse=True)
    self.logger.info("Inviting : " + str(target_name_list))
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
            self.logger.info("Detected name : [ " + st + " ]")
            if detected_name[len(detected_name) - 1] == last_student_name:
                self.logger.warning("Already swipe to the end of the list")
                self.logger.warning("Can't Detect Target Student : [ " + target_name + " ].")
                stop_flag = True
            else:
                last_student_name = detected_name[len(detected_name) - 1]
                for s in range(0, len(detected_name)):
                    if detected_name[s] == target_name:
                        self.logger.info("Find Student " + target_name + " At " + str(location[s]))
                        if not checkConfirmInvite(self, location[s]):
                            stop_flag = True
                            break
                        return True
                if not stop_flag:
                    self.logger.info("Didn't Find Target Student Swipe to Next Page")
                    self.swipe(412, 580, 412, 150, duration=0.5)
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
    if color.judgeRGBFeature(self, "invitation_ticket_available_to_use"):
        self.logger.info("Invite ticket available for use")
        return True
    else:
        self.logger.info("Invitation ticket unavailable")
        return False


def get_cafe_earning_status(self):
    if not image.compare_image(self, 'cafe_0.0'):
        return True
    return False


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
