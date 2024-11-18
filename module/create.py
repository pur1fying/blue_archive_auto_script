import re
from core import color, image, picture


def implement(self):
    use_acceleration_ticket = self.config['use_acceleration_ticket']
    left_create_times = self.config['createTime'] - self.config['alreadyCreateTime']
    create_max_phase = self.config['create_phase']
    self.logger.info("Left Create Times: [ " + str(left_create_times) + " ].")
    self.logger.info("Use Acceleration Ticket : [ " + str(use_acceleration_ticket).upper() + " ].")
    self.logger.info("Create Phase : [ " + str(create_max_phase) + " ].")
    self.quick_method_to_main_page()
    res = to_manufacture_store(self, True)

    if res.startswith("create_phase"):
        phase = int(re.findall(r"\d", res)[0])
        start_phase(self, phase)
        select_node(self, phase)
        confirm_select_node(self, 1)
        to_manufacture_store(self, True)
    status = receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket)

    create_flag = True
    while self.flag_run and left_create_times > 0 and create_flag:
        if status == ["unfinished", "unfinished", "unfinished"] and (not use_acceleration_ticket):
            self.logger.info("-- Stop Crafting --")
            break
        need_acc_collect = False
        for i in range(0, len(status)):
            if status[i] == "empty":
                to_node1(self, i, True)
                create_phase(self, 1)
                if create_max_phase >= 2:
                    confirm_select_node(self, 0)
                    create_phase(self, 2)
                    if create_max_phase >= 3:
                        confirm_select_node(self, 0)
                        create_phase(self, 3)
                confirm_select_node(self, 1)
                need_acc_collect = True
                self.config_set.config['alreadyCreateTime'] += 1
                self.config_set.save()
                self.logger.info("Today Total Create Times : [ " + str(self.config['alreadyCreateTime']) + " ].")
                to_manufacture_store(self)
                if self.config['alreadyCreateTime'] >= self.config['createTime']:
                    create_flag = False
                    need_acc_collect = False
                    break
        if need_acc_collect:
            status = receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket)
    get_next_execute_time(self, status)
    return True


