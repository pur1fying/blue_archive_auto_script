import json
import os
import subprocess
import re


def mumu12_control_api_backend(simulator_type, multi_instance_number=0, operation="start"):
    if os.name == 'nt':
        try:
            import winreg
        # 读取注册表中的键值
            if simulator_type == "mumu":
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0")
                except:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer")
            else:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal-12.0")#predict of mumu5.0 global
        
                except:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal")

            install_path = os.path.dirname(winreg.QueryValueEx(key, "DisplayIcon")[0]).strip('"')
            mumu_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
            winreg.CloseKey(key)
        except:
            return None
        # 修改路径，使其指向MuMuManager.exe
        exe_path = os.path.join(install_path, "MuMuManager.exe")
        def detect_major_version():
            match = re.match(r'^(\d+)\.', mumu_version)
            if match:
                return int(match.group(1))
        major_version_number = detect_major_version()
        if operation == "start":
            # 使用mumumanager控制模拟器开启与关闭
            from .get_adb_address import get_simulator_port
            command = [exe_path, "control", "-v", str(multi_instance_number), "launch"]
            subprocess.run(command)
            return get_simulator_port("mumu", multi_instance_number)
        elif operation == "stop":
            command = [exe_path, "control", "-v", str(multi_instance_number), "shutdown"]
            subprocess.run(command)
        elif operation == "get_path":# 获取MuMuManager.exe所在的目录
            return install_path
        elif operation == "get_device_path":
            if major_version_number == 5:# 获取MuMuNxDevice.exe所在的目录
                return os.path.join(os.path.dirname(install_path), "nx_device", "12.0", "shell")
            else:
                return install_path
        elif operation == "get_manager_path": # 获取MuMuManager.exe所在的路径
            return exe_path
        elif operation == "get_nemu_client_path":# 获取external_renderer_ipc.dll所在的路径
            if major_version_number == 5:
                return os.path.join(os.path.dirname(install_path), "nx_device", "12.0", "shell", "sdk", "external_renderer_ipc.dll")
            else:
                return os.path.join(install_path, "sdk", "external_renderer_ipc.dll")
        elif operation == "disable_app_keptlive": # 关闭后台保活
            command = f""" "{exe_path}" setting -v {multi_instance_number} -k app_keptlive -val false"""
            subprocess.run(command, universal_newlines=True, capture_output=True)
        elif operation == "enable_app_keptlive": # 开启保活
            command = f""" "{exe_path}" setting -v {multi_instance_number} -k app_keptlive -val true"""
            subprocess.run(command, universal_newlines=True, capture_output=True)
        elif operation == "get_launch_status": #获取启动状态
            cmd = [exe_path, "info", "-v", str(multi_instance_number)]
            proc = subprocess.run(cmd, universal_newlines=True, capture_output=True, encoding="utf-8")
            info = json.loads(proc.stdout)
            try:
                return info["player_state"]
            except:
                return "not_launched"
        else:
            return None
