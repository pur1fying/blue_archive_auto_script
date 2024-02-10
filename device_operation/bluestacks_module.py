import os
import re
import winreg

from device_operation.simulator_native import simulator_native_api
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

### return simulator type(bluestacks) ###
def return_bluestacks_type(input_type, process_input):
    bst_cn_path = get_bluestacks_nxt_cn_adb_port()
    bst_path = get_bluestacks_nxt_adb_port()
    if input_type == "process_name":
        if bst_cn_path == simulator_native_api("get_exe_path_name", "hd-player.exe"):
            return "bluestacks_nxt_cn"
        elif bst_path == simulator_native_api("get_exe_path_name", "hd-player.exe"):
            return "bluestacks_nxt"
    if input_type == "pid":
        try:
            process_input = int(process_input)
        except:
            return "ERROR_INPUT"
        if bst_cn_path == simulator_native_api("get_exe_path_pid", process_input):
            return "bluestacks_nxt_cn"
        elif bst_path == simulator_native_api("get_exe_path_pid", process_input):
            return "bluestacks_nxt"
### End return simulator type(bluestacks) ###