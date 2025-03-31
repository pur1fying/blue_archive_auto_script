import re
import psutil
from typing import List, Tuple, Dict, Optional, Union
from .bluestacks_module import get_bluestacks_nxt_adb_port_id, return_bluestacks_type
from .get_adb_address import get_simulator_port
from .simulator_native import process_native_api

SIMULATOR_LISTS: Dict[str, List[str]] = {
    'bluestacks_nxt': ['hd-player.exe'],
    'yeshen': ['nox.exe'],
    'mumu': ['mumuplayer.exe'],
    'leidian': ['dnplayer.exe'],
    'xiaoyao_nat': ['memu.exe']
}


def get_running_processes() -> List[Dict[str, Union[int, str]]]:
    process_list: List[Dict[str, Union[int, str]]] = []
    for process in psutil.process_iter(['pid', 'name']):
        process_list.append(process.info)
    return process_list


def check_simulator(process_name: str, simulator_lists: Dict[str, List[str]]) -> Optional[str]:
    for simulator, names in simulator_lists.items():
        if process_name.lower() in names:
            return simulator
    return None


def auto_scan_simulators(pid_detect: bool = False) -> Tuple[List[int], List[str]]:
    pid_list: List[int] = []
    simulator_list: List[str] = []
    running_processes = get_running_processes()

    for process in running_processes:
        process_name = process['name'].lower()
        simulator = check_simulator(process_name, SIMULATOR_LISTS)
        if simulator:
            pid_list.append(process['pid'])
            simulator_list.append(simulator)

    if pid_detect:
        for pid in pid_list:
            simulator_index = pid_list.index(pid)
            simulator = simulator_list[simulator_index]
            if simulator == 'bluestacks_nxt':
                bluestacks_type = return_bluestacks_type(pid)
                if bluestacks_type:
                    simulator_list[simulator_index] = bluestacks_type
    if pid_detect:
        return pid_list, simulator_list
    else:
        return simulator_list


def auto_search_adb_address() -> List[str]:
    regex_patterns: Dict[str, List[str]] = {
        'bluestacks_nxt': [
            r'.*HD-Player.exe\s+--instance\s+(\w+).*',
            r'.*HD-Player.exe\s*'
        ],
        'mumu': [
            r'.*MuMuPlayer.exe\s+-v\s+(\w+).*',
            r'.*MuMuPlayer.exe\s*'
        ],
        'leidian': [
            r'.*dnplayer.exe\s+index=(\w+).*',
            r'.*dnplayer.exe\s*'
        ],
        'xiaoyao_nat': [
            r'.*MEmu.exe\s+MEmu_(\w+).*',
            r'.*MEmu.exe\s*'
        ]
    }

    adb_addresses: List[str] = []
    pid_list, simulator_list = auto_scan_simulators(pid_detect=True)

    cmdline_dict: Dict[str, List[str]] = {simulator: [] for simulator in simulator_list}

    for pid, simulator in zip(pid_list, simulator_list):  # 使用 zip 将 pid 和对应的 simulator 配对
        cmdline = process_native_api("get_command_line_pid", str(pid))  # 返回类型 str
        cmdline_no_quotes = cmdline.replace('"', '')  # 去掉引号
        cmdline_dict[simulator].append(cmdline_no_quotes)  # 直接添加到对应的字典中

    for simulator, matched_cmdlines in cmdline_dict.items():
        for cmdline in matched_cmdlines:
            multi_instance: Optional[str] = None
            for validation_pattern in regex_patterns[simulator.lower()]:  # 按顺序检查正则表达式
                match = re.match(validation_pattern, cmdline)
                if match:
                    if re.match(r'.*' + simulator + r'\s+', cmdline) or re.match(r'.*' + simulator, cmdline):
                        multi_instance = None
                    else:
                        multi_instance = match.group(1) if len(match.groups()) > 0 else None
                    break
            if simulator == 'bluestacks_nxt':
                adb_address = f"127.0.0.1:{get_bluestacks_nxt_adb_port_id(multi_instance)}"
            elif simulator == 'bluestacks_nxt_cn':
                adb_address = f"127.0.0.1:{get_bluestacks_nxt_adb_port_id(multi_instance, 'cn')}"
            else:
                adb_address = get_simulator_port(simulator, multi_instance)
            adb_addresses.append(adb_address)

    return list(dict.fromkeys(adb_addresses))  # 使用字典去重
