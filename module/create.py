import re

from core import color, image, picture
from core.utils import build_possible_string_dict_and_length, most_similar_string


def implement(self):
    use_acceleration_ticket = self.config.use_acceleration_ticket
    left_create_times = int(self.config.createTime) - int(self.config.alreadyCreateTime)
    create_max_phase = int(self.config.create_phase)
    self.logger.info("Left Create Times       : [ " + str(left_create_times) + " ].")
    self.logger.info("Use Acceleration Ticket : [ " + str(use_acceleration_ticket).upper() + " ].")
    self.logger.info("Create Phase            : [ " + str(create_max_phase) + " ].")
    self.to_main_page()
    ret = to_manufacture_store(self, True)

    if ret.startswith("create_phase"):
        solve_unfinished_create(self, ret)
        to_manufacture_store(self, True)
    create_flag = True
    if left_create_times <= 0:
        create_flag = False
        use_acceleration_ticket = False
    status = receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket)
    while self.flag_run and create_flag:
        if status == ["unfinished", "unfinished", "unfinished"] and (not use_acceleration_ticket):
            self.logger.info("-- Stop Crafting --")
            break
        need_acc_collect = False
        for i in range(0, len(status)):
            if status[i] == "empty":
                ret = to_phase1(self, i, True)
                if ret.startswith("create_phase") or ret == "create_start-crafting":
                    solve_unfinished_create(self, ret)
                    status = check_crafting_list_status(self)  # current position might be occupied by unfinished create
                    continue
                material_adequate = create_phase(self, 1)
                if not material_adequate:
                    create_flag = False
                    break
                if create_max_phase >= 2:
                    confirm_select_node(self, 0)
                    create_phase(self, 2)
                    if create_max_phase >= 3:
                        confirm_select_node(self, 0)
                        create_phase(self, 3)
                confirm_select_node(self, 1)
                need_acc_collect = True
                self.config.alreadyCreateTime += 1
                self.config_set.save()
                self.logger.info("Today Total Create Times : [ " + str(self.config.alreadyCreateTime) + " ].")
                to_manufacture_store(self)
                if self.config.alreadyCreateTime >= self.config.createTime:
                    create_flag = False
                    need_acc_collect = False
                    break
        if need_acc_collect:
            status = receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket)
    get_next_execute_time(self, status)
    return True


def solve_unfinished_create(self, phase_text):
    self.logger.info("Solve Unfinished Create.")
    if phase_text.startswith("create_phase"):
        phase = int(re.findall(r"\d", phase_text)[0])
        start_phase(self, phase)
        select_node(self, phase)
        confirm_select_node(self, 1)
    to_manufacture_store(self, True)


def confirm_select_node(self, tp=0):
    """
        click select node then
        if tp = 0 : go to put more material page
           tp = 1 : confirm create --> return to manufacture store
    """
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


def priority_language_convert(self, phase, pri):
    if self.identifier in ["CN", "Global_en-us", "JP"]:
        return pri
    self.logger.info(f"Phase {phase}. Priority Language Convert.")
    origin_lst = self.static_config.create_default_priority["Global"]["phase" + str(phase)]
    target_lst = self.static_config.create_default_priority[self.identifier]["phase" + str(phase)]
    return [target_lst[origin_lst.index(x)] for x in pri]


