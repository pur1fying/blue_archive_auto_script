import os
import re
import winreg

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

    # 3. 检测是否为hyperv
    def check_hypervisor_status(path):
        conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
        if os.path.exists(conf_file):
            with open(conf_file, 'r') as file:
                for line in file:
                    if 'bst.status.hypervisor="hyperv"' in line:
                        return True
        return False

    # 4. 提取并替换对应的字符
    def extract_port(multi_instance, path, hyperv_status):
        display_name = find_display_name(multi_instance, path)
        if display_name:
            port_type = "status.adb_port" if hyperv_status else "adb_port"
            conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
            with open(conf_file, 'r') as file:
                for line in file:
                    if f'bst.instance.{display_name}.{port_type}' in line:
                        extracted_port = re.search(r'\"(.+?)\"', line)
                        if extracted_port:
                            return extracted_port.group(1)
        return None

    registry_path = read_registry_key()
    if registry_path:
        hyperv_status = check_hypervisor_status(registry_path)
        true_adb_port = extract_port(multi_instance, registry_path, hyperv_status)
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

    # 3. 检测是否为hyperv
    def check_hypervisor_status(path):
        conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
        if os.path.exists(conf_file):
            with open(conf_file, 'r') as file:
                for line in file:
                    if 'bst.status.hypervisor="hyperv"' in line:
                        return True
        return False

    # 4. 提取并替换对应的字符
    def extract_port(multi_instance, path, hyperv_status):
        display_name = find_display_name(multi_instance, path)
        if display_name:
            port_type = "status.adb_port" if hyperv_status else "adb_port"
            conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
            with open(conf_file, 'r') as file:
                for line in file:
                    if f'bst.instance.{display_name}.{port_type}' in line:
                        extracted_port = re.search(r'\"(.+?)\"', line)
                        if extracted_port:
                            return extracted_port.group(1)
        return None

    registry_path = read_registry_key()
    if registry_path:
        hyperv_status = check_hypervisor_status(registry_path)
        true_adb_port = extract_port(multi_instance, registry_path, hyperv_status)
        return true_adb_port
    return None

#对外接口函数：simulator_type为输入模拟器类型，multi_instance为输入的模拟器多开名称/序号，默认参数

def get_simulator_port(simulator_type , multi_instance = 0):
    if simulator_type == "bluestacks_nxt":
        if multi_instance == 0:
            multi_instance = "BlueStacks App Player"
            return f"127.0.0.1:{get_bluestacks_nxt_adb_port(multi_instance)}"
        else:
            return f"127.0.0.1:{get_bluestacks_nxt_adb_port(multi_instance)}"
    elif simulator_type == "bluestacks_nxt_cn":
        if multi_instance == 0:
            multi_instance = "BlueStacks"
            return f"127.0.0.1:{get_bluestacks_nxt_cn_adb_port(multi_instance)}"
        else:
            return f"127.0.0.1:{get_bluestacks_nxt_cn_adb_port(multi_instance)}"
    elif simulator_type == "mumu":
        return f"127.0.0.1:{int(multi_instance) * 32 + 16352}"
    elif simulator_type == "yeshen":
        if int(multi_instance) != 0:
            ys_port = 62023 + int(multi_instance)
        else:
            ys_port = 62001
        return f"127.0.0.1:{ys_port}"
    elif simulator_type == "mumu_classic":
        return f"127.0.0.1:7555"
    elif simulator_type == "tx_syzs":
        return f"127.0.0.1:6555"
    elif simulator_type == "xiaoyao_nat":
        if multi_instance != 0:
            return f"{multi_instance}:58526"
        return f"127.0.0.1:58526"
    elif simulator_type == "wsa":
        if multi_instance != 0:
            return f"{multi_instance}:58526"
        else:
            return f"127.0.0.1:58526"
    elif simulator_type == "manual"
        return f"{multi_instance}"
    return None