def confirm_select_node(self, tp=0):
    p = [(854, 654), (1116, 648)]
    p = p[tp]
    img_possibles = {
        "create_select-node": (1116, 648),
        "create_start-crafting": p,
        "create_start-crafting-notice": (769, 501)
    }
    img_ends = [
        "create_material-list",
        "create_crafting-list"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def start_phase(self, phase_num):
    self.logger.info("Start Phase [ " + str(phase_num) + " ].")
    node_position = [0, (841, 279), (383, 204), (769, 284)]
    img_ends = [
        "create_start-phase-" + str(phase_num) + "-grey",
        "create_select-node"
    ]
    img_possibles = {
        "create_start-phase-" + str(phase_num) + "-bright": (1104, 657),
        "create_phase-" + str(phase_num) + "-wait-to-check-node": node_position[phase_num],
    }
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def select_node(self, phase):
    pri = self.config['createPriority_phase' + str(phase)]
    for i in range(0, len(pri)):
        pri[i] = preprocess_node_info(pri[i], self.server)

    node_x = [[], [573, 508, 416, 302, 174], [122, 232, 323, 378, 401], [549, 422, 312, 223, 156]]
    node_y = [[], [277, 388, 471, 529, 555], [202, 270, 361, 472, 598], [282, 305, 362, 446, 559]]
    node_x = node_x[phase]
    node_y = node_y[phase]
    node = []
    lo = []
    region = (815, 201, 1223, 275)
    for i in range(0, 5):
        if i != 0:
            image.click_until_image_disappear(self, node_x[i], node_y[i], region, 0.9, 10)
        node_info = preprocess_node_info(
            self.ocr.get_region_res(self.latest_img_array, region, self.server, self.ratio), self.server)
        for k in range(0, len(pri)):
            if pri[k] == node_info:
                if k == 0:
                    self.logger.info("choose node : " + pri[0])
                    return
                else:
                    node.append(pri[k])
                    lo.append(i)
    self.logger.info("Detected Nodes:" + str(node))
    for i in range(1, len(pri)):
        for j in range(0, len(node)):
            if node[j][0:len(pri[i])] == pri[i]:
                self.logger.info("Choose Node : " + pri[i])
                if lo[j] != 4:
                    image.click_until_image_disappear(self, node_x[lo[j]], node_y[lo[j]], region, 0.9, 10)
                    return


def get_display_setting(self, phase):
    if phase == 1:
        return [1, 1, 1, 1, 1, 1, 1, 1], "basic", "up"
    if phase == 2:
        return [0, 0, 0, 0, 0, 0, 1, 0], "count", "down"
    if phase == 3:
        return [0, 0, 0, 0, 0, 0, 1, 0], "count", "down"


def create_phase(self, phase):
    self.logger.info("Create Phase [ " + str(phase) + " ].")
    filter_list, sort_type, sort_direction = get_display_setting(self, phase)
    set_display_setting(self, filter_list, sort_type, sort_direction)
    expected_item_list = item_order_list_builder(self, phase, filter_list, sort_type, sort_direction)
    # select item according to the config
    check_state = CreateItemCheckState(expected_item_list, sort_type, sort_direction, phase, self)
    while self.flag_run:
        check_state.clear_exist_item()
        item_recognize(self, check_state)
        if check_state.try_choose_item():
            break
        if check_state.item_all_checked():
            break
        check_state.list_swipe()
    log_detect_information(self, check_state.exist_item_list, "All Detected Items : ")
    start_phase(self, phase)
    select_node(self, phase)


def select_item(self, check_state, item_name, weight):
    item_weight = self.static_config['create_material_information'][item_name]["weight"]
    count = weight // item_weight
    self.logger.info("Select : [ " + item_name + " ] " + "Weight : " + str(item_weight))
    holding_quantity = check_state.item_quantity(item_name)
    if count > holding_quantity:
        self.logger.info("Item : [ " + item_name + " " + str(holding_quantity) + " ] not enough to craft.")
        return False
    p = check_state.now_exist_item_info[item_name]["detected_position"]
    region = get_item_selected_quantity_region(p[0], p[1])
    curr_selected = 0
    add_click_x = p[0] + 53
    add_click_y = p[1] - 52
    minus_click_x = p[0] + 103
    minus_click_y = p[1] - 84
    while curr_selected != count:
        diff = abs(curr_selected - count)
        if curr_selected < count:
            self.click(add_click_x, add_click_y, count=diff, duration=0.1, wait_over=True)
        else:
            self.click(minus_click_x, minus_click_y, count=diff, duration=0.1, wait_over=True)
        self.update_screenshot_array()
        curr_selected = get_item_selected_quantity(self, region)
    return True


def to_manufacture_store(self, skip_first_screenshot=False):
    crafting_x = {
        'CN': 680,
        'Global': 680,
        'JP': 642,
    }
    rgb_possibles = {
        "main_page": (crafting_x[self.server], 650),
        'reward_acquired': (640, 100),
    }
    img_ends = [
        "create_crafting-list",
        "create_phase-1-wait-to-check-node"
        "create_phase-2-wait-to-check-node",
        "create_phase-3-wait-to-check-node",
    ]
    img_possibles = {
        "create_start-crafting": (1115, 657),
        "create_start-crafting-notice": (769, 501),
        "create_select-node": (1115, 657),
    }
    return picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def check_crafting_list_status(self):
    y_position = {
        'CN': [312, 452, 594],
        'Global': [288, 407, 534],
        'JP': [288, 407, 534]
    }
    y_position = y_position[self.server]
    status = [None, None, None]
    for j in range(0, 3):
        if color.judge_rgb_range(self, 1126, y_position[j], 90, 130, 200, 230, 245, 255):
            status[j] = "unfinished"
        elif color.judge_rgb_range(self, 1126, y_position[j], 235, 255, 222, 255, 53, 93):
            status[j] = "finished"
        elif color.judge_rgb_range(self, 1126, y_position[j], 222, 255, 222, 255, 222, 255):
            status[j] = "empty"
    return status


def receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket):
    while self.flag_run:
        status = check_crafting_list_status(self)
        self.logger.info("crafting list status: " + str(status))
        if ("unfinished" in status and use_acceleration_ticket) or "finished" in status:
            collect(self, status, use_acceleration_ticket)
        else:
            return status
        self.latest_img_array = self.get_screenshot_array()