def select_node(self, phase):
    pri = self.config_set.get('createPriority_phase' + str(phase))
    pri = priority_language_convert(self, phase, pri)

    for i in range(0, len(pri)):
        pri[i] = preprocess_node_info(pri[i], self.server)

    priority_character_dict, priority_string_len = build_possible_string_dict_and_length(pri)

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
        origin_text = self.ocr.get_region_res(
            self,
            region,
            self.ocr_language,
            "Node " + str(i + 1) + " Text",
        )
        node_info = preprocess_node_info(origin_text, self.identifier)
        for k in range(0, len(pri)):
            if pri[k] == node_info:  # complete match
                if k == 0:  # node == pri[0]
                    self.logger.info("Choose Node : " + pri[0])
                    return
                else:
                    node.append(pri[k])
                    lo.append(i)
                    break
        else:
            self.logger.info("Node is not completely matched.")
            max_acc, idx = most_similar_string(node_info, priority_character_dict, priority_string_len)
            self.logger.info("max acc : " + str(max_acc))
            if max_acc >= 0.5:
                most_possible_node_name = pri[idx]
                self.logger.info("Assume Node is : " + most_possible_node_name)
                if idx == 0:
                    self.logger.info("Choose Node : " + most_possible_node_name)
                    return
                node.append(most_possible_node_name)
                lo.append(i)
            else:
                self.logger.warning("Node [ " + str(node_info) + " ] can't be recognized.")
                self.logger.warning("If it's a new node, please contact the developer to update default node list.")

    self.logger.info("Detected Nodes:")
    self.logger.info(str(node))
    for i in range(1, len(pri)):
        for j in range(0, len(node)):
            if node[j][0:len(pri[i])] == pri[i]:
                self.logger.info("Choose Node : " + pri[i])
                if lo[j] != 4:
                    image.click_until_image_disappear(self, node_x[lo[j]], node_y[lo[j]], region, 0.9, 10)
                return


def get_display_setting(self, phase):
    """
        return filter_list, sort_type, sort_direction
    """
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
    item_selected = False
    while self.flag_run:
        check_state.clear_exist_item()
        item_recognize(self, check_state)
        if check_state.try_choose_item():
            item_selected = True
            break
        if check_state.item_all_checked():
            break
        check_state.list_swipe()
    log_detect_information(self, check_state.exist_item_list, "All Detected Items : ")
    if not item_selected:
        self.logger.warning("Material inadequate.")
        return False
    start_phase(self, phase)
    select_node(self, phase)
    return True


def select_item(self, check_state, item_name, weight):
    item_weight = self.static_config.create_material_information[item_name]["weight"]
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
            self.click(add_click_x, add_click_y, count=diff, duration=0.3, wait_over=True)
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
        "create_phase-1-wait-to-check-node",
        "create_phase-2-wait-to-check-node",
        "create_phase-3-wait-to-check-node"
    ]
    img_possibles = {
        "create_start-crafting": (1115, 657),
        "create_start-crafting-notice": (769, 501),
        "create_select-node": (1115, 657),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    return picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot)


def check_crafting_list_status(self):
    y_position = [288, 407, 534]
    status = [None, None, None]
    for j in range(0, 3):
        if color.rgb_in_range(self, 1126, y_position[j], 90, 130, 200, 230, 245, 255):
            status[j] = "unfinished"
        elif color.rgb_in_range(self, 1126, y_position[j], 235, 255, 222, 255, 53, 93):
            status[j] = "finished"
        elif color.rgb_in_range(self, 1126, y_position[j], 222, 255, 222, 255, 222, 255):
            status[j] = "empty"
    return status


def receive_objects_and_check_crafting_list_status(self, use_acceleration_ticket):
    while self.flag_run:
        status = check_crafting_list_status(self)
        self.logger.info("Crafting List Status: " + str(status))
        if ("unfinished" in status and use_acceleration_ticket) or "finished" in status:
            collect(self, status, use_acceleration_ticket)
        elif "empty" in status or status.count("unfinished") == 3:
            return status
        else:
            ret = to_manufacture_store(self)
            if ret.startswith("create_phase"):
                solve_unfinished_create(self, ret)


