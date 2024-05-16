import os
import subprocess
import winreg
import re

from .mumu_manager_api import mumu12_control_api_backend
from .bluestacks_module import find_display_name, read_registry_key
from .device_config import load_data

def get_pid_by_cmdline(target_cmdline):
    cmd = 'wmic process get CommandLine,ProcessId'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = proc.communicate()[0].decode('utf-8', 'ignore')
    lines = output.strip().split('\n')

    pid_dict = {}
    for line in lines[1:]:
        match = re.match(r'(.*)\s+(\d+)$', line.strip())
        if match:
            cmdline, pid = match.groups()
            cmdline = cmdline.replace('"', '')  # 去除命令行中的双引号
            cmdline = cmdline.replace('\\\\', '\\')  # 将\\替换为\
            cmdline = re.sub(' +', ' ', cmdline)  # 将连续的空格替换为一个空格
            pid_dict[cmdline] = pid

    target_cmdline = target_cmdline.replace('"', '')  # 去除目标命令行参数中的双引号
    target_cmdline = target_cmdline.replace('\\\\', '\\')  # 将\\替换为\
    target_cmdline = re.sub(' +', ' ', target_cmdline)  # 将连续的空格替换为一个空格
    matched_pids = [pid for cmdline, pid in pid_dict.items() if target_cmdline in cmdline]
    return matched_pids

def stop_simulator_uuid(uuid):
    return subprocess.Popen(load_data(uuid)['latest_command_line'])

def bst_read_registry_key(region):
    key_path = f"SOFTWARE\\BlueStacks_nxt{region}"
    value_name = "InstallDir"
    try:
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
            os.system(f'taskkill /F /PID {pid[0]}')
    if simulator_type == "bluestacks_nxt_cn":
        if multi_instance is None or multi_instance == "":
            multi_instance = "BlueStacks"
        command = f""" "{bst_read_registry_key('cn')}" --instance {find_display_name(multi_instance, read_registry_key('cn'))}"""
        pid = get_pid_by_cmdline(command)
        if pid:
            os.system(f'taskkill /F /PID {pid[0]}')

    if simulator_type == "mumu":
        if multi_instance == None:
            multi_instance = 0
        mumu12_control_api_backend(multi_instance, 'stop')
