import time

from core import color, image
from core.utils import get_x_y, kmp,img_crop
from gui.util import log
from datetime import datetime


x = {
    'menu': (107, 9, 162, 36),
    'workshop': (418, 100, 436, 117),
    'view-all': (98, 103, 181, 122),
    'start-make2': (1054, 640, 1182, 669),
    'choose-node': (1054, 638, 1182, 669),
    'confirm-acc': (740, 466, 800, 493),
    'receive': (1102, 267, 1150, 290),
    'immediately': (1076, 267, 1124, 290),
    'start-make': (931, 303, 1015, 323)
}

def get_next_execute_tick():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    next_time = datetime(year, month, day+1, 4)
    return next_time.timestamp()

def common_create_judge(self):
    pri = ["花","Mo","桃桃","万圣节","情人节","果冻","色彩","灿烂","光芒","玲珑","白金","黄金","铜","白银","金属","隐然"]  # 可设置参数，越靠前的节点在制造时越优先选择
    node_x = [839, 508, 416, 302, 174]
    node_y = [277, 388, 471, 529, 555]
    # 572 278
    node = []
    lo = []
    for i in range(0, 5):
        self.operation("click", (node_x[i], node_y[i]))
        time.sleep(0.5 if i == 0 else 0.1)
        node_info = self.img_ocr(img_crop(self.operation("get_screenshot_array"),734,1123,207,277))
        for k in range(0, len(pri)):
            if kmp(pri[k], node_info) > 0:
                if k == 0:
                    log.d("choose node :" + pri[0], level=1, logger_box=self.loggerBox)
                    return i
                else:
                    node.append(pri[k])
                    lo.append(i)
    log.d("detected nodes:" + str(node), 1, logger_box=self.loggerBox)
    for i in range(1, len(pri)):
        for j in range(0, len(node)):
            if node[j][0:len(pri[i])] == pri[i]:
                log.d("choose node :" + pri[i], level=1, logger_box=self.loggerBox)
                return lo[j]


def implement(self):
    self.logger.info("reconstructing create task")
    return True
    to_crafting_chamber(self)
    if self.server == 'CN':
        start_make(self)
    elif self.server == "Global":
        global_implement(self)


def is_english_letter(char):
    return char.isalpha() and (char.isupper() or char.islower())


def node1_judge(self):
    node_x = [839, 508, 416, 302, 174]
    node_y = [277, 388, 471, 529, 555]
    node = []
    lo = []
    for i in range(0, 5):
        self.click(node_x[i], node_y[i], wait=False)
        time.sleep(0.7 if i == 0 else 0.2)
        img = self.get_screenshot_array()
        # cv2.imshow("img",img)
        # cv2.waitKey(0)
        node_info = self.ocrEN.ocr_for_single_line(img[204:273, 814:1233, :])["text"].lower()
        temp = ""
        for j in range(0, len(node_info)):
            if is_english_letter(node_info[j]):
                temp += node_info[j]
        node_info = temp
        for k in range(0, len(self.pri)):
            if self.pri[k] == node_info:
                if k == 0:
                    self.logger.info("choose node :" + self.pri[0])
                    return i
                else:
                    node.append(self.pri[k])
                    lo.append(i)
    self.logger.info("detected nodes:" + str(node))
    self.logger.info("detected position" + str(lo))
    for i in range(1, len(self.pri)):
        for j in range(0, len(node)):
            if node[j][0:len(self.pri[i])] == self.pri[i]:
                self.logger.info("choose node :" + self.pri[i])
                return lo[j]


def check_availability(img):
    if color.judge_rgb_range(img, 1112, 681, 210, 230, 210, 230, 210, 230) and \
            color.judge_rgb_range(img, 1105, 627, 210, 230, 210, 230, 210, 230):
        return "grey"
    elif color.judge_rgb_range(img, 1112, 681, 235, 255, 233, 253, 65, 85) and \
            color.judge_rgb_range(img, 1105, 627, 235, 255, 233, 253, 65, 85):
        return "bright"
    else:
        return "unknown"


