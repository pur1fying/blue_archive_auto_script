import time

from core.utils import pd_rgb, get_x_y
from gui.util import log


def implement(self):
    self.operation("stop_getting_screenshot_for_location")  #  停止截图

    path1 = "src/cafe/collect_button_bright.png"
    path2 = "src/cafe/collect_button_grey.png"
    return_data1 = get_x_y(self.latest_img_array, path1)
    return_data2 = get_x_y(self.latest_img_array, path2)
    print(return_data1)
    print(return_data2)
    if return_data1[1][0] <= 1e-03:
        log.d("collect reward", 1, logger_box=self.loggerBox)
        self.operation("click@collect", (return_data1[0][0], return_data1[0][1]),duration=2)
        self.operation("click@anywhere", (274, 161))
        self.operation("click@anywhere", (274, 161))
    elif return_data2[1][0] <= 1e-03:
        log.d("reward has been collected", 1, logger_box=self.loggerBox)
        self.operation("click@anywhere", (274, 161))
    else:
        log.d("can't detect collect reward button", 2, logger_box=self.loggerBox)

    if not self.common_icon_bug_detect_method("src/cafe/present.png", 274, 161,"cafe", times=4):
        return False

    img_shot = self.operation("get_screenshot_array")
    path = "src/cafe/invitation_ticket.png"
    return_data1 = get_x_y(img_shot, path)
    print(return_data1)

    if return_data1[1][0] <= 1e-03:
        target_name_list = ["梓（泳装）", "爱丽丝", "纯子", "瞬"]  # ** 可设置参数 邀请券邀请学生的名字 优先邀请前面的，前面没有选择后面
        f = True
        for i in range(0, len(target_name_list)):
            if not f:
                break
            target_name = target_name_list[i]
            self.operation("click@invitation ticket", (return_data1[0][0], return_data1[0][1]),duration=1)
            log.d("begin find student " + target_name, 1, logger_box=self.loggerBox)
            swipe_x = 630
            swipe_y = 580
            dy = 430

            student_name = ["真白（泳装）", "鹤城（泳装)", "梓（泳装）", "爱丽丝", "切里诺", "志美子", "日富美", "佳代子", "明日奈", "菲娜", "艾米", "真纪",
                            "泉奈", "明里", "芹香", "优香", "小春",
                            "花江", "纯子", "千世", "干世", "莲见", "爱理", "睦月", "野宫", "绫音", "歌原",
                            "芹娜", "小玉", "铃美", "朱莉", "好美", "千夏", "琴里",
                            "春香", "真白", "鹤城", "爱露", "晴奈", "日奈", "伊织", "星野",
                            "白子", "柚子", "花凛", "妮露", "纱绫", "静子", "花子", "风香",
                            "和香", "茜", "泉", "梓", "绿", "堇", "瞬", "桃", "椿", "晴", "响"]

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
                            if out[i]['text'] == student_name[j]:
                                if student_name[j] == "干世":
                                    detected_name.append("千世")
                                else:
                                    detected_name.append(student_name[j])
                                location.append(out[i]['position'][0][1] + 25)

                        else:
                            break



                print(detected_name)
                print(location)
                if len(detected_name) == 0:
                    log.d("No name detected", 2, logger_box=self.loggerBox)
                    break

                st = ""
                for i in range(0, len(detected_name)):
                    st = st + detected_name[i] + " "
                log.d("detected name :" + st, 1, logger_box=self.loggerBox)

                if detected_name[len(detected_name) - 1] == last_student_name:
                    log.d("Can't detect target student", 2, logger_box=self.loggerBox)
                    self.operation("click", (271, 281),duration=0.2)
                    stop_flag = True
                else:
                    last_student_name = detected_name[len(detected_name) - 1]
                    for s in range(0, len(detected_name)):
                        if detected_name[s] == target_name:
                            log.d("find student " + target_name + " at " + str(location[s]), level=1, logger_box=self.loggerBox)
                            stop_flag = True
                            f = False
                            self.operation("click", (784, location[s]),duration=0.7)
                            self.operation("click@confirm", (770, 500))
                            if not self.common_icon_bug_detect_method("src/cafe/present.png", 274, 161, "cafe", times=5):
                                return False

                    if not stop_flag:
                        log.d("didn't find target student swipe to next page", 1, logger_box=self.loggerBox)
                        self.operation("swipe", [(swipe_x, swipe_y), (swipe_x, swipe_y - dy)], duration=0.5)
                        self.operation("click", (617, 500))





    else:
        log.d("invitation ticket used", 1, logger_box=self.loggerBox)

    start_x = 640
    start_y = 360
    swipe_action_list = [[640, 640, 0, -640, -640, -640, -640, 0, 640, 640, 640],
                         [0, 0, -360, 0, 0, 0, 0, -360, 0, 0, 0]]

    for i in range(0, len(swipe_action_list[0])+1):
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
                        self.operation("click@student", (min(1270, x+40), y+42))
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
    return True
