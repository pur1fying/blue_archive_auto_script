from .simulator_native import simulator_native_api
from .device_config import device_config, load_data
from .get_adb_address import get_simulator_port
from .auto_scan_simulator import auto_scan_simulators

### simulator api ###

# 请特别注意！
# 使用uuid输入方式时，第一个参数为get_adb_address_by_uuid
# 第二个参数填写对应的uuid，其他参数不需要填写

def simulator_api(operation,simulator_type = None,multi_instance = None):
    if operation == "get_adb_address":
        if simulator_type != None:
            return get_simulator_port(simulator_type,multi_instance)
        else:
            return "MISSING_INPUT_PARAMETER"
    elif operation == "get_running_simulators":# 以易读形式列出正在运行的模拟器
        return auto_scan_simulators()
    elif operation == "get_adb_address_by_uuid":# 使用uuid获取模拟器对应的adb地址
        return load_data(simulator_type)[2]
    elif operation == "get_simulator_uuid":# 获取模拟器唯一uuid，没有对应模拟器时将自动生成
        return device_config(simulator_type, multi_instance)
    elif operation == "terminate_simulator_name":# 第二个参数输入进程名结束该进程，极其不建议使用该功能
        try:
            return simulator_native_api("terminate_name",simulator_type)
        except:
            return "UNKNOWN_ERROR"
    elif operation == "terminate_simulator_pid":# 第二个参数输入pid结束该进程
        try:
            return simulator_native_api("terminate_pid",simulator_type)
        except:
            return "UNKNOWN_ERROR"
    elif operation == "get_simulator_commandline_name":# 第二个参数输入进程名返回命令行参数
        try:
            return simulator_native_api("get_command_line_name",simulator_type)
        except:
            return "UNKNOWN_ERROR"
    elif operation == "get_simulator_commandline_pid":# 第二个参数输入pid返回命令行参数
        try:
            return simulator_native_api("get_command_line_pid",simulator_type)
        except:
            return "UNKNOWN_ERROR"
    elif operation == "get_simulator_commandline_uuid":# 获取uuid对应的模拟器命令行参数
        try:
            return load_data(simulator_type)[3]
        except:
            return "UNKNOWN_ERROR"
    else:
        return "UNKNOWN_OPERATION"
    
### end simulator api ###