def start_crafting(self):
    click_pos = [
        [1108, 654],
        [764, 501]
    ]
    los = [
        "start_crafting",
        "start_crafting_notice",
    ]
    ends = [
        "crafting_chamber_material_synthesis",
    ]
    color.common_rgb_detect_method(self, click_pos, los, ends)


def global_implement(self):
    self.pri = self.config['create_priority']
    for i in range(0, len(self.pri)):
        temp = ""
        for j in range(0, len(self.pri[i])):
            if is_english_letter(self.pri[i][j]):
                temp += self.pri[i][j]
        self.pri[i] = temp.lower()
    self.logger.info("create priority:" + str(self.pri))
    to_crafting_chamber(self)
    create_times = self.config['create_times']  # ** 制造次数 请确保有加速券
    cur_create_times = 0
    create_stop = False
    common_create_collect_operation(self)
    while not create_stop:
        lox = 1076
        loy = [273, 411, 548]
        collect = False
        tmp = min(create_times, 3)
        for i in range(0, tmp):
            cur_create_times += 1
            self.logger.info("start create,time: " + str(cur_create_times))
            to_node1(self, (lox, loy[i]))
            self.click(920, 206, wait=False)
            self.latest_img_array = self.get_screenshot_array()
            res1 = check_availability(self.latest_img_array)
            f = False
            if res1 == "grey":
                self.logger.info("material 2 INADEQUATE,try material 1")
                for x in range(0, 10):
                    self.click(755, 206, wait=False)
                self.latest_img_array = self.get_screenshot_array()
                res2 = check_availability(self.latest_img_array)
                if res2 == "grey":
                    self.logger.info("material 1 INADEQUATE,EXIT create task")
                elif res2 == "bright":
                    collect = True
                    f = True
            elif res1 == "bright":
                collect = True
                f = True
            if f:
                self.click(1123, 650, wait=False)
                time.sleep(3.5)
                node_x = [572, 508, 416, 302, 174]
                node_y = [278, 388, 471, 529, 555]
                choice = node1_judge(self)
                if choice is not None:
                    self.click(node_x[choice], node_y[choice], wait=False)
                    self.click(1117, 654, wait=False)
                    time.sleep(2)
                    start_crafting(self)
        create_times -= 3
        if create_times <= 0:
            create_stop = True
        if collect:
            to_crafting_chamber(self)
            common_create_collect_operation(self)
    return True


def is_make_page(self):
    ocr.screenshot_check_text(self, "制造工坊", (97, 7, 224, 38))


def to_node1(self, lo):
    """
    去第一节点
    """
    click_pos = [[lo[0], lo[1]]]
    los = ["crafting_chamber_material_synthesis"]
    end = ["node1"]
    color.common_rgb_detect_method(self, click_pos, los, end)


def start_make(self):
    for i in range(self.config):
        image.detect(self, 'make_view-all', cl=(975, 264))
        if not choose_tone(self):
            break
        image.detect(self, (('make_workshop', 30),), cl=(1114, 653))
        choose_item(self)
        self.click(1121, 650, False)
        image.detect(self, 'make_start-make2')
        image.detect(self, 'make_menu', cl=(1116, 652))
        make_immediately(self)


def use_acc(self):
    """
    使用加速券
    @param self:
    """
    # 点击使用加速 -> 弹出立即完成
    self.click(1128, 278, False)
    image.detect(self, 'make_confirm-acc')
    # 点击确认
    self.click(771, 478, False)


def receive_prize(self):
    """
    领取奖励
    @param self:
    """
    # 点击领取
    self.click(1122, 275)
    # 关闭奖励
    stage.close_prize_info(self)