def collect(self, status, use_acceleration_ticket):
    if "finished" in status:
        self.click(1126, 617, wait_over=True, duration=1.5)
        self.click(640, 100, wait_over=True, count=2)
        to_manufacture_store(self)
    if ("unfinished" in status) and use_acceleration_ticket:
        img_possibles = {"create_crafting-list": (1126, 617)}
        img_ends = [
            "create_complete-instantly",
            "create_collect-all-rewards-grey"
        ]
        ret = picture.co_detect(self, None, None, img_ends, img_possibles, True)
        if ret == "create_collect-all-rewards-grey":
            self.logger.info("Reward All Collected.")
            return
        img_possibles = {"create_complete-instantly": (766, 516)}
        img_ends = "create_crafting-list"
        picture.co_detect(self, None, None, img_ends, img_possibles, True)
    return


def check_create_availability(self):
    if color.rgb_in_range(self, 1112, 681, 210, 230, 210, 230, 210, 230):
        return "grey"
    elif color.rgb_in_range(self, 1112, 681, 235, 255, 233, 253, 65, 85):
        return "bright"
    else:
        return "unknown"


def to_phase1(self, i, skip_first_screenshot=False):
    y_position = [288, 407, 534]
    img_possibles = {"create_crafting-list": (1153, y_position[i])}
    img_ends = [
        "create_material-list",
        "create_phase-1-wait-to-check-node",
        "create_phase-2-wait-to-check-node",
        "create_phase-3-wait-to-check-node",
        "create_start-crafting"
    ]
    return picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot)


def to_filter_menu(self):
    x = 1048
    img_possibles = {
        "create_material-list": (x, 98),
        "create_sort-menu": (145, 160)
    }
    img_ends = "create_filter-menu"
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def confirm_filter(self):
    img_possibles = {"create_filter-menu": (765, 595)}
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
    self.logger.info(str(filter_list[0:4]))
    self.logger.info(str(filter_list[4:8]))
    filter_list_ensure_choose(self, filter_list)
    confirm_filter(self)


