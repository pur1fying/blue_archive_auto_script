import os
import re
import winreg

from device_operation.simulator_native import process_native_api


def read_registry_key(region):
    if region != "":
        key_path = f"SOFTWARE\\BlueStacks_nxt_{region}"
    else:
        key_path = f"SOFTWARE\\BlueStacks_nxt"
    value_name = "UserDefinedDir"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            # 如果value不以反斜杠结尾，添加一个
            if not value.endswith("\\"):
                value += "\\"
            return value
    except FileNotFoundError:
        return None


def find_display_name(multi_instance, path):
    if multi_instance == None:
        return "MULTI_INSTANCE_IS_NONE"
    try:
        conf_file = os.path.abspath(os.path.join(path, "BlueStacks.conf"))
        if os.path.exists(conf_file):
            with open(conf_file, 'r') as file:
                for line in file:
                    match = re.match(r'^bst\.instance\.(.+?)\.display_name="{}"'.format(re.escape(multi_instance)),
                                     line)
                    if match:
                        return match.group(1)
        return "NOT_INSTALLED"
    except Exception as e:
        print(f"Caught an exception: {e}")
        return None


def get_bluestacks_nxt_adb_port(multi_instance, region=""):
    display_name = find_display_name(multi_instance, read_registry_key(region))
    if display_name:
        registry_path = read_registry_key(region)
        conf_file = os.path.abspath(os.path.join(registry_path, "BlueStacks.conf"))
        try:
            with open(conf_file, 'r') as file:
                for line in file:
                    if f'bst.instance.{display_name}.status.adb_port' in line:
                        extracted_port = re.search(r'\"(.+?)\"', line)
                        if extracted_port:
                            return extracted_port.group(1)
        except:
            return "FILE_NOT_FOUND"
    return None


def get_bluestacks_nxt_adb_port_id(id, region=""):
    registry_path = read_registry_key(region)
    conf_file = os.path.abspath(os.path.join(registry_path, "BlueStacks.conf"))
    try:
        with open(conf_file, 'r') as file:
            for line in file:
                if f'bst.instance.{id}.status.adb_port' in line:
                    extracted_port = re.search(r'\"(.+?)\"', line)
                    if extracted_port:
                        return extracted_port.group(1)
    except:
        return "FILE_NOT_FOUND"
    return None


### End BlueStacks Module ###

### return simulator type(bluestacks) ###

def return_bluestacks_type(pid):
    def bst_read_registry_key(region):
        key_path = f"SOFTWARE\\BlueStacks_nxt{region}"
        value_name = "InstallDir"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value + 'HD-Player.exe'
        except FileNotFoundError:
            return None

    bst_cn_path = bst_read_registry_key('cn')
    bst_path = bst_read_registry_key('')
    try:
        pid = int(pid)
    except:
        return "ERROR_INPUT"
    if bst_cn_path == process_native_api("get_exe_path_pid", pid):
        return "bluestacks_nxt_cn"
    elif bst_path == process_native_api("get_exe_path_pid", pid):
        return "bluestacks_nxt"
### End return simulator type(bluestacks) ###