def make_immediately(self):
    """
    立即加速
    @param self:
    @return:
    """
    if 'use_acc_ticket' in self.tc['config'] and not self.tc['config']['use_acc_ticket']:
        self.logger.error("当前配置为不使用加速券...")
    use_acc_ticket = self.tc['config']['use_acc_ticket']
    create_times = self.tc['config']['count']
    self.logger.info("use acc ticket : " + str(use_acc_ticket) + " total create times : " + str(create_times))
    common_create_collect_operation(self, use_acc_ticket)
    lox = 1147
    loy = [283, 423, 558]
    if not use_acc_ticket:
        cnt = 0
        crafting_list_status = check_crafting_list_status(self)
        for i in range(0, 3):
            if crafting_list_status[i] == "empty" and cnt < create_times:
                cnt += 1
                self.logger.info("start create time : " + str(cnt))
                to_node1(self, (lox, loy[i]))
                if not choose_tone(self):
                    return True
                # 点击第1阶段启动
                self.click(1114, 653, False)
                # 等待加载
                stage.wait_loading(self)
                # 等待制造页面加载
                is_make_page(self)
                # 选择物品
                choose_item(self)
                # 点击选择节点
                self.click(1121, 650)
                # 等待加载
                ocr.screenshot_check_text(self, '开始制造', (1049, 632, 1187, 670))
                # 点击开始制造
                self.click(1116, 652, False)
                to_crafting_chamber(self)
        return True
    if use_acc_ticket:
        for i in range(0, create_times):
            self.logger.info("start create time : " + str(i + 1))
            to_node1(self, (lox, loy[i % 3]))
            # 选择拱心石
            if not choose_tone(self):
                return True
            # 点击第1阶段启动
            self.click(1114, 653, False)
            # 等待加载
            stage.wait_loading(self)
            # 等待制造页面加载
            is_make_page(self)
            # 选择物品
            choose_item(self)
            # 点击选择节点
            self.click(1121, 650)
            # 等待加载
            ocr.screenshot_check_text(self, '开始制造', (1049, 632, 1187, 670))
            # 点击开始制造
            self.click(1116, 652, False)
            to_crafting_chamber(self)
            if (i + 1) % 3 == 0:
                common_create_collect_operation(self, use_acc_ticket)
        return True


def choose_item(self):
    time.sleep(3)
    self.click(445, 552, False)
    # 选择优先级最高物品
    check_index = get_high_priority(self)
    # 选择最高优先级物品
    self.click(*priority_position[check_index + 1])
    return check_index


def get_high_priority(self):
    # 遍历查看所有物品
    items = []
    for i, position in priority_position.items():
        self.click(*position, False)
        item = ocr.screenshot_get_text(self, (720, 204, 1134, 269))
        items.append(item)
    # 计算优先级最高的物品
    check_item = None
    check_index = 0
    for i, item in enumerate(items):
        for priority in self.tc['config']['priority']:
            ratio = fuzz.ratio(item, priority)
            if ratio < 80:
                continue
            if not check_item or \
                    self.tc['config']['priority'].index(priority) < self.tc['config']['priority'].index(check_item):
                check_item = priority
                check_index = i
    return check_index


def choose_tone(self):
    # 点击拱心石
    time.sleep(0.5)
    self.click(908, 199, False)
    time.sleep(0.1)
    # 检查是否满足
    self.latest_img_array = self.get_screenshot_array()
    if color.judge_rgb_range(self.latest_img_array, 1114, 678, 235, 255, 223, 243, 65, 85):
        return True

    # 点击拱心石碎片
    self.click(769, 200, False, 10)
    time.sleep(0.1)
    # 检查是否满足
    self.latest_img_array = self.get_screenshot_array()
    if color.judge_rgb_range(self.latest_img_array, 1114, 678, 235, 255, 223, 243, 65, 85):
        return True
    return False


def check_crafting_list_status(self):
    """
    返回当前制造列表状态
    """
    lox = 1127
    loy = [[252, 309], [396, 453], [535, 594]]
    res = []
    for i in range(0, len(loy)):
        if color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 100, 130, 205, 235, 235, 255) and \
                color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 100, 130, 205, 235, 235, 255):
            res.append("complete_instantly")
        elif color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 230, 255, 215, 255, 60, 90) and \
                color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 230, 255, 215, 255, 60, 90):
            res.append("receive")
        elif color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 215, 255, 215, 255, 215, 255) and \
                color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 215, 255, 215, 255, 215, 255):
            res.append("empty")
        else:
            res.append("unknown")
    self.logger.info("crafting list status: %s", res)
    return res


