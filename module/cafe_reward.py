import threading
import time

import cv2
import numpy as np

from core.utils import pd_rgb, get_x_y
from gui.util import log


def interaction_for_cafe_solve_method1(self):
    start_x = 640
    start_y = 360
    swipe_action_list = [[640, 640, 0, -640, -640, -640, -640, 0, 640, 640, 640],
                         [0, 0, -360, 0, 0, 0, 0, -360, 0, 0, 0]]

    for i in range(0, len(swipe_action_list[0]) + 1):
        stop_flag = False
        while not stop_flag:
            shot = self.operation("get_screenshot_array")
            location = 0
            #  print(shot.shape)
            #  for i in range(0, 720):
            #      print(shot[i][664][:])
            for x in range(0, 1280):
                for y in range(0, 670):
                    if pd_rgb(shot, x, y, 255, 255, 210, 230, 0, 50) and \
                            pd_rgb(shot, x, y + 21, 255, 255, 210, 230, 0, 50) and \
                            pd_rgb(shot, x, y + 41, 255, 255, 210, 230, 0, 50):
                        location += 1
                        log.d("find interaction at (" + str(x) + "," + str(y + 42) + ")", 1,
                              logger_box=self.loggerBox)
                        self.operation("click@student", (min(1270, x + 40), y + 42))
                        for tmp1 in range(-40, 40):
                            for tmp2 in range(-40, 40):
                                if 0 <= x + tmp1 < 1280:
                                    shot[y + tmp2][x + tmp1] = [0, 0, 0]
                                else:
                                    break

            if location == 0:
                log.d("no interaction swipe to next stage", 1, logger_box=self.loggerBox)
                stop_flag = True
            else:
                log.d("totally find " + str(location) + " interaction available", 1, logger_box=self.loggerBox)
        if not self.common_icon_bug_detect_method("src/cafe/present.png", 274, 161, "cafe", times=5):
            return False
        if i != len(swipe_action_list[0]):
            self.operation("swipe", [(start_x, start_y), (start_x + swipe_action_list[0][i],
                                                          start_y + swipe_action_list[1][i])], duration=0.1)

    log.d("cafe task finished", 1, logger_box=self.loggerBox)
    self.main_activity[0][1] = 1
    self.operation("start_getting_screenshot_for_location")
    self.operation("click", (1240, 39))


def find_k_b_of_point1_and_point2(point1, point2):
    k = (point1[1] - point2[1]) / (point1[0] - point2[0])
    b = point1[1] - k * point1[0]
    return k, b


def interaction_for_cafe_solve_method2(self):
    self.operation("click",(547,623))
    self.connection().pinch_in()
    self.operation("swipe",((665, 675), (425,300)),duration=0.1)
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
            self.operation("click",(points[i][j][0], int(points[i][j][1])))


def match(img):
    res = []
    path = "src/cafe/happy_face"
    for i in range(1, 5):
        img_path = path + str(i) + ".png"
        print(img_path)
        template = cv2.imread(img_path)
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)
        for pt in zip(*locations[::-1]):
            res.append([pt[0] + template.shape[1] / 2, pt[1] + template.shape[0] / 2 + 58])
    print(res)
    return res


def shot(self):
    time.sleep(1)
    self.latest_img_array = self.operation("get_screenshot_array")


def interaction_for_cafe_solve_method3(self):
    self.connection().pinch_in()
    self.operation("swipe", ((664, 594), (425, 250)), duration=0.1)
    for i in range(0, 5):
        self.operation("click", (167,646),duration=0.5)
        t1 = threading.Thread(target=shot, args=(self,))
        t1.start()
        self.operation("swipe", [(131, 660), (1280, 660)], duration=0.5)
        t1.join()
        res = match(self.latest_img_array)
        print(res)
        self.operation("click", (1238, 575),duration=0.5)

        for j in range(0, len(res)):
            self.operation("click", (res[j][0], min(res[j][1], 591)))

        for j in range(0, 5):
            self.latest_img_array = self.operation("get_screenshot_array")
            if not pd_rgb(self.latest_img_array, 169, 635, 245, 255, 245, 255, 245, 255):
                self.operation("click",(365, 249),duration=1)
        if i != 4:
            self.operation("click", (68, 636), duration=0.5)
            self.operation("click", (1169, 90), duration=0.5)