def collect(self, status, use_acceleration_ticket):
    if self.server == 'JP' or self.server == 'Global':
        if "finished" in status:
            self.click(1126, 617, wait_over=True, duration=1.5)
            self.click(640, 100, wait_over=True, count=2)
            to_manufacture_store(self)
        if ("unfinished" in status) and use_acceleration_ticket:
            img_possibles = {"create_crafting-list": (1126, 617)}
            img_ends = "create_complete-instantly"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            img_possibles = {"create_complete-instantly": (766, 516)}
            img_ends = "create_crafting-list"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
        return
    y_position = {
        'CN': [312, 452, 594],
    }
    y_position = y_position[self.server]
    for i in range(0, 3):
        if status[i] == "unfinished" and use_acceleration_ticket:
            img_possibles = {"create_crafting-list": (1126, y_position[i])}
            img_ends = "create_complete-instantly"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            img_possibles = {"create_complete-instantly": (766, 516)}
            img_ends = "create_crafting-list"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
            status[i] = "finished"
        if status[i] == "finished":
            self.click(1126, y_position[i], wait_over=True, duration=1.5)
            self.click(640, 100, wait_over=True, count=2)
            to_manufacture_store(self)


def check_create_availability(self):
    if color.judge_rgb_range(self, 1112, 681, 210, 230, 210, 230, 210, 230):
        return "grey"
    elif color.judge_rgb_range(self, 1112, 681, 235, 255, 233, 253, 65, 85):
        return "bright"
    else:
        return "unknown"


def to_node1(self, i, skip_first_screenshot=False):
    y_position = {
        'CN': [312, 452, 594],
        'Global': [288, 407, 534],
        'JP': [288, 407, 534]
    }
    y_position = y_position[self.server]
    img_possibles = {"create_crafting-list": (1153, y_position[i])}
    img_ends = "create_unlock-no1-grey"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_filter_menu(self):
    x = {
        'CN': 946,
        'Global': 1048,
        'JP': 1048
    }
    x = x[self.server]
    img_possibles = {
        "create_material-list": (x, 98),
        "create_sort-menu": (145, 160)
    }
    img_ends = "create_filter-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def confirm_filter(self):
    y = {
        'CN': 493,
        'Global': 595,
        'JP': 595
    }
    y = y[self.server]
    img_possibles = {"create_filter-menu": (765, y)}
    img_ends = "create_material-list"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def set_display_setting(self, filter_list=None, sort_type=None, sort_direction=None):
    if filter_list is not None:
        set_display_setting_filter_list(self, filter_list)
    if sort_type is not None:
        set_display_setting_sort_type(self, sort_type)
    if sort_direction is not None:
        set_display_setting_sort_arrow_direction(self, sort_direction)


def set_display_setting_filter_list(self, filter_list):
    to_filter_menu(self)
    self.logger.info("Set Filter List: ")
    self.logger.info(filter_list[0:4])
    self.logger.info(filter_list[4:8])
    total = sum(filter_list)

    flg = False
    if self.server == 'CN':
        flg = total > 4
        set_display_setting_filter_list_select_all(self, True)
        if flg:
            pass  # select all
        else:
            set_display_setting_filter_list_select_all(self, False)  # unselect all

        if total == 0 or total == 8:
            confirm_filter(self)
            return
    filter_list_ensure_choose(self, filter_list, flg)
    confirm_filter(self)


