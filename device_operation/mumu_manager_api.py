import os
import winreg

def mumu12_control_api_backend(multi_instance_number=0,operation = "start"):
    # 读取注册表中的键值
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0")
    icon_path, _ = winreg.QueryValueEx(key, "DisplayIcon")
    winreg.CloseKey(key)

    # 修改路径，使其指向MuMuManager.exe
    exe_path = os.path.join(os.path.dirname(icon_path), "MuMuManager.exe")
    if operation == "start":
        #使用mumumanager控制模拟器开启与关闭
        command = f""" "{exe_path}"" api -v {multi_instance_number} launch_player"""
        os.system(command)
    elif operation == "stop":
        command = f""" "{exe_path}" api -v {multi_instance_number} shutdown_player"""
    else:
        return "NOT_SUPPORTED_OPERATION"