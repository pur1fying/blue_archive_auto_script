import os
import subprocess
import winreg

from .get_adb_address import get_simulator_port


def mumu12_control_api_backend(simulator_type, multi_instance_number=0, operation="start"):
    # 读取注册表中的键值
    if simulator_type == "mumu":
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0")
    else:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal-12.0")
        
    icon_path, _ = winreg.QueryValueEx(key, "DisplayIcon")
    icon_path = icon_path.replace('"', '') # 去除获取到的文件位置两侧的双引号
    winreg.CloseKey(key)

    # 修改路径，使其指向MuMuManager.exe
    exe_path = os.path.join(os.path.dirname(icon_path), r"""MuMuManager.exe""")
    if operation == "start":
        # 使用mumumanager控制模拟器开启与关闭
        command = f""" "{exe_path}" api -v {multi_instance_number} launch_player"""
        subprocess.Popen(command,shell=True)
        return get_simulator_port("mumu", multi_instance_number)
    elif operation == "stop":
        command = f""" "{exe_path}" api -v {multi_instance_number} shutdown_player"""
        subprocess.Popen(command,shell=True)
    else:
        raise ValueError("NOT_SUPPORTED_OPERATION")