def common_create_collect_operation(self, use_acc_ticket=False):
    """
    根据是否使用加速券收集奖励
    """
    if self.server == "CN":
        res = check_crafting_list_status(self)
        lox = 1127
        loy_collect = [283, 422, 567]
        flag = True
        for i in range(0, len(res)):  # 当出现领取或立即完成且用加速券未完成
            if res[i] == "receive" or (res[i] == "complete_instantly" and use_acc_ticket):
                flag = False
                break
        if flag:
            self.logger.info("all crafting task completed")
            return True
        for i in range(0, len(res)):
            if res[i] == "receive":
                self.click(lox, loy_collect[i], wait=False)
                time.sleep(2)
                self.click(640, 100, wait=False)
                self.click(640, 100, wait=False)
                to_crafting_chamber(self)
            elif res[i] == "complete_instantly" and use_acc_ticket:
                self.click(lox, loy_collect[i], wait=False)
                time.sleep(0.5)
                self.click(772, 480, wait=False)
                time.sleep(0.5)
                self.click(lox, loy_collect[i])
                time.sleep(2)
                self.click(640, 100, wait=False)
                self.click(640, 100, wait=False)
                to_crafting_chamber(self)
        return common_create_collect_operation(self)
    elif self.server == "Global":
        lox = 1127
        loy = [[252, 309], [396, 453], [535, 594]]
        loy_collect = [283, 422, 567]
        res = []
        for i in range(0, len(loy)):
            if color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 100, 130, 205, 235, 235, 255) and \
                    color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 100, 130, 205, 235, 235, 255):
                res.append("complete_instantly")
            elif color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 230, 255, 215, 255, 60, 90) and \
                    color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 230, 255, 215, 255, 60, 90):
                res.append("receive")
            elif color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 215, 255, 215, 255, 215, 255) and \
                    color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 215, 255, 215, 255, 215, 255):
                res.append("empty")
            else:
                res.append("unknown")
        self.logger.info("crafting list status:" + str(res))
        while 1:
            for i in range(0, len(res)):
                if res[i] != "empty":
                    break
                if res[i] == "empty" and i == len(res) - 1:
                    self.logger.info("all crafting task completed")
                    return True
            for i in range(0, len(res)):
                if res[i] == "receive":
                    self.click(lox, loy_collect[i], wait=False)
                    time.sleep(2)
                    self.click(640, 100, wait=False)
                    self.click(640, 100, wait=False)
                    to_crafting_chamber(self)
                elif res[i] == "complete_instantly":
                    self.click(lox, loy_collect[i], wait=False)
                    time.sleep(0.5)
                    self.click(760, 515, wait=False)
                    time.sleep(0.5)
                    self.click(lox, loy_collect[i], wait=False)
                    time.sleep(2)
                    self.click(640, 100, wait=False)
                    self.click(640, 100, wait=False)
                    to_crafting_chamber(self)
            res = []
            for i in range(0, len(loy)):
                if color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 100, 130, 205, 235, 235, 255) and \
                        color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 100, 130, 205, 235, 235, 255):
                    res.append("complete_instantly")
                elif color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 230, 255, 215, 255, 60, 90) and \
                        color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 230, 255, 215, 255, 60, 90):
                    res.append("receive")
                elif color.judge_rgb_range(self.latest_img_array, lox, loy[i][0], 215, 255, 215, 255, 215, 255) and \
                        color.judge_rgb_range(self.latest_img_array, lox, loy[i][1], 215, 255, 215, 255, 215, 255):
                    res.append("empty")
                else:
                    res.append("unknown")
            self.logger.info("crafting list status:" + str(res))


def to_crafting_chamber(self):
    """
    前往制造列表
    """
    if self.server == "CN":
        click_pos = [
            [698, 654],
            [640, 108],
            [872, 165],
        ]
        los = [
            "main_page",
            "reward_acquired",
            "complete_instantly_notice",
        ]
        ends = [
            "crafting_chamber_material_synthesis",
        ]
    elif self.server == "Global":
        click_pos = [
            [680, 654],
            [100, 185],
            [640, 108],
            [872, 165],
        ]
        los = [
            "main_page",
            "crafting_chamber_material_fusion",
            "reward_acquired",
            "complete_instantly_notice"
        ]
        ends = [
            "crafting_chamber_material_synthesis",
        ]
    color.common_rgb_detect_method(self, click_pos, los, ends)