def filter_list_ensure_choose(self, filter_list, flg):
    filter_type_list = self.static_config['create_filter_type_list']
    start_position = {
        'CN': (263, 293),
        'Global': (291, 294),
        'JP': (291, 294)
    }
    dx = {
        'CN': 202,
        'Global': 235,
        'JP': 235
    }
    dy = {
        'CN': 72,
        'Global': 65,
        'JP': 65
    }
    start_position = start_position[self.server]
    dx = dx[self.server]
    dy = dy[self.server]
    curr_position = start_position
    for i in range(0, len(filter_list)):
        pre = "create_filter-" + filter_type_list[i] + "-"
        if filter_list[i] == 1:
            if self.server == 'CN' and flg:
                self.logger.info("[ " + filter_type_list[i] + " ] is already chosen.")
                continue
            img_possibles = {
                pre + "not-chosen": curr_position,
                pre + "reset": curr_position
            }
            img_ends = pre + "chosen"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
        else:
            if self.server == 'CN' and not flg:
                self.logger.info("[ " + filter_type_list[i] + " ] is already not chosen.")
                continue
            img_possibles = {
                pre + "chosen": curr_position,
            }
            img_ends = [pre + "not-chosen", pre + "reset"]
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
        if i == 3:
            curr_position = (start_position[0], start_position[1] + dy)
        else:
            curr_position = (curr_position[0] + dx, curr_position[1])


def set_display_setting_filter_list_select_all(self, state):
    if self.server == "CN":
        if state:
            img_possibles = {"create_filter-select-all-not-chosen": (964, 232)}
            img_ends = "create_filter-select-all-chosen"
        else:
            img_possibles = {"create_filter-select-all-chosen": (964, 232)}
            img_ends = "create_filter-select-all-not-chosen"
        picture.co_detect(self, None, None, img_ends, img_possibles, True)


def set_display_setting_sort_type(self, sort_type):
    self.logger.info("Set Sort Type: " + sort_type)
    to_sort_menu(self)
    set_sort_type(self, sort_type)
    confirm_sort(self)


def to_sort_menu(self):
    img_possibles = {
        "create_material-list": (1098, 98),
        "create_filter-menu": (145, 210)
    }
    img_ends = "create_sort-menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def confirm_sort(self):
    img_possibles = {"create_sort-menu": (767, 576)}
    img_ends = "create_material-list"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def set_sort_type(self, sort_type):
    sort_type_position = {
        'CN': {
            'basic': (195, 168),
            'count': (424, 168),
        },
        'Global': {
            'basic': (294, 181),
            'count': (529, 180),
            'name': (772, 175)
        },
        'JP': {
            'basic': (294, 181),
            'count': (529, 180),
            'name': (772, 175)
        }
    }
    p = sort_type_position[self.server][sort_type]
    img_ends = "create_sort-" + sort_type + "-chosen"
    img_possibles = {"create_sort-" + sort_type + "-not-chosen": p}
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def set_display_setting_sort_arrow_direction(self, direction):
    opposite = {
        "up": "down",
        "down": "up"
    }
    img_possibles = {
        "create_point-" + opposite[direction]: (1213, 104)
    }
    img_ends = "create_point-" + direction
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def preprocess_node_info(st, server):
    st = st.replace(" ", "")
    st = st.replace("・", "")
    st = st.replace(".", "")
    st = st.replace("’", "")
    if server == 'Global':
        st = st.lower()
    return st


def get_next_execute_time(self, status):
    regions = {
        'CN': [(686, 278, 883, 327), (686, 419, 883, 469), (686, 561, 883, 614)],
        'Global': [(686, 278, 883, 327), (686, 419, 883, 469), (686, 561, 883, 614)],
        'JP': [(686, 252, 883, 302), (686, 374, 883, 422), (686, 498, 883, 547)]
    }
    regions = regions[self.server]
    time_deltas = []
    for i in range(0, 3):
        if status[i] == "unfinished":
            res = self.ocr.get_region_res(self.latest_img_array, regions[i], 'Global', self.ratio)
            if res.count(":") != 2:
                continue
            res = res.split(":")
            for j in range(0, len(res)):
                if res[j][0] == "0":
                    res[j] = res[j][1:]
            self.logger.info(
                "ITEM " + str(i + 1) + " Crafting time: " + res[0] + "\tHOUR " + res[1] + "\tMINUTES " + res[
                    2] + "\tSECONDS")
            time_deltas.append(int(res[0]) * 3600 + int(res[1]) * 60 + int(res[2]))
    if time_deltas:
        self.next_time = min(time_deltas)


