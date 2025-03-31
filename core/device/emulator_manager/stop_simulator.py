import subprocess
from .mumu_manager_api import mumu12_control_api_backend
from .bluestacks_module import find_display_name, read_registry_key
from .device_config import load_data
from .simulator_native import process_native_api,get_pid_by_cmdline

def stop_simulator_uuid(uuid):
    return subprocess.Popen(load_data(uuid)['latest_command_line']) # type: ignore

def bst_read_registry_key(region):
    key_path = f"SOFTWARE\\BlueStacks_nxt{region}"
    value_name = "InstallDir"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
        return value + 'HD-Player.exe'
    except FileNotFoundError:
        return None
            
def stop_simulator_classic(simulator_type, multi_instance=None):
    if simulator_type == "bluestacks_nxt":
        if multi_instance is None or multi_instance == "":
            multi_instance = "BlueStacks App Player"
        command = f'"{bst_read_registry_key("")}" --instance {find_display_name(multi_instance, read_registry_key(""))}'
        pid = get_pid_by_cmdline(command)
        if pid:
            process_native_api("terminate_pid",pid[0])
    if simulator_type == "bluestacks_nxt_cn":
        if multi_instance is None or multi_instance == "":
            multi_instance = "BlueStacks"
        command = f""" "{bst_read_registry_key('cn')}" --instance {find_display_name(multi_instance, read_registry_key('cn'))}"""
        pid = get_pid_by_cmdline(command)
        if pid:
            process_native_api("terminate_pid",pid[0])

    if simulator_type in ["mumu", "mumu_global"]:
        if multi_instance == None:
            multi_instance = 0
        mumu12_control_api_backend(simulator_type, multi_instance, 'stop') # type: ignore
