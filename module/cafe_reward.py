import cv2
import os
import time
import queue
import threading

import numpy as np

from core import image, color, picture
from core.utils import merge_nearby_coordinates
from statistics import median

_happy_face_templates = None
_happy_face_match_scale = 0.75
_happy_face_match_roi = (0, 45, 1280, 555)


def _resize_for_happy_face_match(img):
    height, width = img.shape[:2]
    size = (
        max(1, int(round(width * _happy_face_match_scale))),
        max(1, int(round(height * _happy_face_match_scale))),
    )
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)


def implement(self):
    self.to_main_page()
    to_cafe(self, True)
    if self.config.cafe_reward_collect_hour_reward and get_cafe_earning_status(self):
        collect(self)
        to_cafe(self, False)
    ticket1_next_time = None
    ticket2_next_time = None
    if self.config.cafe_reward_use_invitation_ticket:
        if not get_invitation_ticket_status(self):
            ticket1_next_time = get_invitation_ticket_next_time(self)
        else:
            invite_girl(self, 1)
    interaction_for_cafe_solve_method3(self)
    if self.config.cafe_reward_has_no2_cafe:
        self.logger.info("start no2 cafe relationship interaction")
        to_no2_cafe(self)
        if self.config.cafe_reward_use_invitation_ticket:
            if not get_invitation_ticket_status(self):
                ticket2_next_time = get_invitation_ticket_next_time(self)
            else:
                invite_girl(self, 2)
        interaction_for_cafe_solve_method3(self)

    # handle next time according to invitation ticket cool time and interval
    if ticket1_next_time is not None:
        self.next_time = ticket1_next_time
    if ticket2_next_time is not None:
        if self.next_time == 0:
            self.next_time = ticket2_next_time
        else:
            self.next_time = min(ticket2_next_time, self.next_time)
    if self.next_time > self.scheduler.get_interval('cafe_reward'):
        self.next_time = 0
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
        'cafe_specified-visit': (983,  96),
        'cafe_random-visit-notice': (886, 172),
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
    img_ends = "cafe_button-goto-no1-cafe"
    img_possibles = {
        "cafe_button-goto-no2-cafe": (118, 98),
        "cafe_students-arrived": (922, 189),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    return


def _get_happy_face_templates():
    global _happy_face_templates
    if _happy_face_templates is None:
        templates = []
        for i in range(1, 5):
            template = cv2.imread("src/images/CN/cafe/happy_face" + str(i) + ".png")
            if template is None:
                templates.append(None)
                continue
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            template = _resize_for_happy_face_match(template)
            templates.append(template)
        _happy_face_templates = templates
    return _happy_face_templates


def _dedupe_happy_face_points(points):
    deduped = []
    for x, y in sorted(points, key=lambda item: (item[1], item[0])):
        if any(abs(x - px) <= 24 and abs(y - py) <= 24 for px, py in deduped):
            continue
        deduped.append([x, y])
        if len(deduped) >= 32:
            break
    return deduped


def _match_happy_faces_by_color(img):
    roi_x0, roi_y0, roi_x1, roi_y1 = _happy_face_match_roi
    search_img = img[roi_y0:roi_y1, roi_x0:roi_x1]
    hsv = cv2.cvtColor(search_img, cv2.COLOR_BGR2HSV)
    lower_red = cv2.inRange(hsv, np.array([0, 55, 120]), np.array([12, 255, 255]))
    upper_red = cv2.inRange(hsv, np.array([160, 55, 120]), np.array([179, 255, 255]))
    mask = cv2.bitwise_or(lower_red, upper_red)
    count, _, stats, centers = cv2.connectedComponentsWithStats(mask, 8)
    points = []
    for i in range(1, count):
        _, _, width, height, area = stats[i]
        if not (8 <= area <= 500 and 4 <= width <= 40 and 4 <= height <= 40):
            continue
        cx, cy = centers[i]
        points.append([int(roi_x0 + cx), int(roi_y0 + cy + 58)])
    return _dedupe_happy_face_points(points)


def match(img):
    color_matches = _match_happy_faces_by_color(img)
    if color_matches or os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}:
        return color_matches

    res = []
    roi_x0, roi_y0, roi_x1, roi_y1 = _happy_face_match_roi
    search_img = img[roi_y0:roi_y1, roi_x0:roi_x1]
    search_img = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)
    search_img = _resize_for_happy_face_match(search_img)
    for template in _get_happy_face_templates():
        if template is None:
            continue
        result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.75
        suppress_x = max(20, template.shape[1])
        suppress_y = max(20, template.shape[0])
        for _ in range(16):
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val < threshold:
                break
            pt_x, pt_y = max_loc
            res.append([
                int(roi_x0 + (pt_x + template.shape[1] / 2) / _happy_face_match_scale),
                int(roi_y0 + (pt_y + template.shape[0] / 2) / _happy_face_match_scale + 58),
            ])
            left = max(0, pt_x - suppress_x)
            right = min(result.shape[1], pt_x + suppress_x + 1)
            top = max(0, pt_y - suppress_y)
            bottom = min(result.shape[0], pt_y + suppress_y + 1)
            result[top:bottom, left:right] = -1
    return res


