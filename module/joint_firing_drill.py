from core import picture, image
from module.main_story import auto_fight


def implement(self):
    if self.server == "JP":
        return True
    self.to_main_page()
    to_joint_firing_menu(self)
    state = check_drill_state(self)
    if not state:
        self.logger.info("No drill open.")
        return True
    solve_drill(self, state)
    return True


def to_joint_firing_menu(self):
    drill_position = {
        "CN": (1112, 452),
        "Global": (1002, 439),
        "JP": (901, 577)
    }
    rgb_possibles = {
        "main_page": (1195, 570),
        "reward_acquired": (640, 100)
    }
    img_ends = [("drill_select-drill-menu", 0.95)]
    img_possibles = {
        "main_page_bus": drill_position[self.server],
        "drill_Season-Record": (119, 101),
        "drill_drill-finish": (644, 525),
    }
    img_possibles.update(picture.GAME_ONE_TIME_POP_UPS[self.server])
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, True)


def check_drill_state(self):
    self.logger.info("Get drill state.")
    state = ["fighting", "open", "lock", "next"]
    open_state = False
    state_checked = [
        ["Assault", False],
        ["Defense", False],
        ["Shooting", False]
    ]

    for i in range(0, 3):  # try 3 time as picture loading need time
        if i >= 1:
            self.logger.info("Retry : " + str(i) + ".")
            self.update_screenshot_array()
        for t in state_checked:
            if t[1]:
                continue
            for s in state:
                img_name = "drill_" + t[0] + "-" + s
                if image.compare_image(self, img_name):
                    t[1] = True
                    if s == "open" or s == "fighting":
                        open_state = (t[0], s)
                    self.logger.info(t[0] + "   \t: " + s)
                    break
            if not t[1]:
                self.logger.info(t[0] + "   \t: unknown.")
        for t in state_checked:
            if not t[1] and open_state:
                return open_state
            elif not t[1] and not open_state:
                break
        else:
            break
    return open_state


def solve_drill(self, state):
    drill_name = state[0]
    drill_state = state[1]
    to_drill(self, drill_name)
    drill_ticket = get_drill_ticket(self)

    if drill_state == "fighting":
        finish_existing_drill(self)
        if self.config.drill_enable_sweep and drill_ticket > 0:
            self.logger.info("Sweep drill.")
            sweep_drill(self, drill_name, drill_ticket)
            return
    if drill_state == "open" and drill_ticket == 0:
        self.logger.info("No drill ticket left.")
        return
    if drill_state == "open" and drill_ticket > 0:
        drill_ticket -= 1
        fight_one_drill(self)
    if self.config.drill_enable_sweep and drill_ticket > 0:
        self.logger.info("Sweep drill.")
        sweep_drill(self, drill_name, drill_ticket)


def get_drill_fighting_state(self):
    img_ends = ["drill_give-up-drill", "drill_start-drill"]
    return picture.co_detect(self, None, None, img_ends, None, True)