def item_order_list_builder(self, phase, filter_list, sort_type, sort_direction):
    self.logger.info("Build Item Order List.")
    self.logger.info("Phase : " + str(phase))
    self.logger.info("Filter List : ")
    self.logger.info(filter_list[0:4])
    self.logger.info(filter_list[4:8])
    self.logger.info("Sort Type : " + sort_type)
    self.logger.info("Sort Direction : " + sort_direction)
    result = []
    filter_type_list = self.static_config['create_filter_type_list']
    if filter_list[6] and not (self.server == 'CN' and phase == 3):
        # when material is chosen key stone will be displayed at the top
        # CN server phase 3 key stone is not allowed to be chosen
        temp = self.static_config['create_item_order'][self.server]["basic"]["Special"]
        if sort_type == "count":
            t = []
            for itm in temp:
                t.append([itm, self.config_set.config["create_item_holding_quantity"][itm]])
            t.sort(key=lambda x: x[1])
            temp = [x[0] for x in t]

        if sort_direction == "down":
            temp = temp[::-1]
        result.extend(temp)
    if phase == 1:
        return result

    temp = []
    item_info = self.static_config['create_material_information']
    phase_id = "phase" + str(phase)
    for i in range(0, len(filter_list)):
        if filter_list[i]:
            for itm in self.static_config['create_item_order'][self.server]["basic"][filter_type_list[i]]:
                if item_info[itm]["availability"][phase_id]:
                    temp.append(itm)

    if sort_type == "count":
        t = []
        for itm in temp:
            t.append([itm, self.config_set.config["create_item_holding_quantity"][itm]])
        t.sort(key=lambda x: x[1])
        temp = [x[0] for x in t]
    if sort_direction == "down":
        temp = temp[::-1]

    result.extend(temp)
    return result


