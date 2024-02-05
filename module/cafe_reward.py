import threading
import time

import cv2
import numpy as np

from core import image, color, picture


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    self.latest_img_array = self.get_screenshot_array()
    op = np.full(2, False, dtype=bool)
    op[1] = get_invitation_ticket_status(self)
    op[0] = get_cafe_earning_status(self)
    if op[0]:
        self.logger.info("Collect Cafe Earnings")
        collect(self, True)
        to_cafe(self)
    if op[1]:
        invite_girl(self)
    interaction_for_cafe_solve_method3(self)
    if self.server == 'JP':
        self.logger.info("start no2 cafe relationship interaction")
        to_no2_cafe(self)
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


def match(img, server):
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
        res = match(self.latest_img_array, server=self.server)
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

        time.sleep(2)
        to_cafe(self)
        if i != max_times - 1:
            self.click(68, 636, wait_over=True)
            time.sleep(1)
            self.click(1169, 90, wait_over=True)
            time.sleep(1)


def to_invitation_ticket(self, skip_first_screenshot=False):
    if self.server == "CN":
        possible = {
            'cafe_cafe-reward-status': (905, 159, 3),
            'cafe_menu': (838, 647, 3),
        }
        end = 'cafe_invitation-ticket'
        return image.detect(self, end, possible, skip_first_screenshot=skip_first_screenshot)
    elif self.server == "Global":
        click_pos = [[836, 650]]
        los = ["cafe"]
        end = ["invitation_ticket"]
        color.common_rgb_detect_method(self, click_pos, los, end, skip_first_screenshot=skip_first_screenshot)


def invite_girl(self):
    student_name = None
    if self.server == "CN":
        student_name = self.static_config['CN_student_name']
    elif self.server == "Global":
        student_name = self.static_config['Global_student_name']
    elif self.server == "JP":
        self.logger.warning("JP server not support")
        return False
    assert student_name is not None
    for i in range(0, len(student_name)):
        t = ""
        for j in range(0, len(student_name[i])):
            if student_name[i][j] == '(' or student_name[i][j] == "（" or student_name[i][j] == ")" or \
                student_name[i][j] == "）" or student_name[i][j] == ' ':
                continue
            else:
                t = t + student_name[i][j]
        student_name[i] = t.lower()

    target_name_list = self.config['favorStudent']
    student_name.sort(key=len, reverse=True)
    self.logger.info("inviting : " + str(target_name_list))
    for i in range(0, len(target_name_list)):
        t = ""
        for j in range(0, len(target_name_list[i])):
            if target_name_list[i][j] == '(' or target_name_list[i][j] == "（" or target_name_list[i][j] == ")" or \
                target_name_list[i][j] == "）" or target_name_list[i][j] == ' ':
                continue
            else:
                t = t + target_name_list[i][j]
        # target_name_list = t.lower() + target_name_list[1:]
        # 此处有Bug
        target_name_list[i] = t.lower()
    f = True
    for i in range(0, len(target_name_list)):
        to_invitation_ticket(self, skip_first_screenshot=True)
        target_name = target_name_list[i]
        self.logger.info("begin find student " + target_name)
        swipe_x = 630
        swipe_y = 580
        dy = 430
        stop_flag = False
        last_student_name = None
        while not stop_flag:
            region = {
                'CN': (489, 185, 865, 604),
                'Global': (489, 185, 865, 604),
                'JP': (489, 185, 865, 604),
            }
            img_shot = self.get_screenshot_array()
            out = self.ocr.get_region_raw_res(img_shot, region[self.server], model=self.server)
            detected_name = []
            location = []
            for k in range(0, len(out)):
                temp = out[k]['text']
                res = ""
                for x in range(0, len(temp)):
                    if temp[x] == '(' or temp[x] == "（" or temp[x] == ")" or temp[x] == "）" or temp[x] == ' ':
                        continue
                    else:
                        res = res + temp[x]
                res = res.lower()
                for j in range(0, len(student_name)):
                    if len(detected_name) <= 4:
                        if res == student_name[j]:
                            if student_name[j] == "干世":
                                detected_name.append("千世")
                            else:
                                detected_name.append(student_name[j])
                            location.append(out[i]['position'][0][1] + 210)
                    else:
                        break
            if len(detected_name) == 0:
                self.logger.info("No name detected")
                break
            st = ""
            for x in range(0, len(detected_name)):
                st = st + detected_name[x] + " "
            self.logger.info("detected name :" + st)
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
                    self.swipe(swipe_x, swipe_y, swipe_x, swipe_y - dy, duration=0.5)
                    self.click(617, 500, wait=False, wait_over=True)
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


