
### adb_port_scanner ###
from .bluestacks_module import get_bluestacks_nxt_adb_port, get_bluestacks_nxt_cn_adb_port


def get_simulator_port(simulator_type , multi_instance):
    if simulator_type == "bluestacks_nxt":
        if multi_instance == None:
            multi_instance = "BlueStacks App Player"
        bluestacks_adb_port_return = get_bluestacks_nxt_adb_port(multi_instance)
        if bluestacks_adb_port_return:
            return f"127.0.0.1:{bluestacks_adb_port_return}"
        else:
            return "NOT_INSTALLED"
    elif simulator_type == "bluestacks_nxt_cn":
        if multi_instance == None:
            multi_instance = "BlueStacks"
        bluestacks_adb_port_return = get_bluestacks_nxt_cn_adb_port(multi_instance)
        if bluestacks_adb_port_return:
            return f"127.0.0.1:{bluestacks_adb_port_return}"
        else:
                return "NOT_INSTALLED"
    elif simulator_type == "mumu":
        if multi_instance == None:
            multi_instance = 1
        if int(multi_instance)<=1536:
            return f"127.0.0.1:{int(multi_instance) * 32 + 16352}"
        else:
            return "INVALID_INPUT"
    elif simulator_type == "yeshen":
        multi_instance = int(multi_instance)
        if multi_instance != None and multi_instance != 1:
            ys_port = 62023 + multi_instance
        else:
            ys_port = 62001
        
        if ys_port <= 65535 and ys_port>= 0:
            return f"127.0.0.1:{ys_port}"
        else:
            return "INVALID_INPUT"
    elif simulator_type == "mumu_classic":
        return f"127.0.0.1:7555"
    elif simulator_type == "xiaoyao_nat":
        if multi_instance != None:
            if int(multi_instance) <= 4404 and int(multi_instance)>=0:
                return f"127.0.0.1:{int(multi_instance)*10+21493}"
            else:
                return "INVALID_INPUT"
        return f"127.0.0.1:21503"
    elif simulator_type == "leidian":
        if multi_instance == None or multi_instance == 0:
            return f"127.0.0.1:P{int(multi_instance)*2+5555}"
        else:
            return f"127.0.0.1:5555"
    elif simulator_type == "wsa":
        if multi_instance != None:
            return f"{multi_instance}:58526"
        else:
            return f"127.0.0.1:58526"
    return "MISSING_INPUT_PARAMETER"

### end adb_port_scanner ###
