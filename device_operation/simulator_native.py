import subprocess
from typing import Optional
import psutil
import platform
import re

def process_native_api(input_type: str, process_input: str) -> Optional[str]:
    os_type = platform.system()
    if input_type == "terminate_name":
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == process_input.lower():
                process_input = process.info['pid']
                input_type = "terminate_pid"
                break
        else:
            raise FileNotFoundError("no_such_process")
    if input_type == "terminate_pid":
        p = psutil.Process(int(process_input))
        try:
            p.terminate()
            p.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            if os_type == "Windows":
                cmd = f'taskkill /F /PID {process_input}'
            elif os_type == "Linux" or os_type == "Darwin":
                cmd = f'kill -9 {process_input}'
            subprocess.run(cmd, shell=True)
        return "OPERATION_SUCCEEDED"
    if input_type == "get_command_line_name":
        if os_type == "Windows":
            cmd = ["powershell", "-Command", f"Get-WmiObject Win32_Process | Where-Object {{$_.Name -eq '{process_input}'}} | Select-Object Caption, CommandLine | Format-List"]
        elif os_type == "Linux" or os_type == "Darwin":
            cmd = f'ps -eo comm,args'
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE)
        output = []
        for line in proc.stdout:
            if os_type == "Windows":
                if line.strip() == "":
                    continue
                key, value = line.split(':', 1)
                if key.strip() == 'CommandLine':
                    output.append(value.lstrip().rstrip('\n'))
            else:
                match = re.match(rf'^\s*{re.escape(process_input)}\s+(.*)', line, re.IGNORECASE)
                if match:
                    output.append(match.group(1).lstrip().rstrip('\n'))
        proc.wait()
        return output
    if input_type == "get_command_line_pid":  # 以pid获取命令行参数
        if os_type == "Windows":
            cmd = ["powershell", "-Command", f"Get-WmiObject Win32_Process | Where-Object {{$_.ProcessId -eq {process_input}}} | Select-Object CommandLine | Format-List"]
        elif os_type == "Linux" or os_type == "Darwin":
            cmd = f'ps -p {process_input} -o args='
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE)
        for line in proc.stdout:
            if os_type == "Windows":
                if line.strip() == "":
                    continue
                key, value = line.split(':', 1)
                if key.strip() == 'CommandLine':
                    return value.lstrip().rstrip('\n')  # 返回命令行参数字符串
            else:
                return line.lstrip().rstrip('\n')  # 返回命令行参数字符串
        proc.wait()
        return None  # 如果没有找到命令行，返回 None
    if input_type == "get_exe_path_name":
        if os_type == "Windows":
            cmd = ["powershell", "-Command", f"Get-WmiObject Win32_Process | Where-Object {{$_.Name -eq '{process_input}'}} | Select-Object ExecutablePath | Format-List"]
        elif os_type == "Linux" or os_type == "Darwin":
            cmd = f'which {process_input}'
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE)
        output = []
        for line in proc.stdout:
            if os_type == "Windows":
                if line.strip() == "":
                    continue
                key, value = line.split(':', 1)
                if key.strip() == 'ExecutablePath':
                    output.append(value.lstrip().rstrip('\n'))
            else:
                output.append(line.rstrip())
        proc.wait()
        return output
    if input_type == "get_exe_path_pid":
        p = psutil.Process(int(process_input))
        return p.exe()


def get_pid_by_cmdline(target_cmdline):
    cmd = ["powershell", "-Command", "Get-WmiObject Win32_Process | Select-Object CommandLine,ProcessId | Format-Table -AutoSize"]
    proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE)
    output = proc.communicate()[0]
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