class CreateItemCheckState:
    # During a full phase of item creation. This class is used for information transfer and store checked item state
    possible_x = [710, 851, 992, 1133]

    def __init__(self, check_item_order=None, sort_type="basic", sort_direction="up", phase=1, baas=None):
        self.phase = phase
        self.baas = baas
        self.weight_sum = self.baas.static_config["create_each_phase_weight"][phase]
        self.select_item_rule = self.baas.config["create_phase_" + str(phase) + "_select_item_rule"]
        self.already_selected_item = dict()
        self.check_item_order = check_item_order
        self.last_check_y = 0
        self.last_checked_idx = 0  # check item from order list
        self.now_exist_item_info = {}
        self.not_exist_item_list = []
        self.exist_item_list = []
        self.current_item_state = []
        self.sort_type = sort_type
        self.sort_direction = sort_direction
        # every item :
        # {
        #     "detected_position": (x, y),
        #     "holding_quantity": None,
        #     "selected_quantity": None,
        #     "usability": None,
        # }
        self.current_recorded_y_list = []  # (y, num) means line y has num items
        self.swipe_no_change_cnt = 0
        self.select_item_func_list = {
            "default": [0, self.phase1_default_select_item, self.phase2_default_select_item,
                        self.phase3_default_select_item],
        }

    def next_possible_item_name(self):
        if len(self.check_item_order) > self.last_checked_idx:
            name = self.check_item_order[self.last_checked_idx]
            self.last_checked_idx += 1
            return name
        return None

    def pop_checked_item(self, info):
        self.exist_item_list.append(self.check_item_order[self.last_checked_idx - 1])
        self.now_exist_item_info[self.check_item_order[self.last_checked_idx - 1]] = info.copy()
        ret = []
        if self.sort_type == "basic":
            ret = self.check_item_order[0:self.last_checked_idx - 1]  # item before last checked item quantity is 0
            self.check_item_order = self.check_item_order[self.last_checked_idx:]
            self.not_exist_item_list.extend(ret)
        elif self.sort_type == "count":
            print("pop" + self.check_item_order[self.last_checked_idx - 1])
            del self.check_item_order[self.last_checked_idx - 1]
        self.last_checked_idx = 0
        return ret

    def sort_check_item_order(self, create_item_holding_quantity):
        temp1 = []
        temp2 = []
        if "Keystone" in self.check_item_order:
            temp2.append(["Keystone", create_item_holding_quantity["Keystone"]])
        if "Keystone-Purple" in self.check_item_order:
            temp2.append(["Keystone-Purple", create_item_holding_quantity["Keystone-Purple"]])
        # Keystone is always in the head

        for i in range(0, len(self.check_item_order)):
            name = self.check_item_order[i]
            temp1.append([name, create_item_holding_quantity[name]])

        temp1.sort(key=lambda x: x[1], reverse=self.sort_direction == "down")
        temp2.sort(key=lambda x: x[1], reverse=self.sort_direction == "down")

        temp1 = [x[0] for x in temp1]
        temp2 = [x[0] for x in temp2]

        self.check_item_order = temp2
        self.check_item_order.extend(temp1)

    def clear_exist_item(self):
        self.now_exist_item_info.clear()

    def item_now_exist(self, name):
        return name in self.now_exist_item_info

    def item_not_exist(self, name):
        return name in self.not_exist_item_list

    def item_quantity(self, name):
        if name in self.now_exist_item_info:
            return self.now_exist_item_info[name]["holding_quantity"]
        return 0

    def item_all_checked(self):
        for t in self.current_recorded_y_list:
            if t[1] != 4:
                return True
        if self.swipe_no_change_cnt >= 3:
            return True
        return False

    def list_swipe(self):
        dy = swipe_item_list_get_y_diff(self.baas, self.current_recorded_y_list)
        if dy <= 15:
            self.swipe_no_change_cnt += 1
        else:
            self.swipe_no_change_cnt = 0
        self.last_check_y -= dy

    def try_choose_item(self):
        return self.select_item_func_list[self.select_item_rule][self.phase]()

    def phase1_default_select_item(self):
        for name in self.now_exist_item_info:
            if select_item(self.baas, self, name, self.weight_sum):
                return True
        return False

    def phase2_default_select_item(self):
        for name in self.now_exist_item_info:
            if self.item_is_Artifact(name, 0):
                if select_item(self.baas, self, name, self.weight_sum):
                    return True

    def phase3_default_select_item(self):
        for name in self.now_exist_item_info:
            if self.item_is_Artifact(name, 2):
                if select_item(self.baas, self, name, self.weight_sum):
                    return True

    def item_weight_is(self, name, weight):
        return self.baas.static_config["create_material_information"][name]["weight"] == weight

    def item_is_Artifact(self, name, level):
        wt = [1, 2, 4, 10]
        wt = wt[level]
        return self.item_type_is(name, "Material") and self.item_weight_is(name, wt)

    def item_type_is(self, name, material_type):
        return self.baas.static_config["create_material_information"][name]["material_type"] == material_type

    @staticmethod
    def item_type_is_Disk(name):
        return "Tactical-Training" in name

    @staticmethod
    def item_type_is_Beginner_Disk(name):
        return name.startswith("Beginner-Tactical-Training")

    @staticmethod
    def item_type_is_Normal_Disk(name):
        return name.startswith("Normal-Tactical-Training")

    @staticmethod
    def item_type_is_Advanced_Disk(name):
        return name.startswith("Advanced-Tactical-Training")

    @staticmethod
    def item_type_is_Superior_Disk(name):
        return name.startswith("Superior-Tactical-Training")

    @staticmethod
    def item_type_is_Beginner_TechNote(name):
        return name.startswith("Beginner-Tech-Notes")

    @staticmethod
    def item_type_is_Normal_TechNote(self, name):
        return name.startswith("Normal-Tech-Notes")

    @staticmethod
    def item_type_is_Advanced_TechNote(self, name):
        return name.startswith("Advanced-Tech-Notes")

    @staticmethod
    def item_type_is_Superior_TechNote(self, name):
        return name.startswith("Superior-Tech-Notes")

    @staticmethod
    def item_type_is_TechNote(self, name):
        return "Tech-Notes" in name