def cafe_to_gift(self):
    rgb_possibles = {"cafe": (163, 639)}
    rgb_ends = "gift"
    img_ends = "cafe_gift"
    img_possibles = {
        'cafe_students-arrived': (922, 189),
        'cafe_specified-visit': (983, 96),
        'cafe_random-visit-notice': (886, 172),
    }
    picture.co_detect(self, rgb_ends, rgb_possibles, img_ends, img_possibles, True)


def screenshot_thread(self, delay):
    if not self.is_android_device:
        delay += 0.1
    time.sleep(delay)
    if self.is_android_device:
        self.latest_img_array = self.u2_get_screenshot()
    else:
        self.update_screenshot_array()
        cv2.imwrite("cafe_reward_shot.png", self.latest_img_array)

def gift_to_cafe(self):
    if self.is_android_device:
        self.click(1240, 574, wait_over=True)
        picture.co_detect(self, "cafe", None, None, None, False, time_out=15)
        return

    img_possibles = {
        'cafe_gift': (1240, 574),
    }
    rgb_possibles = {"gift": (1240, 574)}
    rgb_ends = "cafe"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)

def zoom_out(self):
    if self.is_android_device:
        self.u2().pinch_in(percent=50, steps=30)
    else:
        for _ in range(0, 15):
            self.control.scroll(640, 360, 10)
    duration = 0.2 if self.is_android_device else 0.5
    self.swipe(709, 558, 709, 309, duration=duration)

def swipe_gift_thread(self, duration, ret_queue):
    start_t = time.time()
    self.swipe(131, 660, 1280, 660, duration=duration)
    ret_queue.put(round(time.time() - start_t, 3))

def swipe_gift_and_screenshot(self):
    shotDelay = self.config.cafe_reward_interaction_shot_delay
    if self.is_android_device:
        t1 = threading.Thread(target=screenshot_thread, args=(self, shotDelay))
        t1.start()
        start_t = time.time()
        self.u2_swipe(131, 660, 1280, 660, duration=0.5)
        swipe_t = round(time.time() - start_t, 3)
        self.logger.info("Gift swipe duration : [ " + str(swipe_t) + " ]")
        return swipe_t
    else:
        q = queue.Queue()
        t1 = threading.Thread(target=swipe_gift_thread, args=(self, 1, q))
        t1.start()
        time.sleep(shotDelay + 0.1)
        self.update_screenshot_array()
        t1.join()
        return q.get()