def to_drill(self, drill_name):
    position = {
        "CN": {
            "Assault": (182, 363),
            "Defense": (716, 396),
            "Shooting": (1113, 343),
        },
        "Global": {
            "Assault": (1113, 343),
            "Defense": (716, 396),
            "Shooting": (182, 363),
        },
        "JP": {
            "Assault": (182, 363),
            "Defense": (716, 396),
            "Shooting": (1113, 343),
        }
    }

    img_ends = [
        "drill_Season-Record",
    ]
    img_possibles = {
        "drill_select-drill-menu": position[self.server][drill_name],
        'normal_task_fight-confirm': (1168, 659),
        "drill_drill-finish": (644, 525)
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def get_drill_ticket(self):
    region = {
        "CN": (938, 95, 975, 117),
        "Global": (938, 95, 975, 117),
        "JP": (938, 95, 975, 117),
    }
    text = self.ocr.get_region_res(self, region[self.server], 'en-us', "Drill Ticket Count")
    if text[0] in ['0', '1', '2', '3', '4', '5']:
        return int(text[0])
    else:
        self.logger.info("Drill Ticket Num Unknown.Assume Enough.")
        return 3


def fight_one_drill(self):
    self.logger.info("Start Drill.")
    start_drill(self)
    difficulty = self.config.drill_difficulty_list
    formation_num = self.config.drill_fight_formation_list
    for i in range(0, 3):
        diff = difficulty[i]
        form_id = formation_num[i]
        self.logger.info("Fight drill [ " + str(difficulty[i]) + " ] with formation [ " + str(formation_num[i]) + " ].")
        to_drill_information(self, diff)
        select_formation(self, form_id)
        # TODO:: borrow character
        enter_fight(self, form_id)
        auto_fight(self, True)
        if wait_drill_fight_finish(self) == "drill_drill-finish":
            self.logger.info("Drill finish.")
            to_joint_firing_menu(self)
            return True


def to_drill_information(self, difficulty):
    difficulty_y = [0, 190, 290, 390, 490]
    img_ends = "drill_drill-information"
    img_possibles = {
        "drill_Season-Record": (1190, difficulty_y[difficulty]),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def start_drill(self):
    self.logger.info("Start drill.")
    img_possibles = {
        "drill_Season-Record": (1148, 647),
    }
    img_ends = "drill_start-drill-notice"
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
    img_ends = "drill_Season-Record"
    img_possibles = {
        "drill_start-drill-notice": (765, 503),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)


def select_formation(self, i):
    loy = [195, 275, 354, 423]
    y = loy[i - 1]
    rgb_ends = "formation_edit" + str(i)
    rgb_possibles = {
        "formation_edit1": (74, y),
        "formation_edit2": (74, y),
        "formation_edit3": (74, y),
        "formation_edit4": (74, y),
    }
    rgb_possibles.pop("formation_edit" + str(i))
    img_possibles = {"drill_drill-information": (627, 507)}
    picture.co_detect(self, rgb_ends, rgb_possibles, None, img_possibles, True)


def enter_fight(self, i):
    rgb_possibles = {
        "formation_edit" + str(i): (1160, 659),

    }
    rgb_ends = "fighting_feature"
    picture.co_detect(self, rgb_ends, rgb_possibles, None, None, True)


def finish_existing_drill(self):
    self.logger.info("Finish existing drill.")
    difficulty = self.config.drill_difficulty_list
    formation_num = self.config.drill_fight_formation_list
    last_unfinished_fight_number = 1
    while last_unfinished_fight_number <= 2:
        if image.compare_image(self, "drill_fight-" + str(last_unfinished_fight_number) + "-unfinished"):
            break
        if image.compare_image(self, "drill_fight-" + str(last_unfinished_fight_number) + "-finished"):
            last_unfinished_fight_number += 1
            self.logger.info("Drill fight [ " + str(last_unfinished_fight_number) + " ] finished.")
            continue
        self.logger.info("Unknown drill fight [ " + str(last_unfinished_fight_number) + " ] state. Assume finished.")
        last_unfinished_fight_number += 1

    for i in range(last_unfinished_fight_number-1, 3):
        diff = difficulty[i]
        form_id = formation_num[i]
        self.logger.info("Fight drill [ " + str(difficulty[i]) + " ] with formation [ " + str(formation_num[i]) + " ].")
        to_drill_information(self, diff)
        select_formation(self, form_id)
        # TODO:: borrow character
        enter_fight(self, form_id)
        auto_fight(self, True)
        if wait_drill_fight_finish(self) == "drill_drill-finish":
            self.logger.info("Drill finish.")
            to_joint_firing_menu(self)
            return True


def wait_drill_fight_finish(self):
    img_ends = [
        "drill_Season-Record",
        "drill_drill-finish",
    ]
    img_possibles = {
        'normal_task_fight-confirm': (1168, 659),
    }
    return picture.co_detect(self, None, None, img_ends, img_possibles, True)


def sweep_drill(self, drill_name, count):
    self.logger.info("Sweep drill [ " + str(count) + " ] times.")
    to_drill(self, drill_name)
    img_ends = [
        "drill_sweep-menu",
        "drill_sweep-menu2",
    ]
    img_possibles = {
        "drill_Season-Record": (818, 654),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)

    self.click(993, 361, count=count-1, wait_over=True)

    img_ends = "drill_sweep-complete"
    img_possibles = {
        "drill_sweep-menu": (880, 462),
        "drill_sweep-menu2": (880, 462),
        "drill_start-sweep-notice": (766, 502),
    }
    picture.co_detect(self, None, None, img_ends, img_possibles, True)