def implement(self):
    self.operation("stop_getting_screenshot_for_location")  # 停止截图

    path1 = "src/cafe/collect_button_bright.png"
    path2 = "src/cafe/collect_button_grey.png"
    return_data1 = get_x_y(self.latest_img_array, path1)
    return_data2 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    print(return_data2)
    if return_data1[1][0] <= 1e-03:
        log.d("collect reward", 1, logger_box=self.loggerBox)
        self.operation("click@collect", (return_data1[0][0], return_data1[0][1]), duration=2)
        self.operation("click@anywhere", (274, 161))
        self.operation("click@anywhere", (274, 161))
    elif return_data2[1][0] <= 1e-03:
        log.d("reward has been collected", 1, logger_box=self.loggerBox)
        self.operation("click@anywhere", (274, 161))
    else:
        log.d("can't detect collect reward button", 2, logger_box=self.loggerBox)

    if not self.common_icon_bug_detect_method("src/cafe/present.png", 274, 161, "cafe", times=7):
        return False

    img_shot = self.operation("get_screenshot_array")
    path = "src/cafe/invitation_ticket.png"
    return_data1 = get_x_y(img_shot, path)
    print(return_data1)

    target_name = self.config.get('favorStudent')  # ** 可设置参数 邀请券邀请学生的名字
    if return_data1[1][0] <= 1e-03:
        target_name_list = [self.config.get('favorStudent')]  # ** 可设置参数 邀请券邀请学生的名字 优先邀请前面的，前面没有选择后面
        for i in range(0, len(target_name_list)):
            t = ""
            for j in range(0, len(target_name_list[i])):
                if target_name_list[i][j] == '(' or target_name_list[i][j] == "（" or target_name_list[i][j] == ")" or \
                        target_name_list[i][j] == "）":
                    continue
                else:
                    t = t + target_name_list[i][j]
            target_name_list[i] = t
        f = True
        for i in range(0, len(target_name_list)):
            if not f:
                break
            target_name = target_name_list[i]
            self.operation("click@invitation ticket", (return_data1[0][0], return_data1[0][1]), duration=1)
            log.d("begin find student " + target_name, 1, logger_box=self.loggerBox)
            swipe_x = 630
            swipe_y = 580
            dy = 430

            student_name = ["日富美(泳装)", "真白(泳装)", "鹤城(泳装)","白子(骑行)" "梓(泳装)", "爱丽丝", "切里诺", "志美子", "日富美", "佳代子",
                            "明日奈", "菲娜", "艾米", "真纪",
                            "泉奈", "明里", "芹香", "优香", "小春",
                            "花江", "纯子", "千世", "干世", "莲见", "爱理", "睦月", "野宫", "绫音", "歌原",
                            "芹娜", "小玉", "铃美", "朱莉", "好美", "千夏", "琴里",
                            "春香", "真白", "鹤城", "爱露", "晴奈", "日奈", "伊织", "星野",
                            "白子", "柚子", "花凛", "妮露", "纱绫", "静子", "花子", "风香",
                            "和香", "茜", "泉", "梓", "绿", "堇", "瞬", "桃", "椿", "晴", "响"]
            for i in range(0, len(student_name)):
                t = ""
                for j in range(0, len(student_name[i])):
                    if student_name[i][j] == '(' or student_name[i][j] == "（" or student_name[i][j] == ")" or student_name[i][j] == "）":
                        continue
                    else:
                        t = t + student_name[i][j]
                student_name[i] = t
            stop_flag = False
            last_student_name = None

            while not stop_flag:
                img_shot = self.operation("get_screenshot_array")
                #   cv2.imshow("image", img_shot)
                #  cv2.waitKey(0)
                # print(img_shot.shape)
                out = self.ocr.ocr(img_shot)
                print(out)
                name_st = []
                print(name_st)
                detected_name = []
                location = []
                for i in range(0, len(out)):
                    for j in range(0, len(student_name)):
                        if len(detected_name) <= 4:
                            t = out[i]['text']
                            res = ""
                            for x in range(0, len(t)):
                                if t[x] == '(' or t[x] == "（" or t[x] == ")" or t[x] == "）":
                                    continue
                                else:
                                    res = res + t[x]
                            if res == student_name[j]:
                                if student_name[j] == "干世":
                                    detected_name.append("千世")
                                else:
                                    detected_name.append(student_name[j])
                                location.append(out[i]['position'][0][1] + 25)

                        else:
                            break

                if len(detected_name) == 0:
                    log.d("No name detected", 2, logger_box=self.loggerBox)
                    break

                st = ""
                for i in range(0, len(detected_name)):
                    st = st + detected_name[i] + " "
                log.d("detected name :" + st, 1, logger_box=self.loggerBox)

                if detected_name[len(detected_name) - 1] == last_student_name:
                    log.d("Can't detect target student", 2, logger_box=self.loggerBox)
                    self.operation("click", (271, 281), duration=0.2)
                    stop_flag = True
                else:
                    last_student_name = detected_name[len(detected_name) - 1]
                    for s in range(0, len(detected_name)):
                        if detected_name[s] == target_name:
                            log.d("find student " + target_name + " at " + str(location[s]), level=1,
                                  logger_box=self.loggerBox)
                            stop_flag = True
                            f = False
                            self.operation("click", (784, location[s]), duration=0.7)
                            self.operation("click@confirm", (770, 500))
                            if not self.common_icon_bug_detect_method("src/cafe/present.png", 274, 161, "cafe",
                                                                      times=5):
                                return False

                    if not stop_flag:
                        log.d("didn't find target student swipe to next page", 1, logger_box=self.loggerBox)
                        self.operation("swipe", [(swipe_x, swipe_y), (swipe_x, swipe_y - dy)], duration=0.5)
                        self.operation("click", (617, 500))

    else:
        log.d("invitation ticket used", 1, logger_box=self.loggerBox)

    # interaction_for_cafe_solve_method1(self)
    # interaction_for_cafe_solve_method2(self)
    interaction_for_cafe_solve_method3(self)
    return True