def interaction_for_cafe_solve_method1(self):
    start_x = 640
    start_y = 360
    swipe_action_list = [[640, 640, 0, -640, -640, -640, -640, 0, 640, 640, 640],
                         [0, 0, -360, 0, 0, 0, 0, -360, 0, 0, 0]]

    for i in range(0, len(swipe_action_list[0]) + 1):
        stop_flag = False
        while not stop_flag:
            shot = self.get_screenshot_array()
            location = 0
            #  print(shot.shape)
            #  for i in range(0, 720):
            #      print(shot[i][664][:])
            for x in range(0, 1280):
                for y in range(0, 670):
                    if color.judge_rgb_range(shot, x, y, 255, 255, 210, 230, 0, 50) and \
                        color.judge_rgb_range(shot, x, y + 21, 255, 255, 210, 230, 0, 50) and \
                        color.judge_rgb_range(shot, x, y + 41, 255, 255, 210, 230, 0, 50):
                        location += 1
                        self.logger.info("find interaction at (" + str(x) + "," + str(y + 42) + ")")
                        self.click(min(1270, x + 40), y + 42)
                        for tmp1 in range(-40, 40):
                            for tmp2 in range(-40, 40):
                                if 0 <= x + tmp1 < 1280:
                                    shot[y + tmp2][x + tmp1] = [0, 0, 0]
                                else:
                                    break

            if location == 0:
                self.logger.info("no interaction swipe to next stage")
                stop_flag = True
            else:
                self.logger.info("totally find " + str(location) + " interaction available")
        if not self.common_icon_bug_detect_method("src/cafe/present.png", 274, 161, "cafe", times=5):
            return False
        if i != len(swipe_action_list[0]):
            self.swipe(start_x, start_y, start_x + swipe_action_list[0][i],
                       start_y + swipe_action_list[1][i], duration=0.1)

    self.logger.info("cafe task finished")
    self.main_activity[0][1] = 1
    self.operation("start_getting_screenshot_for_location")
    self.operation("click", (1240, 39))


def find_k_b_of_point1_and_point2(point1, point2):
    k = (point1[1] - point2[1]) / (point1[0] - point2[0])
    b = point1[1] - k * point1[0]
    return k, b


def interaction_for_cafe_solve_method2(self):
    self.operation("click", (547, 623))
    self.connection().pinch_in()
    self.operation("swipe", ((665, 675), (425, 300)), duration=0.1)
    k_and_b = [find_k_b_of_point1_and_point2((370, 254), (631, 198)),
               find_k_b_of_point1_and_point2((665, 677), (992, 570)),
               find_k_b_of_point1_and_point2((1186, 342), (791, 191)),
               find_k_b_of_point1_and_point2((164, 508), (299, 609))]
    print(k_and_b)
    points = []
    dx = 40
    dy = 40
    for i in range(-2, 18):
        x = i * dx
        y = x * k_and_b[3][0] + k_and_b[3][1]
        points.append([(x, y)])
        for j in range(1, 100):
            x_move = x + j * dy
            b_new = y - x * k_and_b[0][0]
            y_move = x_move * k_and_b[0][0] + b_new
            y1 = x_move * k_and_b[1][0] + k_and_b[1][1]
            y2 = x_move * k_and_b[2][0] + k_and_b[2][1]
            if y1 >= y_move >= y2:
                points[i + 2].append((x_move, y_move))
            else:
                break
    for i in range(0, len(points)):
        print(points[i])
        for j in range(0, len(points[i])):
            if points[i][j][0] <= 0:
                continue
            self.operation("click", (points[i][j][0], int(points[i][j][1])))
