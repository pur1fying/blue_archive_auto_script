import os
import re
import winreg
import psutil

### BlueStacks Module ###

def get_bluestacks_nxt_cn_adb_port(multi_instance):
    # 1. 读取注册表中的路径
    def read_registry_key():
        key_path = r"SOFTWARE\BlueStacks_nxt_cn"
        value_name = "UserDefinedDir"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except FileNotFoundError:
            return None

    # 2. 在BlueStacks.conf文件中查找特定行
    def find_display_name(multi_instance, path):
        conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
        if os.path.exists(conf_file):
            with open(conf_file, 'r') as file:
                for line in file:
                    match = re.match(r'^bst\.instance\.(.+?)\.display_name="{}"'.format(re.escape(multi_instance)), line)
                    if match:
                        return match.group(1)
        return None

    # 3. 提取并替换对应的字符
    def extract_port(multi_instance, path):
        display_name = find_display_name(multi_instance, path)
        if display_name:
            conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
            with open(conf_file, 'r') as file:
                for line in file:
                    if f'bst.instance.{display_name}.status.adb_port' in line:
                        extracted_port = re.search(r'\"(.+?)\"', line)
                        if extracted_port:
                            return extracted_port.group(1)
        return None

    registry_path = read_registry_key()
    if registry_path:
        true_adb_port = extract_port(multi_instance, registry_path)
        return true_adb_port
    return None

def get_bluestacks_nxt_adb_port(multi_instance):
    # 1. 读取注册表中的路径
    def read_registry_key():
        key_path = r"SOFTWARE\BlueStacks_nxt"
        value_name = "UserDefinedDir"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except FileNotFoundError:
            return None

    # 2. 在BlueStacks.conf文件中查找特定行
    def find_display_name(multi_instance, path):
        conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
        if os.path.exists(conf_file):
            with open(conf_file, 'r') as file:
                for line in file:
                    match = re.match(r'^bst\.instance\.(.+?)\.display_name="{}"'.format(re.escape(multi_instance)), line)
                    if match:
                        return match.group(1)
        return None

    # 3. 提取并替换对应的字符
    def extract_port(multi_instance, path):
        display_name = find_display_name(multi_instance, path)
        if display_name:
            conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
            with open(conf_file, 'r') as file:
                for line in file:
                    if f'bst.instance.{display_name}.status.adb_port' in line:
                        extracted_port = re.search(r'\"(.+?)\"', line)
                        if extracted_port:
                            return extracted_port.group(1)
        return None

    registry_path = read_registry_key()
    if registry_path:
        true_adb_port = extract_port(multi_instance, registry_path)
        return true_adb_port
    return None

### End BlueStacks Module ###

### get running simulator ###


def get_running_processes():
    process_list = []
    
    for process in psutil.process_iter(['pid', 'name']):
        process_list.append(process.info)

    return process_list

def check_simulator(process_name, simulator_lists):
    for simulator, names in simulator_lists.items():
        if process_name.lower() in names:
            return simulator
    return None

def detect_simulators():
    simulator_list = []
    simulator_lists = {
        'bluestacks_nxt': ['hd-player.exe'],
        'yeshen': ['nox.exe'],
        'mumu12': ['mumuplayer.exe']
        # 添加其他模拟器的名称和对应进程名
    }

    running_processes = get_running_processes()

    for process in running_processes:
        process_name = process['name'].lower()
        simulator = check_simulator(process_name, simulator_lists)
        
        if simulator:
            simulator_list.append(simulator)

    return simulator_list

### End get running simulator ###

### adb_port_scanner ###
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
        if multi_instance != None:
            ys_port = 62023 + int(multi_instance)
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
    elif simulator_type == "wsa":
        if multi_instance != None:
            return f"{multi_instance}:58526"
        else:
            return f"127.0.0.1:58526"
    return "MISSING_INPUT_PARAMETER"
### end adb_port_scanner ###


def simulator_api(operation,simulator_type = None,multi_instance = None):
    if operation == "get_adb_address":
        if simulator_type != None:
            return get_simulator_port(simulator_type,multi_instance)
        else:
            return "MISSING_INPUT_PARAMETER"
    elif operation == "get_running_simulators":
        return #auto_scan_simulators()
    else:
        return "UNKNOWN_OPERATION"
