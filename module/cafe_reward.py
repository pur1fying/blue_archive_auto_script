import threading
import time

import cv2
import numpy as np

from core import image, position, color

x = {
    'menu': (107, 9, 162, 36),
    '0.0': (1114, 642, 1155, 665),
    'students-arrived': (572, 240, 662, 269),
    'cafe-reward-status': (625, 135, 688, 171),
    'invitation-ticket': (421, 78, 451, 111),
}


def implement(self):
    to_cafe(self)
    if self.server == "CN":
        cn_implement(self)
    elif self.server == "Global":
        time.sleep(1)
        global_implement(self)
    return True

def to_cafe(self):
    if self.server == 'CN':
        possible = {
            'main_page_home-feature': (89, 653, 3),
            'cafe_cafe-reward-status': (905, 159, 3),
            'cafe_invitation-ticket': (835, 97, 3),
            'cafe_students-arrived': (922, 189, 3),
            'main_page_full-notice': (887, 165),

        }
        click_pos = [
            [1240, 577],
            [640, 154],
            [640, 360],
        ]
        los = [
            "gift",
            "reward_acquired",
            "relationship_rank_up"
        ]
        return image.detect(self, 'cafe_menu', possible, pre_func=color.detect_rgb_one_time,
                            pre_argv=(self, click_pos, los, ['cafe']))
    elif self.server == "Global":
        click_pos = \
            [
                [889, 162],
                [836, 97],
                [640, 360],
                [95, 699],
                [640, 458],
                [910, 138],
                [902, 156],
                [902, 156],
                [1240, 574],
                [628, 147],
            ]
        los = [
            "full_ap_notice",
            "invitation_ticket",
            "relationship_rank_up",
            "main_page",
            "guide",
            "insufficient_inventory_space",
            "cafe_earning_status_bright",
            "cafe_earning_status_grey",
            "gift",
            "reward_acquired"
        ]
        end = ["cafe"]
        color.common_rgb_detect_method(self, click_pos, los, end)


def cn_implement(self):
    op = np.full(2, False, dtype=bool)
    if not image.compare_image(self, 'cafe_0.0', 3):
        op[0] = True
    if self.ocrCN.ocr_for_single_line(image.screenshot_cut(self, (801, 586, 875, 606), self.latest_img_array))[
        'text'] == "可以使用":
        op[1] = True
    if op[0]:
        self.logger.info("Collect Cafe Earnings")
        collect(self)
        to_cafe(self)
    if not op[1]:
        self.logger.info("Invitation ticket unavailable")
    else:
        invite_girl(self)
    pat_style = self.config['patStyle']
    print(pat_style)
    if pat_style == '普通' or pat_style is None:
        interaction_for_cafe_solve_method3(self)
    elif pat_style == '地毯':
        interaction_for_cafe_solve_method3(self)
    elif pat_style == '拖动礼物':
        interaction_for_cafe_solve_method3(self)
    return True


def global_implement(self):
    self.latest_img_array = self.get_screenshot_array()
    op = np.full(2, False, dtype=bool)
    op[0] = get_invitation_ticket_status(self)
    op[1] = get_cafe_earning_status1(self)
    if op[1]:
        self.logger.info("Collect Cafe Earnings")
        collect(self)
        to_cafe(self)

    if not op[0]:
        self.logger.info("Invitation ticket unavailable")
    else:
        invite_girl(self)
    interaction_for_cafe_solve_method3(self)
    self.logger.info("cafe task finished")
    self.click(1240, 39)
    return True


def match(img, server):
    res = []
    for i in range(1, 5):
        template = cv2.imread("src/images/CN/cafe/happy_face" + str(i) + ".png")
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.75
        locations = np.where(result >= threshold)
        for pt in zip(*locations[::-1]):
            res.append([pt[0] + template.shape[1] / 2, pt[1] + template.shape[0] / 2 + 58])
    return res


def to_gift(self):
    click_pos = [
        [163, 639],
    ]
    los = ["cafe"]
    ends = ["gift"]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def shot(self):
    time.sleep(1)
    self.latest_img_array = self.get_screenshot_array()


def interaction_for_cafe_solve_method3(self):
    self.connection().pinch_in()
    self.swipe(709, 558, 709, 209, duration=0.5)
    for i in range(0, 4):
        to_gift(self)
        t1 = threading.Thread(target=shot, args=(self,))
        t1.start()
        self.swipe(131, 660, 1280, 660, duration=0.5)
        t1.join()
        res = match(self.latest_img_array, server=self.server)
        to_cafe(self)
        if res:
            print(res)
            res.sort(key=lambda x: x[0])
            temp = 0
            print(res)
            while temp < len(res):
                if temp == len(res) - 1:
                    break
                print(res[temp][0], res[temp + 1][0])
                print(res[temp][1], res[temp + 1][1])
                if abs(res[temp][0] - res[temp + 1][0]) <= 10 and abs(res[temp][1] - res[temp + 1][1]) <= 10:
                    res.pop(temp+1)
                else:
                    temp += 1
            self.logger.info("totally find " + str(len(res)) + " interactions")
            for j in range(0, len(res)):
                self.click(res[j][0], min(res[j][1], 591), wait=False)

        time.sleep(2)
        to_cafe(self)
        if i != 4:
            self.click(68, 636)
            time.sleep(1)
            self.click(1169, 90)
            time.sleep(1)