def swipe_item_list_get_y_diff(self, item_lines_y):
    max_y = item_lines_y[len(item_lines_y) - 1][0]
    y1 = max_y + 43
    y2 = max_y + 109
    if max_y > 534 - 109:
        y1 = max_y - 53
        y2 = max_y
    area = (713, y1, 1247, y2)
    tar_img = image.screenshot_cut(self, area)
    self.swipe(690, 511, 690, 348, duration=0.05, post_sleep_time=1)
    self.update_screenshot_array()
    position = image.search_image_in_area(self, tar_img, area=(713 - 10, 122, 1247 + 10, 482), threshold=0.8)
    return area[1] - position[1]


def item_recognize(self, check_state):
    get_item_position(self, check_state)
    items = check_state.current_item_state
    item_lines_y = check_state.current_recorded_y_list
    last_checked_y = check_state.last_check_y
    self.logger.info("detected item row y : " + str(item_lines_y))
    self.logger.info("last checked y : " + str(last_checked_y))
    temp = 0
    log_name_list = []
    log_quantity_list = []
    threshold = 0.8
    for i in range(0, len(item_lines_y)):
        if item_lines_y[i][0] - check_state.last_check_y <= 10:
            temp += item_lines_y[i][1]
            continue
        y = item_lines_y[i][0]
        for j in range(0, item_lines_y[i][1]):
            p = items[temp + j]["detected_position"]
            item_image_region = get_item_image_region(p[0], y)
            if item_image_region[1] <= 140:
                continue
            item_holding_quantity_region = get_item_holding_quantity_region(p[0], y)
            usability = items[temp + j]["usability"]
            name = check_state.next_possible_item_name()
            compare_img_name = "create_" + name
            if usability == 2:
                compare_img_name += "-Used-Up"
            max_similarity = 0
            max_idx = 0
            holding_quantity = 0
            # detect name
            while self.flag_run:
                if name == "Broken-Crystal-Haniwa":
                    print(1)
                pos, max_val = image.search_in_area(self, compare_img_name, item_image_region, threshold, 10,
                                                    ret_max_val=True)
                if max_val < threshold:
                    if max_val > max_similarity:
                        max_similarity = max_val
                        max_idx = check_state.last_checked_idx - 1
                    name = check_state.next_possible_item_name()
                    if name is None:
                        break
                    compare_img_name = "create_" + name
                    if usability == 2:
                        compare_img_name += "-Used-Up"
                    continue
                if usability == 1:
                    holding_quantity = get_item_holding_quantity(self, item_holding_quantity_region)
                elif usability == 2:
                    self.logger.info("Item : [ " + name + " ] is used up.Set holding quantity to 0.")
                break
            if name is None:
                if max_similarity >= 0.5:
                    check_state.last_checked_idx = max_idx + 1
                    name = check_state.check_item_order[max_idx]
                    holding_quantity = get_item_holding_quantity(self, item_holding_quantity_region)
                    self.logger.info("Predict : " + name)
                    self.logger.info("Similarity : " + str(round(max_similarity, 3)))
                else:
                    self.logger.warning("Could't detect item type at " + str(p))
                    check_state.last_checked_idx = 0
                    log_name_list.append("UNKNOWN")
                    continue
            items[temp + j]["holding_quantity"] = holding_quantity
            self.config_set.config["create_item_holding_quantity"][name] = holding_quantity
            log_name_list.append(name)
            log_quantity_list.append(holding_quantity)
            item_invisible = check_state.pop_checked_item(items[temp + j])
            self.config_set.save()
            if len(item_invisible) > 0:  # game will hide item you don't have
                self.logger.info("Item : [ " + str(item_invisible) + " ] invisible.")
                self.logger.info("Set holding quantity to 0.")
                for invisible_item_name in item_invisible:
                    self.config["create_item_holding_quantity"][invisible_item_name] = 0
        check_state.last_check_y = y
        temp += item_lines_y[i][1]
    if len(log_name_list) > 0:
        log_detect_information(self, log_name_list, "Detected Item name : ")
        log_detect_information(self, log_quantity_list, "Holding Quantity : ")