def find_student_position(self):
    swipe_t = swipe_gift_and_screenshot(self)
    match_start_t = time.time()
    img = cv2.resize(self.latest_img_array, (1280, 720), interpolation=cv2.INTER_AREA)
    res = match(img)
    self.logger.info("Cafe interaction match duration : [ " + str(round(time.time() - match_start_t, 3)) + " ], candidates : [ " + str(len(res)) + " ]")
    if not res:
        self.logger.info("No interaction found")
        if swipe_t < self.config.cafe_reward_interaction_shot_delay + 0.3:
            self.logger.warning(
                "Swipe duration : [ " + str(swipe_t) + "] should be a bit larger than shot delay : ""[ " +
                str(self.config.cafe_reward_interaction_shot_delay) + " ]")
            self.logger.warning("It's might be caused by your emulator fps, please adjust it to lower than 60")
            if swipe_t > 0.4:
                self.logger.info("Adjusting shot delay to [ " + str(swipe_t - 0.3) + " ], and retry")
                self.config.cafe_reward_interaction_shot_delay = swipe_t - 0.3
                self.config_set.set("cafe_reward_interaction_shot_delay",
                                    self.config.cafe_reward_interaction_shot_delay)
        time.sleep(1)
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
        return res
    return []

def interaction_for_cafe_solve_method3(self):
    zoom_out(self)
    max_times = self.config.cafe_reward_affection_pat_round
    self.logger.info("Pat Round : [ " + str(max_times) + " ]")
    for i in range(0, max_times):
        cafe_to_gift(self)
        res = find_student_position(self)
        if len(res) == 0:
            continue
        self.logger.info("Find " + str(len(res)) + " interactions")
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
        'cafe_menu': (887, 647),
        'cafe_duplicate-invite-notice': (534, 497),
        'cafe_switch-clothes-notice': (534, 497),
        'cafe_duplicate-invite': (534, 497),
        'cafe_students-arrived': (922, 189)
    }
    return picture.co_detect(self, None, None, img_end, img_possible, skip_first_screenshot)