def to_invitation_ticket(self):
    if self.server == "CN":
        possible = {
            'cafe_cafe-reward-status': (905, 159, 3),
            'cafe_menu': (838, 647, 3),
        }
        end = 'cafe_invitation-ticket'
        return image.detect(self, end, possible)
    elif self.server == "Global":
        click_pos = [[836, 650]]
        los = ["cafe"]
        end = ["invitation_ticket"]
        color.common_rgb_detect_method(self, click_pos, los, end)


def invite_girl(self):
    student_name = None
    if self.server == "CN":
        student_name = ["瞬(小)", "桐乃", "纱绫(便服)", "日富美(泳装)", "真白(泳装)", "鹤城(泳装)",
                        "白子(骑行)" "梓(泳装)", "爱丽丝", "切里诺", "志美子", "日富美", "佳代子",
                        "明日奈", "菲娜", "艾米", "真纪",
                        "泉奈", "明里", "芹香", "优香", "小春",
                        "花江", "纯子", "千世", "干世", "莲见", "爱理", "睦月", "野宫", "绫音", "歌原",
                        "芹娜", "小玉", "铃美", "朱莉", "好美", "千夏", "琴里",
                        "春香", "真白", "鹤城", "爱露", "晴奈", "日奈", "伊织", "星野",
                        "白子", "柚子", "花凛", "妮露", "纱绫", "静子", "花子", "风香",
                        "和香", "茜", "泉", "梓", "绿", "堇", "瞬", "桃", "椿", "晴", "响"]
    elif self.server == "Global":
        student_name = ["Akane (Bunny)", "Ako", "Aris", "Aris (Maid)", "Aru", "Aru (New Year)",
                        "Asuna (Bunny)",
                        "Atsuko", "Azusa", "Azusa (Swimsuit)",
                        "Cherino", "Cherino (Hot Spring)", "Chihiro", "Chinatsu (Hot Spring)", "Chise (Swimsuit)",
                        "Eimi",
                        "Fuuka (New Year)", "Hanae (Christmas)", "Hanako (Swimsuit)", "Haruka (New Year)",
                        "Haruna", "Haruna (New Year)", "Haruna (Track)", "Hatsune Miku", "Hibiki",
                        "Hifumi", "Hifumi (Swimsuit)", "Himari", "Hina", "Hina (Swimsuit)", "Hinata",
                        "Hinata (Swimsuit)",
                        "Hiyori", "Hoshino", "Hoshino (Swimsuit)",
                        "Ichika", "Iori", "Iori (Swimsuit)", "Iroha", "Izumi", "Izuna", "Izuna (Swimsuit)",
                        "Kaede", "Kaho", "Kanna", "Karin", "Karin (Bunny)", "Kasumi", "Kayoko (New Year)",
                        "Kazusa",
                        "Koharu", "Kokona", "Kotori (Cheer Squad)", "Koyuki",
                        "Maki", "Mari (Track)", "Marina", "Mashiro", "Mashiro (Swimsuit)", "Megu", "Meru",
                        "Midori",
                        "Mika", "Mimori", "Mimori (Swimsuit)", "Mina", "Mine",
                        "Minori", "Misaka Mikoto", "Misaki", "Miyako", "Miyako (Swimsuit)", "Miyu", "Moe",
                        "Mutsuki (New Year)",
                        "Nagisa", "Natsu", "Neru", "Neru (Bunny Girl)", "Noa", "Nodoka (Hot Spring)",
                        "Nonomi (Swimsuit)",
                        "Reisa", "Rumi",
                        "Saki", "Saki (Swimsuit)", "Sakurako", "Saori", "Saya", "Saya (Casual)", "Sena",
                        "Serina (Christmas)",
                        "Shigure", "Shigure (Hot Spring)", "Shiroko",
                        "Shiroko (Cycling)", "Shiroko (Swimsuit)", "Shokuhou Misaki", "Shun", "Shun (Small)", "Sumire",
                        "Toki", "Toki (Bunny)", "Tsukuyo", "Tsurugi",
                        "Ui", "Ui (Swimsuit)", "Utaha (Cheer Squad)",
                        "Wakamo", "Wakamo (Swimsuit)", "Yuuka (Track)", "Yuzu",

                        "Airi", "Akane", "Akari", "Ayane",
                        "Chise", "Fuuka", "Hanae", "Hanako", "Hare", "Hasumi", "Junko", "Kayoko", "Kirino", "Mari",
                        "Momiji",
                        "Momoi", "Mutsuki", "Nonomi", "Serika",
                        "Shizuko", "Tsubaki", "Utaha", "Yuuka",

                        "Asuna", "Asuna (Bunny)",
                        "Ayane (Swimsuit)", "Chinatsu", "Fubuki", "Haruka", "Hasumi (Track)",
                        "Hibiki (Cheer Squad)",
                        "Izumi (Swimsuit)", "Junko (New Year)", "Juri",
                        "Koharu (Swimsuit)", "Kotama", "Kotori", "Michiru", "Miyu (Swimsuit)", "Nodoka", "Pina",
                        "Saten Ruiko",
                        "Serina", "Shimiko", "Shizuko (Swimsuit)", "Suzumi", "Tomoe",
                        "Tsurugi (Swimsuit)", "Yoshimi", "Yuzu (Maid)"]

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
    self.logger.info("inviting" + str(target_name_list))
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
        to_invitation_ticket(self)
        target_name = target_name_list[i]
        self.logger.info("begin find student " + target_name)
        swipe_x = 630
        swipe_y = 580
        dy = 430
        stop_flag = False
        last_student_name = None
        while not stop_flag:
            img_shot = self.get_screenshot_array()
            if self.server == 'CN':
                out = self.ocrCN.ocr(img_shot)
            elif self.server == 'Global':
                out = self.ocrEN.ocr(img_shot)
            detected_name = []
            location = []
            for i in range(0, len(out)):
                t = out[i]['text']
                res = ""
                for x in range(0, len(t)):
                    if t[x] == '(' or t[x] == "（" or t[x] == ")" or t[x] == "）" or t[x] == ' ':
                        continue
                    else:
                        res = res + t[x]
                res = res.lower()
                for j in range(0, len(student_name)):
                    if len(detected_name) <= 4:
                        if res == student_name[j]:
                            if student_name[j] == "干世":
                                detected_name.append("千世")
                            else:
                                detected_name.append(student_name[j])
                            location.append(out[i]['position'][0][1] + 25)
                    else:
                        break
            if len(detected_name) == 0:
                self.logger.info("No name detected")
                break
            st = ""
            for i in range(0, len(detected_name)):
                st = st + detected_name[i] + " "
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
                        self.click(784, location[s], wait=False)
                        time.sleep(0.7)
                        self.click(770, 500)
                        break
                if not stop_flag:
                    self.logger.info("didn't find target student swipe to next page")
                    self.swipe(swipe_x, swipe_y, swipe_x, swipe_y - dy, duration=0.5)
                    self.click(617, 500)
        to_cafe(self)
        if not f:
            break