def log_detect_information(self, itm_list, pre_info=None):
    self.logger.info(pre_info)
    t = 4
    length = len(itm_list)
    while t <= length:
        self.logger.info(itm_list[t - 4:t])
        t += 4
    if t != length + 4:
        self.logger.info(itm_list[t - 4:])
    return


def get_item_holding_quantity(self, region):
    res = self.ocr.get_region_res(self.latest_img_array, region, "Global", self.ratio)
    res = res.replace("g", "9")
    res = res.replace("i", "1")
    try:
        if 'x' in res:
            return int(res.split("x")[1])
        if 'X' in res:
            return int(res.split("X")[1])
    except ValueError:
        pass
    res = re.sub(r"\D", "", res)
    try:
        res = int(res)
        return res
    except ValueError:
        pass


def get_item_selected_quantity(self, region):
    res = self.ocr.get_region_res(self.latest_img_array, region, "Global", self.ratio)
    res = res.replace("g", "9")
    res = res.replace("i", "1")
    res = re.sub(r"\D", "", res)
    try:
        res = int(res)
        return res
    except ValueError:
        return 0


def get_item_image_region(x, y):
    dx1 = -11
    dx2 = 122
    dy1 = -95
    dy2 = -23
    return x + dx1, y + dy1, x + dx2, y + dy2


def get_item_holding_quantity_region(x, y):
    dy1 = -30
    dy2 = -3
    dx = 93
    return x, y + dy1, x + dx, y + dy2


def get_item_selected_quantity_region(x, y):
    dx = 103
    dy = 25
    return x, y, x + dx, y + dy


def get_item_position(self, check_state):
    x = CreateItemCheckState.possible_x
    y_end = 533

    state = []
    recorded_y = []
    item_template = {
        "detected_position": None,
        "holding_quantity": None,
        "selected_quantity": None,
        "usability": None,
    }
    for k in range(0, len(x)):
        possibles_x = x[k]
        curr_y = 127
        while curr_y <= y_end:
            sta = judge_item_state(self, possibles_x, curr_y)
            if sta == 0:
                curr_y += 1
                continue
            elif sta == 1 or sta == 2:
                item_template["usability"] = sta
                y = curr_y
                for i in range(0, len(recorded_y)):
                    if abs(curr_y - recorded_y[i][0]) <= 5:
                        y = recorded_y[i][0]
                        recorded_y[i] = (recorded_y[i][0], recorded_y[i][1] + 1)
                        break
                else:
                    recorded_y.append((curr_y, 1))
                item_template["detected_position"] = (possibles_x, y)
                curr_y += 100
                state.append(item_template.copy())

    check_state.current_item_state = sorted(state, key=lambda t: t["detected_position"][1])
    check_state.current_recorded_y_list = sorted(recorded_y, key=lambda t: t[0])


def judge_item_state(self, x, y):
    # x y is upper left of the bar which records the chosen item number
    # four points to judge
    # rgb for item available 67 82 102
    # item unavailable 155 162 168
    dx = 83
    dy = 23
    if color.judge_rgb_range(self, x, y, 57, 77, 72, 92, 92, 112) and \
        color.judge_rgb_range(self, x + dx, y, 57, 77, 72, 92, 92, 112) and \
        color.judge_rgb_range(self, x, y + dy, 57, 77, 72, 92, 92, 112) and \
        color.judge_rgb_range(self, x + dx, y + dy, 57, 77, 72, 92, 92, 112):
        return 1
    elif color.judge_rgb_range(self, x, y, 145, 165, 160, 180, 165, 185) and \
        color.judge_rgb_range(self, x + dx, y, 145, 165, 160, 180, 165, 185) and \
        color.judge_rgb_range(self, x, y + dy, 145, 165, 160, 180, 165, 185) and \
        color.judge_rgb_range(self, x + dx, y + dy, 145, 165, 160, 180, 165, 185):
        return 2
    return 0  # 0: not am item, 1: usable 2 : unusable but is an item