def checkConfirmInvite(self, y):
    res = to_confirm_invite(self, (785, y))
    f = False
    if res == 'cafe_switch-clothes-notice' and not self.config.cafe_reward_allow_exchange_student:
        self.logger.warning("Not Allow Student Switch Clothes")
        f = True
    elif (res == 'cafe_duplicate-invite' or res == 'cafe_duplicate-invite-notice') \
            and not self.config.cafe_reward_allow_duplicate_invite:
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
    if image.compare_image(self, target, threshold=0.9):
        self.logger.info("Invitation ticket order [ " + order_type + " ]")
        return

    self.logger.info("Switch order --> [ " + order_type + " ]")
    to_revise_order_type(self)
    order_type_location = {
        'CN': {
            "academy": (531, 267),
            "affection": (745, 267),
            "starred": (531, 317),
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
        "cafe_duplicate-invite-notice",
        "cafe_duplicate-invite",
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def confirm_invite(self):
    img_possibles = {
        "cafe_confirm-invite": (767, 514),
        "cafe_duplicate-invite": (767, 514),
        "cafe_switch-clothes-notice": (764, 501),
        "cafe_duplicate-invite-notice": (764, 514),
        "cafe_students-arrived": (922, 189)
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

    method = self.config_set.get('cafe_reward_invite' + str(no) + '_criterion')
    self.logger.info(f"No.{no} Cafe Invite Student Method : [ {method} ].")

    if method == 'lowest_affection':
        invite_by_affection(self, 'lowest')
        return
    elif method == 'highest_affection':
        invite_by_affection(self, 'highest')
        return
    elif method == 'starred':
        position = self.config_set.get("cafe_reward_invite" + str(no) + "_starred_student_position")
        invite_starred(self, position)
        return

    target_name_list = self.config_set.get('favorStudent' + str(no))

    if len(target_name_list) == 0:
        self.logger.warning(
            "Current mode is invite target student but no student name configured in favorStudent" + str(no))
        self.logger.warning("Current mode fallback to invite by lowest affection")
        invite_by_affection(self, 'lowest')
        return
    self.logger.info("Invite Student List : " + str(target_name_list))
    search_button_region = {
        'CN': (717, 185, 857, 604),
        'Global': (695, 187, 865, 604),
        'JP': (695, 187, 852, 604),
    }
    ocr_region_offsets = {
        'CN': (-255, -17, 225, 32),
        'Global': (-252, -14, 220, 27),
        'JP': (-258, -17, 222, 32),
    }
    search_button_region = search_button_region[self.server]
    ocr_region_offsets = ocr_region_offsets[self.server]
    for i in range(0, len(target_name_list)):
        to_invitation_ticket(self, skip_first_screenshot=True)
        target_name = target_name_list[i]
        self.logger.info("Target Student [ " + target_name + " ].")
        target_name = operate_name(target_name)
        stop_flag = False
        last_student_name = None
        while not stop_flag and self.flag_run:
            all_position = image.get_image_all_appear_position(
                self,
                'cafe_invite-student-button',
                search_button_region,
                threshold=0.8
            )
            if len(all_position) == 0:
                self.logger.warning("Can't Find Any Invite Student Button.")
                break
            all_position = merge_nearby_coordinates(all_position, 10, 10)
            detected_name = []
            for pos in all_position:
                x_coords = [coord[0] for coord in pos]
                y_coords = [coord[1] for coord in pos]
                p = (median(x_coords), median(y_coords))
                ocr_region = (
                    p[0] + ocr_region_offsets[0],
                    p[1] + ocr_region_offsets[1],
                    p[0] + ocr_region_offsets[0] + ocr_region_offsets[2],
                    p[1] + ocr_region_offsets[1] + ocr_region_offsets[3]
                )
                # img = image.screenshot_cut(self, ocr_region)
                # cv2.imshow("img", img)
                # cv2.waitKey(0)
                res = self.ocr.get_region_res(
                    baas=self,
                    region=ocr_region,
                    language=self.ocr_language,
                    log_info='Student Name',
                    candidates=''
                )
                detected_name.append(res)
                res = operate_name(res)
                if res == target_name:
                    self.logger.info("Find Target Student [ " + target_name + " ]")
                    if not checkConfirmInvite(self, p[1] + 10):
                        stop_flag = True
                        break
                    return True
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
                if not stop_flag:
                    self.logger.info("Didn't Find Target Student Swipe to Next Page")
                    self.swipe(412, 580, 412, 170, duration=0.5)
                    self.click(412, 500, wait_over=True)
                    self.update_screenshot_array()
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
    if color.rgb_in_range(self, 563, 539, 225, 255, 213, 255, 55, 95):
        self.logger.info("Collect Cafe Earnings")
        self.click(643, 521, wait_over=True)


def get_invitation_ticket_status(self):
    log = 'Invitation Ticket '
    if color.match_rgb_feature(self, "invitation_ticket_available_to_use"):
        self.logger.info(log + " Available To Use")
        return True
    else:
        self.logger.info(log + " Unavailable To Use")
        return False


def get_cafe_earning_status(self):
    if not image.compare_image(self, 'cafe_0.0'):
        return True
    return False


def find_k_b_of_point1_and_point2(point1, point2):
    k = (point1[1] - point2[1]) / (point1[0] - point2[0])
    b = point1[1] - k * point1[0]
    return k, b


# replace special characters in name and return lower case
def operate_name(name):
    name = name.replace(" ", "")
    name = name.replace(",", "")
    name = name.replace("，", "")
    name = name.replace("。", "")
    name = name.replace(".", "")
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace("（", "")
    name = name.replace("）", "")
    name = name.replace("[", "")
    name = name.replace("]", "")
    name = name.replace("【", "")
    name = name.replace("】", "")
    name = name.replace("{", "")
    name = name.replace("}", "")
    ret = ""
    for i in range(0, len(name)):
        if is_english(name[i]):
            ret += name[i].lower()
        else:
            ret += name[i]
    return ret


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


def get_invitation_ticket_next_time(self):
    for i in range(0, 3):
        if i != 0:
            self.update_screenshot_array()
        res = self.ocr.get_region_res(
            baas=self,
            region=(850, 588, 926, 614),
            language='en-us',
            log_info='Invitation Ticket Next Time',
            candidates='0123456789:'
        )
        if res.count(":") != 2:
            return None
        res = res.split(":")
        for j in range(0, len(res)):
            if res[j][0] == "0":
                res[j] = res[j][1:]
        try:
            return int(res[0]) * 3600 + int(res[1]) * 60 + int(res[2])
        except ValueError:
            pass
    return 0
