# this script is used to generate explore task data which can be used
# in function common_gird_method which is under this line in module.explore_normal_task


import json

stage_data = {}

input_record = ""


def get_input():
    global input_record
    temp = input()
    input_record += temp + "\n"
    return temp


def get_stage_name():
    print("Please enter stage name : ")
    stage_name = get_input()
    return stage_name


def get_team_info():
    char2attr = {
        "b": "burst",
        "p": "pierce",
        "m": "mystic",
        "s": "shock",
    }

    print("Please enter the team count : ")
    teamLeft = int(get_input())
    teams = []
    while teamLeft > 0:
        print("Teams left : ", teamLeft)
        print(f"Please enter the team name : \n b : burst \n p : pierce \n m : mystic \n s : shock \n swipe : swipe")
        char = get_input().replace(" ", "")
        if char == "swipe":
            print("Please enter the swipe position and duration : format [ x1 y1 x2 y2 duration ]")
            t = get_input().split()
            if len(t) < 5:
                print("Invalid swipe data")
                continue
            x1, y1, x2, y2 = map(int, t[:4])
            duration = float(t[4])
            teams.append(["swipe", (x1, y1, x2, y2, duration)])
        elif char in ["b", "p", "m", "s"]:
            print("Please enter the position : ")
            pos = get_one_position()
            teams.append([char2attr[char], pos])
            teamLeft -= 1
            print('successfully add team : ', char2attr[char])
            print('--------------------------------------------------')
            print("current teams : ", teams)
            print('--------------------------------------------------')
        else:
            print("Invalid team attribute")
            continue
    return teams


def has_position(tp):
    if tp in ["2", "3", "4", "5", "6"]:
        return 1
    return 0


def get_one_position():
    print("please enter position : format [ x y ]")
    temp = get_input().split()
    if len(temp) != 2:
        print("Invalid position")
        return get_one_position()
    try:
        ret = tuple(map(int, temp))
        return ret
    except Exception as e:
        print("Invalid position : " + str(temp))
        return get_one_position()


def get_y_n():
    temp = get_input()
    if temp != "y" and temp != "n":
        print("Invalid input")
        return get_y_n()
    if temp == "y":
        return True
    return False


def get_actions(team_cnt):
    action = []
    action_name = {
        "0": "exchange",
        "1": "exchange_twice",
        "2": "click",
        "3": "exchange_and_click",
        "4": "exchange_twice_and_click",
        "5": "click_and_teleport",
        "6": "choose_and_change",
        "7": "end-turn",
        "8": "retreat"
    }
    while True:
        one_action = {

        }
        print("please enter the action type : \n 0 : exchange \n 1 : exchange_twice \n 2 : click \n 3 : "
              "exchange_and_click \n 4 : exchange_twice_and_click \n 5 : click_and_teleport \n 6 : choose_and_change "
              "\n 7 : end-turn \n 8 : retreat")
        print("q : quit")
        tp = get_input()

        if tp == "q":
            break
        temp = tp.split()
        p_cnt = 0
        if len(temp) == 1:
            one_action["t"] = action_name[temp[0]]
        else:
            t = []
            for i in temp:
                if i == "8":
                    print("please enter total fights and which fight to retreat : format [ total_fights "
                          "fight_to_retreat ]")
                    one_action["retreat"] = get_one_position()
                if i != "8":
                    t.append(action_name[i])
            one_action["t"] = t
        for i in temp:
            p_cnt += has_position(i)
        print("total position required : ", p_cnt)
        if p_cnt == 1:
            one_action["p"] = get_one_position()
        else:
            one_action["p"] = []
            for i in range(p_cnt):
                one_action["p"].append(get_one_position())
        if one_action['t'] == 'end-turn':
            print("current action : \n", one_action)
            action.append(one_action)
            continue
        if team_cnt > 1 and one_action['t'] != 'choose_and_change':
            print("Will formation number change after this action ? [y/n]")
            if get_y_n():
                one_action["ec"] = True
        if one_action['t'] != 'choose_and_change':
            print("Need wait-over after this action ? [y/n]")
            if get_y_n():
                one_action["wait-over"] = True

        print("please enter the desc : ")
        one_action["desc"] = get_input()
        print("current action : \n", one_action)
        action.append(one_action)
    return action


try:
    stage_name = get_stage_name()
    stage_data[stage_name] = {}
    stage_data[stage_name]["start"] = get_team_info()
    stage_data[stage_name]["action"] = get_actions(len(stage_data[stage_name]["start"]))
except Exception as e:
    print(json.dumps(stage_data, indent=2))
    print("Invalid input")
    print(e)

print("---------------------------------")
print("input record : ")
print(input_record)
print("---------------------------------")

print(json.dumps(stage_data, indent=2))