def filter_list_ensure_choose(self, filter_list):
    filter_type_list = self.static_config.create_filter_type_list
    start_position = {
        'CN': (293, 273),
        'Global': (291, 294),
        'JP': (291, 294)
    }
    dx = 235
    dy = {
        'CN': 56,
        'Global': 65,
        'JP': 65
    }
    start_position = start_position[self.server]
    dy = dy[self.server]
    curr_position = start_position
    for i in range(0, len(filter_list)):
        if i == 4:
            curr_position = (start_position[0], start_position[1] + dy)
        else:
            if i != 0:
                curr_position = (curr_position[0] + dx, curr_position[1])
        pre = "create_filter-" + filter_type_list[i] + "-"
        if filter_list[i] == 1:
            img_possibles = {
                pre + "not-chosen": curr_position,
                pre + "reset": curr_position
            }
            img_ends = pre + "chosen"
            picture.co_detect(self, None, None, img_ends, img_possibles, True)
        else:
            img_possibles = {
                pre + "chosen": curr_position,
            }
            img_ends = [pre + "not-chosen", pre + "reset"]
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
            'basic': (290, 168),
            'count': (590, 180),
        },
        'Global': {
            'basic': (294, 181),
            'name': (529, 180),
            'count': (772, 175)
        },
        'JP': {
            'basic': (294, 181),
            'name': (529, 180),
            'count': (772, 175)
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


def preprocess_node_info(st, identifier):
    st = st.replace(" ", "")
    st = st.replace("・", "")
    st = st.replace(".", "")
    st = st.replace("·", "")
    st = st.replace("’", "")
    if identifier == 'Global_en-us':
        st = st.lower()
    return st


def get_next_execute_time(self, status):
    regions = [
        (686, 252, 883, 302),
        (686, 374, 883, 422),
        (686, 498, 883, 547)
    ]
    time_deltas = []
    for i in range(0, 3):
        if status[i] == "unfinished":
            res = self.ocr.get_region_res(
                baas=self,
                region=regions[i],
                language="en-us",
                log_info=f"Item {i + 1} Left Time",
                candidates="0123456789:"
            )
            if res.count(":") != 2:
                continue
            res = res.split(":")
            for j in range(0, len(res)):
                if res[j][0] == "0":
                    res[j] = res[j][1:]
            time_deltas.append(int(res[0]) * 3600 + int(res[1]) * 60 + int(res[2]))
    if time_deltas:
        self.next_time = min(time_deltas)


def item_order_list_builder(self, phase, filter_list, sort_type, sort_direction):
    self.logger.info("Build Item Order List.")
    self.logger.info("Phase : " + str(phase))
    self.logger.info("Filter List : ")
    self.logger.info(str(filter_list[0:4]))
    self.logger.info(str(filter_list[4:8]))
    self.logger.info("Sort Type : " + sort_type)
    self.logger.info("Sort Direction : " + sort_direction)
    result = []
    filter_type_list = self.static_config.create_filter_type_list
    if filter_list[6]:
        # when material is chosen key stone will be displayed at the top
        # CN server phase 3 key stone is not allowed to be chosen
        temp = self.static_config.create_item_order[self.server]["basic"]["Special"]
        if sort_type == "count":
            t = []
            for itm in temp:
                t.append([itm, self.config.create_item_holding_quantity[itm]])
            t.sort(key=lambda x: x[1])
            temp = [x[0] for x in t]

        if sort_direction == "down":
            temp = temp[::-1]
        result.extend(temp)
    if phase == 1:
        return result

    temp = []
    item_info = self.static_config.create_material_information
    phase_id = "phase" + str(phase)
    for i in range(0, len(filter_list)):
        if filter_list[i]:
            for itm in self.static_config.create_item_order[self.server]["basic"][filter_type_list[i]]:
                if item_info[itm]["availability"][phase_id]:
                    temp.append(itm)

    if sort_type == "count":
        t = []
        for itm in temp:
            t.append([itm, self.config.create_item_holding_quantity[itm]])
        t.sort(key=lambda x: x[1])
        temp = [x[0] for x in t]
    if sort_direction == "down":
        temp = temp[::-1]

    result.extend(temp)
    return result


class CreateItemCheckState:
    # During a full phase of item creation. This class is used for information transfer and store checked item state
    possible_x = [710, 851, 992, 1133]
    level_weight = {
        "primary": 1,
        "normal": 2,
        "advanced": 4,
        "superior": 10
    }

    def __init__(self, check_item_order=None, sort_type="basic", sort_direction="up", phase=1, baas=None):
        self.phase = phase
        self.baas = baas
        self.weight_sum = self.baas.static_config.create_each_phase_weight[phase]
        self.select_item_rule = self.baas.config_set.get("create_phase_" + str(phase) + "_select_item_rule")
        self.baas.logger.info("Select Item Rule : [ " + self.select_item_rule + " ].")
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
            "default": [
                self.phase1_default_select_item,
                None,
                None
            ],
            "primary": [
                None,
                (self.select_levels, "primary"),
                None
            ],
            "normal": [
                None,
                (self.select_levels, "normal"),
                None
            ],
            "primary_normal": [
                None,
                (self.select_levels, "primary_normal"),
                None
            ],
            "advanced": [
                None,
                (self.select_levels, "advanced"),
                (self.select_levels, "advanced"),
            ],
            'superior': [
                None,
                (self.select_levels, "superior"),
                (self.select_levels, "superior"),
            ],
            "advanced_superior": [
                None,
                (self.select_levels, "advanced_superior"),
                (self.select_levels, "advanced_superior"),
            ],
            "primary_normal_advanced_superior": [
                None,
                (self.select_levels, "primary_normal_advanced_superior"),
                None
            ],
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
        func = self.select_item_func_list[self.select_item_rule][self.phase - 1]
        if type(func) is tuple:
            return func[0](func[1])
        else:
            return func()

    def phase1_default_select_item(self):
        for name in self.now_exist_item_info:
            if select_item(self.baas, self, name, self.weight_sum):
                return True
        return False

    def select_levels(self, level_str):
        levels = level_str.split("_")
        for name in self.now_exist_item_info:
            if name == 'Keystone' or name == 'Keystone-Piece':
                continue
            if self.item_level_in(name, levels):
                if select_item(self.baas, self, name, self.weight_sum):
                    return True
        return False

    def select_material(self, levels):
        for name in self.now_exist_item_info:
            if self.item_is_Material(name, levels):
                if select_item(self.baas, self, name, self.weight_sum):
                    return True
        return False

    def item_level_is(self, name, level):
        weight = CreateItemCheckState.level_weight[level]
        return self.baas.static_config.create_material_information[name]["weight"] == weight

    def item_level_in(self, name, levels):
        weights = [CreateItemCheckState.level_weight[level] for level in levels]
        return self.baas.static_config.create_material_information[name]["weight"] in weights

    def item_is_Material(self, name, level):
        return self.item_type_is(name, "Material") and self.item_level_is(name, level)

    def item_type_is(self, name, material_type):
        return self.baas.static_config.create_material_information[name]["material_type"] == material_type

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
                    holding_quantity = get_item_holding_quantity(self, item_holding_quantity_region, name)
                elif usability == 2:
                    self.logger.info("Item : [ " + name + " ] is used up.Set holding quantity to 0.")
                break
            if name is None:
                if max_similarity >= 0.5:
                    check_state.last_checked_idx = max_idx + 1
                    name = check_state.check_item_order[max_idx]
                    holding_quantity = get_item_holding_quantity(self, item_holding_quantity_region, name)
                    self.logger.info("Predict : " + name)
                    self.logger.info("Similarity : " + str(round(max_similarity, 3)))
                else:
                    self.logger.warning("Could't detect item type at " + str(p))
                    check_state.last_checked_idx = 0
                    log_name_list.append("UNKNOWN")
                    continue
            items[temp + j]["holding_quantity"] = holding_quantity
            self.config.create_item_holding_quantity[name] = holding_quantity
            log_name_list.append(name)
            log_quantity_list.append(holding_quantity)
            item_invisible = check_state.pop_checked_item(items[temp + j])
            self.config_set.save()
            if len(item_invisible) > 0:  # game will hide item you don't have
                self.logger.info("Item : [ " + str(item_invisible) + " ] invisible.")
                self.logger.info("Set holding quantity to 0.")
                for invisible_item_name in item_invisible:
                    self.config.create_item_holding_quantity[invisible_item_name] = 0
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
        self.logger.info(str(itm_list[t - 4:t]))
        t += 4
    if t != length + 4:
        self.logger.info(str(itm_list[t - 4:]))
    return


def get_item_holding_quantity(self, region, name):
    res = self.ocr.get_region_res(
        baas=self,
        region=region,
        language="en-us",
        log_info=name,
        candidates="0123456789xX"
    )
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
        return 0


def get_item_selected_quantity(self, region):
    res = self.ocr.get_region_res(
        baas=self,
        region=region,
        language="en-us",
        log_info="Select Count",
        candidates="0123456789"
    )
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
    if color.rgb_in_range(self, x, y, 57, 77, 72, 92, 92, 112) and \
        color.rgb_in_range(self, x + dx, y, 57, 77, 72, 92, 92, 112) and \
        color.rgb_in_range(self, x, y + dy, 57, 77, 72, 92, 92, 112) and \
        color.rgb_in_range(self, x + dx, y + dy, 57, 77, 72, 92, 92, 112):
        return 1
    elif color.rgb_in_range(self, x, y, 145, 165, 160, 180, 165, 185) and \
        color.rgb_in_range(self, x + dx, y, 145, 165, 160, 180, 165, 185) and \
        color.rgb_in_range(self, x, y + dy, 145, 165, 160, 180, 165, 185) and \
        color.rgb_in_range(self, x + dx, y + dy, 145, 165, 160, 180, 165, 185):
        return 2
    return 0  # 0: not am item, 1: usable 2 : unusable but is an item
