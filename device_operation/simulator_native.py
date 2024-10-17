import subprocess
import psutil
import platform
import re

def process_native_api(input_type, process_input):
    os_type = platform.system()

    if input_type == "terminate_name":
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == process_input.lower():  # 不区分大小写匹配进程名
                process_input = process.info['pid']
                input_type = "terminate_pid"
                break
        else:
            raise FileNotFoundError("no_such_process")  # 返回报错

    if input_type == "terminate_pid":
        p = psutil.Process(int(process_input))
        try:
            p.terminate()  # 使用terminate()方法结束进程
            p.wait(timeout=3)  # 等待进程结束
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            if os_type == "Windows":
                cmd = f'taskkill /F /PID {process_input}'
            elif os_type == "Linux" or os_type == "Darwin":  # Darwin 是 MacOS 的系统标识
                cmd = f'kill -9 {process_input}'
            subprocess.run(cmd, shell=True)
        return "OPERATION_SUCCEEDED"

    if input_type == "get_command_line_name":  # 以进程名获取命令行参数
        if os_type == "Windows":
            cmd = f'wmic process where "name=\'{process_input}\'" get caption,commandline /value'
        elif os_type == "Linux" or os_type == "Darwin":
            cmd = f'ps -eo comm,args'
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, capture_output=True)
        output = []
        for line in proc.stdout.splitlines():
            if os_type == "Windows":
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'Caption' and value.strip().lower() == process_input.lower():
                        output.append(value.strip())
                    elif key.strip() == 'CommandLine':
                        output.append(value.strip())
            else:
                match = re.match(rf'^\s*{re.escape(process_input)}\s+(.*)', line, re.IGNORECASE)
                if match:
                    output.append(match.group(1).strip())
        return output

    if input_type == "get_command_line_pid":  # 以pid获取命令行参数
        if os_type == "Windows":
            cmd = f'wmic process where "ProcessId={process_input}" get Commandline /value'
        elif os_type == "Linux" or os_type == "Darwin":
            cmd = f'ps -p {process_input} -o args='
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, capture_output=True)
        output = ''
        for line in proc.stdout.splitlines():
            if os_type == "Windows":
                if 'CommandLine' in line:
                    output += line.split('=')[1].strip() + ' '
            else:
                output += line.strip() + ' '
        return output.strip()

    if input_type == "get_exe_path_name":
        if os_type == "Windows":
            cmd = f'wmic process where "name=\'{process_input}\'" get ExecutablePath /value'
        elif os_type == "Linux" or os_type == "Darwin":
            cmd = f'which {process_input}'
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, capture_output=True) # type: ignore
        output = ''
        for line in proc.stdout.splitlines(): # type: ignore
            if os_type == "Windows":
                if 'ExecutablePath' in line:
                    output += line.split('=')[1].strip() + ' '
            else:
                output += line.strip() + ' '
        return output.strip()

    if input_type == "get_exe_path_pid":
        p = psutil.Process(int(process_input))
        return p.exe()

def get_pid_by_cmdline(target_cmdline):
    cmd = 'wmic process get CommandLine,ProcessId'
    proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, capture_output=True) # type: ignore
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