def collect(self):
    if self.server == "CN":
        self.click(1150, 643)
        time.sleep(1)
        self.click(640, 522)
    elif self.server == "Global":
        click_pos = \
            [
                [1150, 643],
                [889, 162],
                [910, 138],
                [640, 522],
                [628, 147],
            ]
        los = ["cafe", "full_ap_notice", "insufficient_inventory_space", "cafe_earning_status_bright",
               "reward_acquired"]
        ends = ["insufficient_inventory_space", "cafe_earning_status_grey"]
        color.common_rgb_detect_method(self, click_pos, los, ends)


def get_invitation_ticket_status(self):
    img = self.latest_img_array[585:606, 731:870, :]
    t1 = time.time()
    ocr_res = self.ocrEN.ocr_for_single_line(img)
    t2 = time.time()
    self.logger.info("ocr_ticket:" + str(t2 - t1))
    temp = ""
    for j in range(0, len(ocr_res['text'])):
        if ocr_res['text'][j] == ' ':
            continue
        temp = temp + ocr_res['text'][j]
    temp = temp.lower()
    if temp == "availableforuse":
        print("Invite ticket available for use")
        self.logger.info("Invite ticket available for use")
        return True
    elif temp[2] == temp[5] == ':':
        self.logger.info("Invite ticket next available time : " + temp)
        return False
    else:
        self.logger.info("Invite ticket UNKNOWN STATUS")
        return False


def get_cafe_earning_status1(self):
    img = self.latest_img_array[643:675, 1093:1205, :]
    t1 = time.time()
    ocr_res = self.ocrEN.ocr_for_single_line(img)
    t2 = time.time()
    self.logger.info("ocr_cafe_earnings:" + str(t2 - t1))
    temp = ""
    for j in range(0, len(ocr_res['text'])):
        if ocr_res['text'][j] == ' ':
            continue
        temp = temp + ocr_res['text'][j]
    temp = temp.lower()
    if temp[len(temp) - 1] == "%":
        t = float(temp[:len(temp) - 1])
        self.logger.info("Cafe earnings : " + str(t) + "%")
        if t > 0:
            return True
    self.logger.info("Cafe earnings UNKNOWN STATUS")
    return False


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
