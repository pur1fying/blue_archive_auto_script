import psutil
import subprocess
### start simulator native api ###

def process_native_api(input_type, process_input):
    if input_type == "terminate_name":
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == process_input.lower(): # 不区分大小写匹配进程名
                process_input = process.info['pid']
                input_type = "terminate_pid"
                break
        else:
            return "NO_SUCH_PROCESS" # 返回报错
    if input_type == "terminate_pid":
        try:
            p = psutil.Process(int(process_input))
            p.terminate()  # 使用terminate()方法结束进程
            return "OPERATION_SUCCEEDED"
        except psutil.NoSuchProcess as e: # 异常捕获
            return "NO_SUCH_PROCESS"
        except psutil.AccessDenied as e:
            return "ACCESS_DENIED"
    if input_type == "get_command_line_name":# 以进程名获取命令行参数
        cmd = 'wmic process get caption,commandline /value'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = []
        current_caption = None
        for line in proc.stdout:
            if not line.strip():  # skip empty lines
                continue
            try:
                line_decoded = line.decode('utf-8')
            except UnicodeDecodeError:
                line_decoded = line.decode('gbk', errors='ignore')
            if '=' in line_decoded:
                key, value = line_decoded.split('=', 1)
                if key.strip() == 'Caption':
                    current_caption = value.strip()
                elif key.strip() == 'CommandLine':
                    if current_caption and current_caption.lower() == process_input.lower():
                        output.append(value.strip())
                    current_caption = None  # reset current_caption
        return output if output else "NO_SUCH_PROCESS"
    
    if input_type == "get_command_line_pid":# 以pid获取命令行参数
        cmd = 'wmic process where "ProcessId={}" get Commandline /value'.format(process_input)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = ''
        for line in proc.stdout:
            try:
                line_decoded = line.decode('utf-8')
            except UnicodeDecodeError:# 如果输入不是utf-8，尝试使用gbk解码（Windows 中文系统默认页936，即gbk）
                line_decoded = line.decode('gbk', errors='ignore')
            if 'CommandLine' in line_decoded:
                output += line_decoded.split('=')[1].strip() + ' '
        return output.strip() if output else "NO_SUCH_PROCESS"
    if input_type == "get_exe_path_name":
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == process_input.lower(): # 不区分大小写匹配进程名
                process_input = process.info['pid']
                input_type = "get_exe_path_pid"
                break
        else:
            return "NO_SUCH_PROCESS"
    if input_type == "get_exe_path_pid":
        try:
            p = psutil.Process(int(process_input))
            return p.exe()
        except psutil.NoSuchProcess:
            return "NO_SUCH_PROCESS"
### end simulator native api ###
